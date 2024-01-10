import datetime
from sqlalchemy.orm import sessionmaker

from .database import metadata
from .models import MessageHistory, Contacts, KnownUsers


class Storage:
    def __init__(self, engine):
        metadata.create_all(engine)  # Инициализация базы данных и создание таблиц
        self.session = sessionmaker(bind=engine)()  # Создание сессии

    # Функция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(Contacts).filter_by(name=contact).count():
            contact_row = Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Функция удаления контакта
    def del_contact(self, contact):
        self.session.query(Contacts).filter_by(name=contact).delete()
        self.session.commit()

    # Функция добавления известных пользователей.
    # Пользователи получаются только с сервера, поэтому таблица очищается.
    def add_users(self, users_list):
        self.session.query(KnownUsers).delete()
        for user in users_list:
            user_row = KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    # Функция сохраняет сообщения
    def save_message(self, from_user, to_user, message):
        message_row = MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    # Функция возвращает контакты
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(Contacts.name).all()]

    # Функция возвращает список известных пользователей
    def get_users(self):
        return [user[0] for user in self.session.query(KnownUsers.username).all()]

    # Функция проверяет наличие пользователя в таблице Известных Пользователей
    def check_user(self, user):
        if self.session.query(KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    # Функция проверяет наличие пользователя в таблице Контактов
    def check_contact(self, contact):
        if self.session.query(Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def contacts_clear(self):
        """Метод, очищающий таблицу со списком контактов."""
        self.session.query(Contacts).delete()
        self.session.commit()

    # Функция возвращает историю переписки
    def get_history(self, from_who=None, to_who=None):
        query = self.session.query(MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [
            (
                history_row.from_user,
                history_row.to_user,
                history_row.message,
                history_row.date,
            )
            for history_row in query.all()
        ]


# отладка
if __name__ == "__main__":
    from sqlalchemy import create_engine

    engine = create_engine(
        "sqlite:///db_client.db3",
        echo=False,
        pool_recycle=7200,
        connect_args={"check_same_thread": False},
    )
    test_db = Storage(engine)

    for i in ["test3", "test4", "test5"]:
        test_db.add_contact(i)
    test_db.add_contact("test4")
    test_db.add_users(["test1", "test2", "test3", "test4", "test5"])
    test_db.save_message("test1", "test2", f"Привет! я тестовое сообщение от {datetime.datetime.now()}!")
    test_db.save_message(
        "test2",
        "test1",
        f"Привет! я другое тестовое сообщение от {datetime.datetime.now()}!",
    )
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user("test1"))
    print(test_db.check_user("test10"))
    print(test_db.get_history("test2"))
    print(test_db.get_history(to_who="test2"))
    print(test_db.get_history("test3"))
    test_db.del_contact("test4")
    print(test_db.get_contacts())
