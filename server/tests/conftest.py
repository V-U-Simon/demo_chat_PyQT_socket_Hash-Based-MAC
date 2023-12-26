import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.db_server import metadata
from server.db_server.storage import Storage


# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine("sqlite:///:memory:")  # Или другой URL для тестовой БД
    metadata.create_all(engine)  # Создаем структуру БД
    return engine


# Фикстура для создания сессии
@pytest.fixture(scope="function")
def session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session  # используется для тестов
    session.close()
    transaction.rollback()
    connection.close()


# Фикстура для ServerStorage
@pytest.fixture(scope="function")
def storage(session):
    return Storage(session.bind)
