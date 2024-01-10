from sqlalchemy.orm import sessionmaker
import datetime
import hashlib
import binascii

from . import metadata, engine
from . import Users, ActiveUsers, UsersHistory, LoginHistory, Contacts


class Storage:
    def __init__(self, engine=engine):
        metadata.create_all(engine)  # Инициализация базы данных и создание таблиц
        self.session = sessionmaker(bind=engine)()  # Создание сессии

    def check_user_existing(self, username: str) -> bool:
        # Проверяет, существует ли пользователь с данным именем username.
        # Если пользователь существует, query.first() вернет не None, а фукнция вернет True
        # В случае ошибки запроса, считаем что пользователь не найден, вернет False

        try:
            user = self.session.query(Users).filter_by(name=username).first()
            return user is not None
        except:
            return False

    def get_hash(self, username: str):
        hash_string = self.session.query(Users).filter_by(name=username).first().password_hash
        return hash_string

    def add_user(self, username, password, last_login=None) -> Users:
        # Добавляет нового пользователя в базу данных.
        # Проверяем, существует ли уже такой пользователь
        # Если нет, то добавляем нового пользователя
        # Устанавливаем время последнего входа
        try:
            if not self.check_user_existing(username):
                # Создание пользователя
                # Создание хеша пароля. В качестве соли будем использовать логин в  нижнем регистре.
                passwd_bytes = password.encode("utf-8")
                salt = username.lower().encode("utf-8")
                hash_bytes = hashlib.pbkdf2_hmac("sha512", passwd_bytes, salt, 10000)
                hash_string = binascii.hexlify(hash_bytes)
                new_user = Users(username, password_hash=hash_string)
                new_user.last_login = last_login if last_login else datetime.datetime.now()
                self.session.add(new_user)
                self.session.commit()
                return new_user

        except Exception as e:
            print(f"Ошибка добавления пользователя {username}: {e}")
            self.session.rollback()  # Откатываем изменения в случае ошибки
            return None  # В случае ошибки

    def remove_user(self, username) -> None:
        self.session.query(Users).filter_by(name=username).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port, pubkey="") -> None:
        # Функция выполняющаяся при входе пользователя, записывает в базу факт входа
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        # и проверяем корректность ключа. Если клиент прислал новый ключ,
        # сохраняем его.
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        # Если нет, то создаём нового пользователя
        # Теперь можно создать запись в таблицу активных пользователей о факте входа.
        # и сохранить в историю входов

        user = self.session.query(Users).filter_by(name=username).first()
        user.last_login = datetime.datetime.now()
        if user.pubkey != pubkey:
            user.pubkey = pubkey

        new_active_user = ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        user_history = UsersHistory(user.id)
        self.session.add(user_history)

        logon_history = LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(logon_history)

        self.session.commit()

    def user_logout(self, username: str) -> None:
        # Запрашиваем пользователя, что покидает нас.
        # Удаляем его из таблицы активных пользователей.

        user = self.session.query(Users).filter_by(name=username).first()
        self.session.query(ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def get_pubkey(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(Users).filter_by(name=name).first()
        return user.pubkey

    def process_message(self, sender_name: str, recipient_name: str) -> None:
        # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
        # Получаем ID отправителя и получателя
        # Запрашиваем строки из истории и увеличиваем счётчики

        sender_id = self.session.query(Users).filter_by(name=sender_name).first().id
        sender_history = self.session.query(UsersHistory).filter_by(user=sender_id).first()
        sender_history.sent += 1

        recipient_id = self.session.query(Users).filter_by(name=recipient_name).first().id
        recipient_history = self.session.query(UsersHistory).filter_by(user=recipient_id).first()
        recipient_history.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        # Функция добавляет контакт для пользователя.
        # Получаем ID пользователей
        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        # Создаём объект и заносим его в базу

        user = self.session.query(Users).filter_by(name=user).first()
        contact = self.session.query(Users).filter_by(name=contact).first()

        if not contact or self.session.query(Contacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = Contacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        # Функция удаляет контакт из базы данных
        # Получаем ID пользователей
        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        # Удаляем требуемое

        user = self.session.query(Users).filter_by(name=user).first()
        contact = self.session.query(Users).filter_by(name=contact).first()

        if not contact:
            return

        self.session.query(Contacts).filter(Contacts.user == user.id, Contacts.contact == contact.id).delete()
        self.session.commit()

    def users_list(self):
        # Функция возвращает список известных пользователей со временем последнего входа.
        # Запрос строк таблицы пользователей.
        # Возвращаем список кортежей

        query = self.session.query(Users.name, Users.last_login)
        return query.all()

    def active_users_list(self):
        # Функция возвращает список активных пользователей
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        # Возвращаем список кортежей

        query = self.session.query(
            Users.name,
            ActiveUsers.ip_address,
            ActiveUsers.port,
            ActiveUsers.login_time,
        ).join(Users)
        return query.all()

    def login_history(self, username=None):
        # Функция возвращающая историю входов по пользователю или всем пользователям
        # Запрашиваем историю входа
        # Если было указано имя пользователя, то фильтруем по нему
        # Возвращаем список кортежей

        query = self.session.query(
            Users.name,
            LoginHistory.date_time,
            LoginHistory.ip,
            LoginHistory.port,
        ).join(Users)

        if username:
            query = query.filter(Users.name == username)

        return query.all()

    def get_contacts(self, username):
        # Функция возвращает список контактов пользователя.
        # Запрашиваем указанного пользователя
        # Запрашиваем его список контактов
        # выбираем только имена пользователей и возвращаем их.

        user = self.session.query(Users).filter_by(name=username).one()
        contacts = (
            self.session.query(Contacts, Users.name)
            .filter_by(user=user.id)
            .join(Users, Contacts.contact == Users.id)
            .all()
        )
        return [contact[1] for contact in contacts]

    def message_history(self):
        # Функция возвращает количество переданных и полученных сообщений
        # Возвращаем список кортежей

        query = self.session.query(
            Users.name,
            Users.last_login,
            UsersHistory.sent,
            UsersHistory.accepted,
        ).join(Users)

        return query.all()
