from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from config import DB_CONN_STR

engine = create_engine(DB_CONN_STR)

# Create a sessionmaker factory
Session = sessionmaker(bind=engine)

@contextmanager
def get_db_session():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
