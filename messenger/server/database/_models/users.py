from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
import datetime
from base import Base
from .history import LoginHistory


class Users(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    last_login = Column(DateTime)

    def __init__(self, username):
        self.name = username
        self.last_login = datetime.datetime.now()

    @classmethod
    def check_user(cls, session, username):
        return session.query(cls).filter_by(name=username).first() is not None

    @classmethod
    def user_login(cls, session, username, ip_address, port):
        user = session.query(cls).filter_by(name=username).first()

        # Если имя пользователь существует, обновляем время последнего входа
        if user:
            user.last_login = datetime.datetime.now()
        else:
            # Create new user
            user = cls(name=username)
            session.add(user)
            session.flush()  # Flush to assign an ID without committing transaction

        # Запись как активный пользователь
        new_active_user = ActiveUsers(user_id=user.id, ip_address=ip_address, port=port)
        session.add(new_active_user)

        # Запись в историю входа
        new_login_history = LoginHistory(
            user_id=user.id, date_time=datetime.datetime.now(), ip=ip_address, port=port
        )
        session.add(new_login_history)

        # Commit all changes at once
        session.commit()
        return user


class ActiveUsers(Base):
    __tablename__ = "Active_users"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    ip_address = Column(String)
    port = Column(Integer)
    login_time = Column(DateTime)

    def __init__(self, user_id, ip_address, port, login_time=None):
        self.user_id = user_id
        self.ip_address = ip_address
        self.port = port
        self.login_time = login_time if login_time else datetime.datetime.now()
