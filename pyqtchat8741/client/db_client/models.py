from sqlalchemy import Table, Column, Integer, String, Text, DateTime
import datetime

from .database import metadata, registry


# Таблицы
users = Table(
    "known_users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String),
)


history = Table(
    "message_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("from_user", String),
    Column("to_user", String),
    Column("message", Text),
    Column("date", DateTime),
)


contacts = Table(
    "contacts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
)


# Классы
class KnownUsers:
    def __init__(self, user):
        self.id = None
        self.username = user


class MessageHistory:
    def __init__(self, from_user, to_user, message):
        self.id = None
        self.from_user = from_user
        self.to_user = to_user
        self.message = message
        self.date = datetime.datetime.now()


class Contacts:
    def __init__(self, contact):
        self.id = None
        self.name = contact


# Регистрация классов
registry.map_imperatively(KnownUsers, users)
registry.map_imperatively(MessageHistory, history)
registry.map_imperatively(Contacts, contacts)
