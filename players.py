from dataclasses import dataclass, field
from enum import StrEnum
from flask import abort
from sqlalchemy import update
from streamlit import balloons, error, success

from models import Country, Player, session
from player_photos import PlayerPhotoUpdater

def get_all_players() -> list[dict]:
    results = session.query(Player).all()
    return [e.__dict__ for e in results]

def get_all_players_as_classes() -> list[Player]:
    return [_ for _ in session.query(Player).all()]

def get_player(pdga_id: int) -> Player:
    player = session.query(Player).filter_by(pdga_id=pdga_id).one_or_none()
    return player or abort(404, f'Player with PDGA# {pdga_id} not found')

def get_last_added_player() -> dict:
    return session.query(Player).order_by(Player.created_ts.desc()).limit(1).one_or_none().__dict__

class Division(StrEnum):
    MPO = 'MPO'
    FPO = 'FPO'

@dataclass
class IncomingPlayer:
    pdga_id: int
    first_name: str
    last_name: str
    division: Division
    country_code: str
    photo_url: str = None

    def __post_init__(self):
        if session.query(Player).filter_by(pdga_id=self.pdga_id).one_or_none():
            error(f"A player with PDGA #{self.pdga_id} already exists")
            exit()

        if not session.query(Country).filter_by(code=self.country_code).one_or_none():
            error(f"No such country code of {self.country_code} found")
            exit()

    def create_player(self):
        session.add(Player(**self.__dict__))
        session.commit()
        success(f"Successfully added {self.first_name} {self.last_name} to the database")
        balloons()


def update_player_photos():
    """For all players in db, scrape new photos on pdga.com (else stock image) and update those photo_urls in the db"""
    ids_and_urls: list[tuple[int, str]] = [(p['pdga_id'], p['photo_url']) for p in get_all_players()]
    updated_records = PlayerPhotoUpdater(ids_and_urls).updated_records
    print(f"Updating these records: {updated_records}")
    session.execute(update(Player), updated_records)
    session.commit()
