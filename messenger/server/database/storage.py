from sqlalchemy.orm import sessionmaker
import datetime

from server.database import metadata, engine
from server.database import (
    Users,
    ActiveUsers,
    UsersHistory,
    LoginHistory,
    Contacts,
)


class ServerStorage:
    def __init__(self, engine):
        metadata.create_all(engine)  # Инициализация базы данных и создание таблиц
        self.session = sessionmaker(bind=engine)()  # Создание сессии

    def user_login(self, username, ip_address, port):
        # Функция выполняющаяся при входе пользователя, записывает в базу факт входа
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        # Если нет, то создаём нового пользователя
        # Теперь можно создать запись в таблицу активных пользователей о факте входа.
        # и сохранить в историю входов

        usersQuery = self.session.query(Users).filter_by(name=username)
        if usersQuery.count():
            user = usersQuery.first()
            user.last_login = datetime.datetime.now()
        else:
            user = Users(username)
            self.session.add(user)
            self.session.flush()
            # todo: delte - self.session.commit() # Коммит здесь нужен, чтобы присвоился ID
            user_in_history = UsersHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        # Запрашиваем пользователя, что покидает нас.
        # Удаляем его из таблицы активных пользователей.

        user = self.session.query(Users).filter_by(name=username).first()
        self.session.query(ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def process_message(self, sender, recipient):
        # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
        # Получаем ID отправителя и получателя
        # Запрашиваем строки из истории и увеличиваем счётчики

        sender = self.session.query(Users).filter_by(name=sender).first().id
        sender_history = self.session.query(UsersHistory).filter_by(user=sender).first()
        sender_history.sent += 1

        recipient = self.session.query(Users).filter_by(name=recipient).first().id
        recipient_history = self.session.query(UsersHistory).filter_by(user=recipient).first()
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

    def add_user(self, username, last_login=None):
        # Добавляет нового пользователя в базу данных.
        # Проверяем, существует ли уже такой пользователь
        # Если нет, то добавляем нового пользователя
        # Устанавливаем время последнего входа

        try:
            if not self.check_user(username):
                new_user = Users(username)
                new_user.last_login = last_login if last_login else datetime.datetime.now()

                self.session.add(new_user)
                self.session.commit()
                return True  # Успешно добавлен
            else:
                return False  # Пользователь уже существует
        except Exception as e:
            print(f"Ошибка добавления пользователя {username}: {e}")
            self.session.rollback()  # Откатываем изменения в случае ошибки
            return False  # В случае ошибки

    def check_user(self, username):
        # Проверяет, существует ли пользователь с данным именем username.
        # Если пользователь существует, query.first() вернет не None
        # В случае ошибки запроса, считаем что пользователь не найден

        try:
            user = self.session.query(Users).filter_by(name=username).first()
            return user is not None
        except:
            return False


# Отладка
if __name__ == "__main__":
    test_db = ServerStorage(engine)
    test_db.user_login("1111", "192.168.1.113", 8080)
    test_db.user_login("McG2", "192.168.1.113", 8081)
    print(test_db.users_list())
    print(test_db.active_users_list())
    test_db.user_logout("McG2")
    print(test_db.login_history("re"))
    test_db.add_contact("test2", "test1")
    test_db.add_contact("test1", "test3")
    test_db.add_contact("test1", "test6")
    test_db.remove_contact("test1", "test3")
    test_db.process_message("McG2", "1111")
    print(test_db.message_history())
