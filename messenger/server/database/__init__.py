# In database/__init__.py
from .models import Users, ActiveUsers, LoginHistory, Contacts, UsersHistory
from .database import engine, metadata

# from .session import init_db, get_scoped_session, engine


# Optionally, initialize database here or leave it to main app
# db_uri = "sqlite:///mydatabase.db"  # or other appropriate URI
# Session = init_db(db_uri)
