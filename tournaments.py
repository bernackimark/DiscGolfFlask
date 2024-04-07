from flask import abort

from models import Tournament, session

def get_all_tourneys() -> list[dict]:
    results = session.query(Tournament).all()
    return [e.__dict__ for e in results]

def get_tourney(name: str) -> list[Tournament]:
    tourney = session.query(Tournament).filter_by(name=name).all()
    return tourney or abort(404, f'Tournament named {name} not found')

def create_tourney(tourney):
    name, city = tourney.get('name'), tourney.get('city')
    if session.query(Tournament).filter_by(name=name, city=city).one_or_none():
        abort(406, f'{name} in {city} already exists')

    session.add(Tournament(**tourney))
    session.commit()

