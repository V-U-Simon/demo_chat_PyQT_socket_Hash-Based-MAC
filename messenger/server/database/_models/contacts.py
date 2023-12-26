from sqlalchemy import Column, Integer, ForeignKey
from base import Base


class UsersContacts(Base):
    __tablename__ = "Contacts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    contact_id = Column(Integer, ForeignKey("Users.id"))

    def __init__(self, user_id, contact_id):
        self.user_id = user_id
        self.contact_id = contact_id
