import pytest
import datetime

from server.database import Users, UsersHistory


def test_user_login(server_storage, session):
    username = "test_user"
    ip_address = "127.0.0.1"
    port = 1234
    server_storage.user_login(username, ip_address, port)
    user = session.query(Users).filter_by(name=username).first()
    assert user is not None  # Пользователь должен существовать
    assert user.name == username  # Имя должно соответствовать


def test_user_logout(server_storage, session):
    username = "user_for_logout"
    server_storage.add_user(username)  # Сначала добавляем пользователя
    server_storage.user_login(username, "127.0.0.1", 1234)  # Пользователь входит
    server_storage.user_logout(username)  # Пользователь выходит

    # Проверяем, что пользователь больше не в списке активных пользователей
    active_users = server_storage.active_users_list()
    assert username not in [user[0] for user in active_users]


def test_add_user(server_storage, session):
    username = "user_to_add"
    result = server_storage.add_user(username)
    assert result is True  # Пользователь успешно добавлен
    # Проверяем, что пользователь действительно добавлен в базу
    assert server_storage.check_user(username) is True


def test_check_user(server_storage, session):
    existing_user = "existing_user"
    non_existing_user = "non_existing_user"
    server_storage.add_user(existing_user)

    # Проверяем существующего пользователя
    assert server_storage.check_user(existing_user) is True
    # Проверяем несуществующего пользователя
    assert server_storage.check_user(non_existing_user) is False


@pytest.mark.only
def test_process_message(server_storage, session):
    sender_name, recipient_name = "user1", "user2"
    # Добавляем пользователей и имитируем их вход
    # server_storage.add_user(sender_name)
    # server_storage.add_user(recipient_name)
    server_storage.user_login(sender_name, "127.0.0.1", 1234)
    server_storage.user_login(recipient_name, "127.0.0.1", 1235)

    assert server_storage.check_user(sender_name) is True
    assert server_storage.check_user(recipient_name) is True

    # Получаем ID пользователей после их добавления и входа
    sender = session.query(Users).filter_by(name=sender_name).first()
    recipient = session.query(Users).filter_by(name=recipient_name).first()

    print(sender.id, recipient.id)

    assert sender is not None  # Проверяем, что пользователь отправитель существует
    assert recipient is not None  # Проверяем, что пользователь получатель существует

    # Проверка, что истории для пользователей существуют
    sender_history = session.query(UsersHistory).filter_by(user=sender.id).first()
    recipient_history = session.query(UsersHistory).filter_by(user=recipient.id).first()

    print(sender_history)
    print(recipient_history)

    # assert sender_history is not None  # Проверяем, что история отправителя существует
    # assert recipient_history is not None  # Проверяем, что история получателя существует

    # Обработка сообщения
    # server_storage.process_message(sender_name, recipient_name)

    # Проверяем историю сообщений после отправки сообщения
    # updated_sender_history = (
    #     session.query(UsersHistory).filter_by(user=sender.id).first()
    # )
    # updated_recipient_history = (
    #     session.query(UsersHistory).filter_by(user=recipient.id).first()
    # )

    # Проверяем, что у отправителя увеличилось число отправленных сообщений и у получателя число полученных
    # assert updated_sender_history.sent == sender_history.sent + 1
    # assert updated_recipient_history.accepted == recipient_history.accepted + 1


def test_add_contact(server_storage, session):
    user1, user2 = "user1", "user2"
    server_storage.add_user(user1)
    server_storage.add_user(user2)
    server_storage.add_contact(user1, user2)

    contacts = server_storage.get_contacts(user1)
    assert user2 in contacts  # Проверяем, что user2 теперь контакт user1


def test_remove_contact(server_storage, session):
    user1, user2 = "user1", "user2"
    server_storage.add_user(user1)
    server_storage.add_user(user2)
    server_storage.add_contact(user1, user2)
    server_storage.remove_contact(user1, user2)

    contacts = server_storage.get_contacts(user1)
    assert user2 not in contacts  # Проверяем, что user2 удален из контактов user1


def test_users_list(server_storage, session):
    username = "new_user"
    server_storage.add_user(username)
    users = server_storage.users_list()

    # Проверяем, что новый пользователь появился в списке пользователей
    assert username in [user[0] for user in users]


def test_active_users_list(server_storage, session):
    username = "active_user"
    server_storage.add_user(username)
    server_storage.user_login(username, "127.0.0.1", 1234)
    active_users = server_storage.active_users_list()

    # Проверяем, что пользователь теперь активный
    assert username in [user[0] for user in active_users]


def test_login_history(server_storage, session):
    username = "user_with_history"
    server_storage.add_user(username)
    server_storage.user_login(username, "127.0.0.1", 1234)

    history = server_storage.login_history(username)
    # Проверяем, что история входа содержит запись о входе
    assert any(h[0] == username for h in history)


def test_get_contacts(server_storage, session):
    user1, user2 = "contact_user1", "contact_user2"
    server_storage.add_user(user1)
    server_storage.add_user(user2)
    server_storage.add_contact(user1, user2)
    contacts = server_storage.get_contacts(user1)

    # Проверяем, что user2 в списке контактов user1
    assert user2 in contacts


def test_message_history(server_storage, session):
    sender, recipient = "msg_user1", "msg_user2"
    server_storage.add_user(sender)
    server_storage.add_user(recipient)
    server_storage.user_login(sender, "127.0.0.1", 1234)
    server_storage.user_login(recipient, "127.0.0.1", 1235)
    server_storage.process_message(sender, recipient)

    messages = server_storage.message_history()
    # Проверяем историю сообщений для учета переданных и полученных сообщений
    assert any(m[0] == sender and m[2] == 1 for m in messages)
    assert any(m[0] == recipient and m[3] == 1 for m in messages)


# ... Продолжайте с тестами для других методов, подобным образом ...


# # test_server_storage.py


# from server.database.storage import ServerStorage


# from sqlalchemy import create_engine

# engine = create_engine(
#     "sqlite:///db_test.db3",
#     echo=False,
#     pool_recycle=7200,
#     connect_args={"check_same_thread": False},
# )


# @pytest.fixture
# def server_storage():
#     # Настройте здесь временную базу данных, если это необходимо
#     storage = ServerStorage(engine)
#     return storage


# def test_user_login(server_storage):
#     username = "test_user"
#     ip_address = "192.168.1.100"
#     port = 8080
#     server_storage.user_login(username, ip_address, port)
#     users_list = server_storage.users_list()
#     assert any(user[0] == username for user in users_list)


# def test_user_logout(server_storage):
#     username = "test_user"
#     # Сначала убедимся, что пользователь вошел
#     server_storage.user_login(username, "192.168.1.100", 8080)
#     server_storage.user_logout(username)
#     active_users = server_storage.active_users_list()
#     assert not any(user[0] == username for user in active_users)


# def test_add_contact(server_storage):
#     user1 = "user1"
#     user2 = "user2"
#     server_storage.add_user(user1)
#     server_storage.add_user(user2)
#     server_storage.add_contact(user1, user2)
#     contacts = server_storage.get_contacts(user1)
#     assert user2 in contacts


# def test_remove_contact(server_storage):
#     user1 = "user1"
#     user2 = "user2"
#     server_storage.add_user(user1)
#     server_storage.add_user(user2)
#     server_storage.add_contact(user1, user2)
#     server_storage.remove_contact(user1, user2)
#     contacts = server_storage.get_contacts(user1)
#     assert user2 not in contacts


# # Дополнительные тесты для других функций...

if __name__ == "__main__":
    pytest.main()
