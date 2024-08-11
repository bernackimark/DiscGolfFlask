from dataclasses import dataclass
from enum import StrEnum

from db import get_db_session
from flask import abort
from models import Country, Player
from .player_photos import PlayerPhotoUpdater
from sqlalchemy import update
from streamlit import balloons, error, success


def get_all_players() -> list[dict]:
    with get_db_session() as s:
        results = s.query(Player).all()
        return [e.k_v for e in results]

def get_all_players_as_classes() -> list[Player]:
    with get_db_session() as s:
        return [_ for _ in s.query(Player).all()]

def get_player(pdga_id: int) -> Player:
    with get_db_session() as s:
        player = s.query(Player).filter_by(pdga_id=pdga_id).one_or_none()
        return player or abort(404, f'Player with PDGA# {pdga_id} not found')

def get_last_added_player() -> dict:
    with get_db_session() as s:
        return s.query(Player).order_by(Player.created_ts.desc()).limit(1).one_or_none().k_v

class Division(StrEnum):
    MPO = 'MPO'
    FPO = 'FPO'

@dataclass
class NewPlayer:
    pdga_id: int
    first_name: str
    last_name: str
    division: Division
    country_code: str
    photo_url: str = None

    def __post_init__(self):
        with get_db_session() as s:
            if s.query(Player).filter_by(pdga_id=self.pdga_id).one_or_none():
                error(f"A player with PDGA #{self.pdga_id} already exists")
                return

            if not s.query(Country).filter_by(code=self.country_code).one_or_none():
                error(f"No such country code of {self.country_code} found")
                return

            s.add(Player(**self.__dict__))
            s.commit()
            success(f"Successfully added {self.first_name} {self.last_name} to the database")
            balloons()


def update_player_photos():
    """For all players in db, scrape new photos on pdga.com (else stock image) and update those photo_urls in the db"""
    ids_and_urls: list[tuple[int, str]] = [(p['pdga_id'], p['photo_url']) for p in get_all_players()]
    updated_records = PlayerPhotoUpdater(ids_and_urls).updated_records
    print(f"Updating these records: {updated_records}")
    with get_db_session() as s:
        s.execute(update(Player), updated_records)
        s.commit()
