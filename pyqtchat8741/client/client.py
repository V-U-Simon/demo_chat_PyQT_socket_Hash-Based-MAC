import argparse
import os
import sys
from pathlib import Path
from Cryptodome.PublicKey import RSA

from PyQt5.QtWidgets import QApplication, QMessageBox

from .core.core import ClientTransport
from .core.variables import *
from .core.errors_user import ServerError
from .db_client import Storage
from .logs.logger import logger, log


# Парсер аргументов коммандной строки
@log
def arg_parser():
    """
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов
    адрес сервера, порт, имя пользователя, пароль.
    Выполняет проверку на корректность номера порта.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("addr", default=DEFAULT_IP_ADDRESS, nargs="?")
    parser.add_argument("port", default=DEFAULT_PORT, type=int, nargs="?")
    parser.add_argument("-n", "--name", default=None, nargs="?")
    parser.add_argument("-p", "--password", default="", nargs="?")
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {server_port}. "
            f"Допустимы адреса с 1024 до 65535. Клиент завершается."
        )
        exit(1)

    return server_address, server_port, client_name, client_passwd


@log
def main():
    from .gui.main_window import ClientMainWindow
    from .gui.start_dialog import UserNameDialog

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name, client_passwd = arg_parser()
    logger.debug("Args loaded")

    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке, то запросим его
    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и
        # удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            logger.debug(f"Using USERNAME = {client_name}, PASSWD = {client_passwd}.")
        else:
            exit(0)

    # Записываем логи
    logger.info(
        f"Запущен клиент с параметрами: адрес сервера: {server_address} , порт: {server_port},"
        f" имя пользователя: {client_name}"
    )

    dir_path = Path(__file__).parent
    keys_dir = dir_path / "keys"
    key_file = keys_dir / f"{client_name}.key"

    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # key_file = os.path.join(dir_path, f"{client_name}.key")
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, "wb") as key:
            key.write(keys.export_key())
    else:
        with open(key_file, "rb") as key:
            keys = RSA.import_key(key.read())

    # !!!keys.publickey().export_key()
    logger.debug("Keys successfully loaded.")
    # Создаём объект базы данных

    from sqlalchemy import create_engine

    engine = create_engine(
        f"sqlite:///db/client_{client_name}.db3",
        echo=False,
    )
    db = Storage(engine)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_port, server_address, db, client_name, client_passwd, keys)
        logger.debug("Transport ready.")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, "Ошибка сервера", error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Удалим объект диалога за ненадобностью
    del start_dialog

    # Создаём GUI
    main_window = ClientMainWindow(db, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f"Чат Программа alpha release - {client_name}")
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()


if __name__ == "__main__":
    main()
