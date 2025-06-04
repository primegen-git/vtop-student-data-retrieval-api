from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///./vtop_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()
