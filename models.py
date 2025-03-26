from datetime import date, datetime

from db import engine
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Tournament(Base):
    """A tournament is just a name. It is a type 2 slowly-changing dimension
    allows the name to morph but still keep the same parent_id"""
    __tablename__ = 'dg_tourney'
    id: int = Column(Integer, primary_key=True)
    parent_id: int = Column(Integer)
    name: str = Column(String)
    effective_date: date = Column(Date)
    expiry_date: date = Column(Date, default=None)
    created_ts = Column(DateTime, default=func.now())
    lmt = Column(DateTime, default=func.now(), onupdate=func.now())

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        return {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}

class Country(Base):
    __tablename__ = 'country'
    code: str = Column(String, primary_key=True)
    name: str = Column(String)
    flag_emoji_code: str = Column(String)
    flag_emoji: str = Column(String)

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        return {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}


class Player(Base):
    __tablename__ = 'dg_player'
    pdga_id: int = Column(Integer, primary_key=True)
    first_name: str = Column(String)
    last_name: str = Column(String)
    division: str = Column(String)
    photo_url: str = Column(String, default=None)
    country_code: str = Column(String, ForeignKey('country.code'))
    created_ts = Column(DateTime, default=func.now())
    lmt = Column(DateTime, default=func.now(), onupdate=func.now())
    country = relationship("Country")

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
    id: int = Column(Integer, primary_key=True)
    governing_body: str = Column(String)
    designation: str = Column(String)
    start_date: date = Column(Date)
    end_date: date = Column(Date)
    winner_id: int = Column(Integer, ForeignKey('dg_player.pdga_id'))
    tourney_id: int = Column(Integer, ForeignKey('dg_tourney.id'))
    city: str = Column(String, nullable=True)
    state: str = Column(String, nullable=True)
    country_code: str = Column(String, ForeignKey('country.code'))
    pdga_event_id: str = Column(Integer)
    results: list[dict] = Column(JSONB, nullable=True)
    created_ts = Column(DateTime, default=func.now())
    lmt = Column(DateTime, default=func.now(), onupdate=func.now())
    tourney = relationship("Tournament")
    winner = relationship('Player')
    country = relationship('Country')

    @property
    def year(self) -> int:
        return self.end_date.year

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        instance_dict = {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}
        instance_dict['year'] = self.year
        instance_dict['tourney_name'] = self.tourney.name
        instance_dict['country_name'] = self.country.name
        return instance_dict


class Season(Base):
    __tablename__ = 'dg_season'
    tourney_id: int = Column(Integer)
    pdga_event_id: int = Column(Integer, primary_key=True)
    end_date: date = Column(Date, primary_key=True)
    event_designation: str = Column(String, nullable=True)
    division_str: str = Column(String, nullable=True)
    created_ts: datetime = Column(DateTime, default=func.now())
    lmt: datetime = Column(DateTime, default=func.now(), onupdate=func.now())

    @property
    def divisions(self) -> list[str]:
        div_str = self.division_str
        return ['MPO', 'FPO'] if div_str == 'MF' else ['MPO'] if div_str == 'M' else ['FPO']

    @property
    def k_v(self) -> dict:
        # the first entry in a Base instance dict is some sqlalchemy junk, hence  "idx > 0"
        instance_dict = {k: v for idx, (k, v) in enumerate(self.__dict__.items()) if idx > 0}
        instance_dict['divisions'] = self.divisions
        return instance_dict


if __name__ == '__main__':
    if input('Are you sure you want to drop and create these tables? (Y/n) ') == 'Y':
        # Create the database tables
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print('Tables dropped and recreated')
