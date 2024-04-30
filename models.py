from datetime import date, datetime
from dotenv import load_dotenv
import os
from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from typing import Optional

load_dotenv('.env')
DB_CONN_STR = os.getenv('DB_PROD_CONN_STR')
engine = create_engine(DB_CONN_STR)
Session = sessionmaker(bind=engine)
session = Session()

# conn: sqlalchemy.future.Connection = engine.connect()

# def db_query(query: str, params: list[dict] = None) -> list[dict]:
#     with engine.connect() as conn:
#         result = conn.execute(text(query), params if params else [])
#         return [dict(r) for r in result.mappings()]

class Base(DeclarativeBase):
    created_ts: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    lmt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class Tournament(Base):
    __tablename__ = 'dg_tourney'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    city: Mapped[str]
    state: Mapped[Optional[str]]
    country: Mapped[str]

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        return {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}

class Country(Base):
    __tablename__ = 'country'
    code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    flag_emoji: Mapped[str]

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        return {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}


class Player(Base):
    __tablename__ = 'dg_player'
    pdga_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    division: Mapped[str]
    photo_url: Mapped[Optional[str]]
    country_code: Mapped[Optional[str]] = mapped_column(String, ForeignKey('country.code'))

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        instance_dict = {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}
        instance_dict['full_name'] = self.full_name
        return instance_dict


class Event(Base):
    __tablename__ = 'dg_event'
    id: Mapped[int] = mapped_column(primary_key=True)
    governing_body: Mapped[str]
    designation: Mapped[str]
    start_date: Mapped[date]
    end_date: Mapped[date]
    mpo_champ_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dg_player.pdga_id'))
    fpo_champ_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dg_player.pdga_id'))
    tourney_id: Mapped[int] = mapped_column(Integer, ForeignKey('dg_tourney.id'))

    @property
    def year(self) -> int:
        return self.end_date.year

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        instance_dict = {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}
        instance_dict['year'] = self.year
        return instance_dict


# Create the database tables
# Base.metadata.create_all(engine)
