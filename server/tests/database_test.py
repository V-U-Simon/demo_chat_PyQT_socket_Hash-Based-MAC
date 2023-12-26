import pytest
import datetime

from db_server import Users, UsersHistory


@pytest.mark.only
def test_user_login(storage, session):
    username = "test_user"
    password = "pass"
    ip_address = "127.0.0.1"
    port = 1234

    new_user = storage.add_user(username, password)  # Сначала добавляем пользователя
    print(new_user)
    storage.user_login(username=username, ip_address=ip_address, port=port)
    user = session.query(Users).filter_by(name=username).first()
    assert user is not None  # Пользователь должен существовать
    assert user.name == username  # Имя должно соответствовать


def test_user_logout(storage, session):
    username = "user_for_logout"
    storage.add_user(username, password="pass")  # Сначала добавляем пользователя
    storage.user_login(username, "127.0.0.1", 1234)  # Пользователь входит
    storage.user_logout(username)  # Пользователь выходит

    # Проверяем, что пользователь больше не в списке активных пользователей
    active_users = storage.active_users_list()
    assert username not in [user[0] for user in active_users]


def test_add_user(storage, session):
    username = "user_to_add"
    new_user = storage.add_user(username, password="pass")

    # Проверяем, что пользователь действительно добавлен в базу
    assert new_user.id == session.query(Users).filter_by(name=username).first().id
    assert storage.check_user_existing(username) is True


def test_check_user_existing(storage, session):
    existing_user = "existing_user"
    non_existing_user = "non_existing_user"
    storage.add_user(existing_user, password="some_hash")

    # Проверяем существующего и несуществующего пользователя
    assert storage.check_user_existing(existing_user) is True
    assert storage.check_user_existing(non_existing_user) is False


def test_add_contact(storage, session):
    user1, user2 = "user1", "user2"
    storage.add_user(user1, password="some_hash")
    storage.add_user(user2, password="some_hash")
    storage.add_contact(user1, user2)

    contacts = storage.get_contacts(user1)
    assert user2 in contacts  # Проверяем, что user2 теперь контакт user1


def test_remove_contact(storage, session):
    user1, user2 = "user1", "user2"
    storage.add_user(user1, password="some_hash")
    storage.add_user(user2, password="some_hash")
    storage.add_contact(user1, user2)
    storage.remove_contact(user1, user2)

    contacts = storage.get_contacts(user1)
    assert user2 not in contacts  # Проверяем, что user2 удален из контактов user1


def test_users_list(storage, session):
    username = "new_user"
    storage.add_user(username, password="pass")
    users = storage.users_list()

    # Проверяем, что новый пользователь появился в списке пользователей
    assert username in [user[0] for user in users]


def test_active_users_list(storage, session):
    username = "active_user"
    storage.add_user(username, password="pass")
    storage.user_login(username, "127.0.0.1", 1234)
    active_users = storage.active_users_list()

    # Проверяем, что пользователь теперь активный
    assert username in [user[0] for user in active_users]


def test_login_history(storage, session):
    username = "user_with_history"
    storage.add_user(username, password="pass")
    storage.user_login(username, "127.0.0.1", 1234)

    history = storage.login_history(username)
    # Проверяем, что история входа содержит запись о входе
    assert any(h[0] == username for h in history)


def test_get_contacts(storage, session):
    user1, user2 = "contact_user1", "contact_user2"
    storage.add_user(user1, password="some_hash")
    storage.add_user(user2, password="some_hash")
    storage.add_contact(user1, user2)
    contacts = storage.get_contacts(user1)

    # Проверяем, что user2 в списке контактов user1
    assert user2 in contacts


def test_process_message(storage, session):
    # Добавляем пользователей и имитируем их вход
    sender_name, recipient_name = "user1", "user2"
    sender = storage.add_user(sender_name, password="some_hash")
    storage.user_login(sender_name, "127.0.0.1", 1234)
    recipient = storage.add_user(recipient_name, password="some_hash")
    storage.user_login(recipient_name, "127.0.0.1", 1235)

    # Проверяем, что пользователи существует
    assert storage.check_user_existing(sender_name) is True
    assert storage.check_user_existing(recipient_name) is True
    assert sender is not None
    assert recipient is not None

    # Проверка, что истории для пользователей существуют
    sender_history = session.query(UsersHistory).filter_by(user=sender.id).first()
    recipient_history = session.query(UsersHistory).filter_by(user=recipient.id).first()
    assert sender_history is not None  # Проверяем, что история отправителя существует
    assert sender_history.sent == 0
    assert recipient_history is not None  # Проверяем, что история получателя существует
    assert recipient_history.accepted == 0

    # Проверяем историю сообщений после отправки сообщения
    storage.process_message(sender_name, recipient_name)
    updated_sender_history = session.query(UsersHistory).filter_by(user=sender.id).first()
    updated_recipient_history = session.query(UsersHistory).filter_by(user=recipient.id).first()
    session.refresh(sender_history)  # Обновление конкретных объектов
    session.refresh(recipient_history)  # Обновление конкретных объектов
    assert updated_sender_history.sent == 1
    assert updated_recipient_history.accepted == 1


def test_message_history(storage, session):
    sender, recipient = "msg_user1", "msg_user2"
    storage.add_user(sender, password="some_hash")
    storage.user_login(sender, "127.0.0.1", 1234)
    storage.add_user(recipient, password="some_hash")
    storage.user_login(recipient, "127.0.0.1", 1235)

    storage.process_message(sender, recipient)
    messages = storage.message_history()
    # Проверяем историю сообщений для учета переданных и полученных сообщений
    assert any(m[0] == sender and m[2] == 1 for m in messages)
    assert any(m[0] == recipient and m[3] == 1 for m in messages)


if __name__ == "__main__":
    pytest.main()
