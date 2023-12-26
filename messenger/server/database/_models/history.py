from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from base import Base


class LoginHistory(Base):
    __tablename__ = "Login_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    date_time = Column(DateTime)
    ip = Column(String)
    port = Column(String)

    def __init__(self, user_id, date_time, ip, port):
        self.user_id = user_id
        self.date_time = date_time
        self.ip = ip
        self.port = port


class UsersHistory(Base):
    __tablename__ = "History"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    sent = Column(Integer)
    accepted = Column(Integer)

    def __init__(self, user_id):
        self.user_id = user_id
        self.sent = 0
        self.accepted = 0
