from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Text
import datetime

from .database import metadata, registry

# Таблицы
users_table = Table(
    "Users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("password_hash", String),
    Column("last_login", DateTime),
    Column("pubkey", Text),
)


active_users_table = Table(
    "Active_users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user", ForeignKey("Users.id"), unique=True),
    Column("ip_address", String),
    Column("port", Integer),
    Column("login_time", DateTime),
)

user_login_history = Table(
    "Login_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", ForeignKey("Users.id")),
    Column("date_time", DateTime),
    Column("ip", String),
    Column("port", String),
)

contacts = Table(
    "Contacts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user", ForeignKey("Users.id")),
    Column("contact", ForeignKey("Users.id")),
)

users_history_table = Table(
    "History",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user", ForeignKey("Users.id")),
    Column("sent", Integer),
    Column("accepted", Integer),
)


# Классы
class Users:
    def __init__(self, username, password_hash):
        self.id = None
        self.name = username
        self.password_hash = password_hash
        self.last_login = datetime.datetime.now()
        self.pubkey = None


class ActiveUsers:
    def __init__(self, user_id, ip_address, port, login_time):
        self.id = None
        self.user = user_id
        self.ip_address = ip_address
        self.port = port
        self.login_time = login_time


class LoginHistory:
    def __init__(self, name, date, ip, port):
        self.id = None
        self.name = name
        self.date_time = date
        self.ip = ip
        self.port = port


class Contacts:
    def __init__(self, user, contact):
        self.id = None
        self.user = user
        self.contact = contact


class UsersHistory:
    def __init__(self, user):
        self.id = None
        self.user = user
        self.sent = 0
        self.accepted = 0


# Регистрация классов
registry.map_imperatively(Users, users_table)
registry.map_imperatively(ActiveUsers, active_users_table)
registry.map_imperatively(LoginHistory, user_login_history)
registry.map_imperatively(Contacts, contacts)
registry.map_imperatively(UsersHistory, users_history_table)
