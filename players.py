from flask import abort
from sqlalchemy import update

from models import Player, session
from player_photos import PlayerPhotoUpdater

def get_all_players() -> list[dict]:
    results = session.query(Player).all()
    return [e.__dict__ for e in results]

def get_all_players_as_classes() -> list[Player]:
    return [_ for _ in session.query(Player).all()]

def get_player(pdga_id: int) -> Player:
    player = session.query(Player).filter_by(pdga_id=pdga_id).one_or_none()
    return player or abort(404, f'Player with PDGA# {pdga_id} not found')

def create_player(player):
    pdga_id = player.get('pdga_id')
    if session.query(Player).filter_by(pdga_id=pdga_id).one_or_none():
        abort(406, f"A player with PDGA #{pdga_id} already exists")

    session.add(Player(**player))
    session.commit()

def update_player_photos():
    """For all players in db, scrape new photos on pdga.com (else stock image) and update those photo_urls in the db"""
    ids_and_urls: list[tuple[int, str]] = [(p['pdga_id'], p['photo_url']) for p in get_all_players()]
    updated_records = PlayerPhotoUpdater(ids_and_urls).updated_records
    print(f"Updating these records: {updated_records}")
    session.execute(update(Player), updated_records)
    session.commit()
