from flask import abort

from models import Player, session

def get_all_players() -> list[dict]:
    results = session.query(Player).all()
    return [e.__dict__ for e in results]

def get_player(pdga_id: int) -> Player:
    player = session.query(Player).filter_by(pdga_id=pdga_id).one_or_none()
    return player or abort(404, f'Player with PDGA# {pdga_id} not found')

def create_player(player):
    pdga_id = player.get('pdga_id')
    if session.query(Player).filter_by(pdga_id=pdga_id).one_or_none():
        abort(406, f"A player with PDGA #{pdga_id} already exists")

    session.add(Player(**player))
    session.commit()
