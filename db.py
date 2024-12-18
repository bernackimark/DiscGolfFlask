from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from config import CONN_STR_UNPACKED, DB_CONN_STR
import psycopg2

# SQLAlchemy
engine = create_engine(DB_CONN_STR)
Session = sessionmaker(bind=engine)

@contextmanager
def get_db_session():
    """Connects to and yields a database connection through SQLAlchemy's sessionmaker"""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_cursor_w_commit():
    """Using raw psycopg2, connect to & yield a database connection.  Commits the transaction, if no error"""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(CONN_STR_UNPACKED)
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        # Roll back in case of exception
        if conn:
            conn.rollback()
        raise
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
