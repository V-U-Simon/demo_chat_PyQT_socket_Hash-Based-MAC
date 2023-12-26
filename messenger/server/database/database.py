from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import registry

engine = create_engine(
    "sqlite:///db_server.db3",
    echo=False,
    pool_recycle=7200,
    connect_args={"check_same_thread": False},
)


metadata = MetaData()  # создаем экземпляр MetaData
registry = registry()  # создаем экземпляр registry


# db_session = sessionmaker(bind=engine)()
# todo: from source engine
# engine = create_engine(
#     f"sqlite:///{path}",
#     echo=False,
#     pool_recycle=7200,
#     connect_args={"check_same_thread": False},
# )

# "db_test_server.db3"
