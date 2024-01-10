import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
import sys
import hashlib

from .decos import login_required
from .utils import send_message, get_message
from .variables import *
from .decos import Port
from .metaclasses import ServerMaker

from ..db_server import Storage
from ..db_server.models import Users

# sys.path.append("../")

# Загрузка логера
logger = logging.getLogger("server")


class MessageProcessor(threading.Thread):
    """
    Основной класс сервера. Принимает содинения, словари - пакеты
    от клиентов, обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока.
    """

    port = Port()

    def __init__(self, listen_address, listen_port, database: Storage):
        # Параметры подключения
        self.addr = listen_address
        self.port = listen_port

        # База данных сервера
        self.db = database

        # Сокет, через который будет осуществляться работа
        self.sock = None

        # Список подключённых клиентов.
        self.clients = []

        # Сокеты
        self.listen_sockets = None
        self.error_sockets = None

        # Флаг продолжения работы
        self.running = True

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

        # Конструктор предка
        super().__init__()

    def run(self):
        """Метод основной цикл потока."""
        # Инициализация Сокета
        self.init_socket()

        # Основной цикл программы сервера
        while self.running:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f"Установлено соедение с ПК {client_address}")
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    (
                        recv_data_lst,
                        self.listen_sockets,
                        self.error_sockets,
                    ) = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f"Ошибка работы с сокетами: {err.errno}")

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.debug(f"Getting data from client exception.", exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        """
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        """
        logger.info(f"Клиент {client.getpeername()} отключился от сервера.")
        for name in self.names:
            if self.names[name] == client:
                self.db.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        """Метод инициализатор сокета."""
        logger.info(
            f"Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов."
        )
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):
        """
        Метод отправки сообщения клиенту.
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in self.listen_sockets:
            try:
                send_message(self.names[message[DESTINATION]], message)
                logger.info(
                    f"Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}."
                )
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.listen_sockets:
            logger.error(
                f"Связь с клиентом {message[DESTINATION]} была потеряна. Соединение закрыто, доставка невозможна."
            )
            self.remove_client(self.names[message[DESTINATION]])
        else:
            logger.error(
                f"Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна."
            )

    @login_required
    def process_client_message(self, message, client):
        """Метод обработчик поступающих сообщений."""
        logger.debug(f"Разбор сообщения от клиента : {message}")
        # Если это сообщение о присутствии, принимаем и отвечаем
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если сообщение о присутствии то вызываем функцию авторизации.
            self.autorize_user(message, client)

        # Если это сообщение, то отправляем его получателю.
        elif (
            ACTION in message
            and message[ACTION] == MESSAGE
            and DESTINATION in message
            and TIME in message
            and SENDER in message
            and MESSAGE_TEXT in message
            and self.names[message[SENDER]] == client
        ):
            if message[DESTINATION] in self.names:
                self.db.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = "Пользователь не зарегистрирован на сервере."
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        # Если клиент выходит
        elif (
            ACTION in message
            and message[ACTION] == EXIT
            and ACCOUNT_NAME in message
            and self.names[message[ACCOUNT_NAME]] == client
        ):
            self.remove_client(client)

        # Если это запрос контакт-листа
        elif (
            ACTION in message
            and message[ACTION] == GET_CONTACTS
            and USER in message
            and self.names[message[USER]] == client
        ):
            response = RESPONSE_202
            response[LIST_INFO] = self.db.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если это добавление контакта
        elif (
            ACTION in message
            and message[ACTION] == ADD_CONTACT
            and ACCOUNT_NAME in message
            and USER in message
            and self.names[message[USER]] == client
        ):
            self.db.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # Если это удаление контакта
        elif (
            ACTION in message
            and message[ACTION] == REMOVE_CONTACT
            and ACCOUNT_NAME in message
            and USER in message
            and self.names[message[USER]] == client
        ):
            self.db.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # Если это запрос известных пользователей
        elif (
            ACTION in message
            and message[ACTION] == USERS_REQUEST
            and ACCOUNT_NAME in message
            and self.names[message[ACCOUNT_NAME]] == client
        ):
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.db.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если это запрос публичного ключа пользователя
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.db.get_pubkey(message[ACCOUNT_NAME])
            # может быть, что ключа ещё нет (пользователь никогда не логинился,
            # тогда шлём 400)
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = "Нет публичного ключа для данного пользователя"
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = "Запрос некорректен."
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        """Метод реализующий авторизацию пользователей."""
        logger.debug(f"Start auth process for {message[USER]}")

        username = message[USER][ACCOUNT_NAME]
        pubkey = message[USER][PUBLIC_KEY]
        print(self.db.check_user_existing(username))
        print(self.db.session.query(Users).filter_by(name=username).first())

        # Проверка взаимодействует ли данный пользователь с сервером в настоящий момент
        # если да, то подлкючение занято и возвращаем 400
        if username in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = "Имя пользователя уже занято."
            try:
                logger.debug(f"Username busy, sending {response}")
                send_message(sock, response)
            except OSError:
                logger.debug("OS Error")
                pass
            self.clients.remove(sock)
            sock.close()
        # Проверяем зарегистрирован ли на сервере пользователь пытающийся подключиться.
        # если нет, то возвращаем 400
        elif not self.db.check_user_existing(username):
            response = RESPONSE_400
            response[ERROR] = "Пользователь не зарегистрирован."
            try:
                logger.debug(f"Unknown username, sending {response}")
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()

        else:
            # начинаем процедуру авторизации
            # код 511 сообщает клиенту об авторизации
            logger.debug("Correct username, starting passwd check.")
            message_auth = RESPONSE_511
            # Генерируем набор байтов в hex представлении
            # В словарь байты нельзя, декодируем
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем серверную версию ключа
            random_str: bytes = binascii.hexlify(os.urandom(64))
            message_auth[DATA]: str = random_str.decode("ascii")

            # Обмен с клиентом
            try:
                print(message_auth[DATA])
                send_message(sock, message_auth)
                answer = get_message(sock)
            except OSError as err:
                logger.debug("Error in auth, data:", exc_info=err)
                sock.close()
                return

            client_digest = binascii.a2b_base64(answer[DATA])
            # Если ответ клиента корректный, то сохраняем его в список
            # пользователей.

            hash = hmac.new(self.db.get_hash(username), random_str, "MD5")
            digest = hash.digest()
            logger.debug(f"Auth message = {message_auth}")

            if RESPONSE in answer and answer[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[username] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(username)
                # добавляем пользователя в список активных и если у него изменился открытый ключ
                # сохраняем новый
                self.db.user_login(
                    username,
                    client_ip,
                    client_port,
                    pubkey,
                )
            else:
                response = RESPONSE_400
                response[ERROR] = "Неверный пароль."
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """Метод реализующий отправки сервисного сообщения 205 клиентам."""
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
