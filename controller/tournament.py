from datetime import date

from db import get_db_session
from flask import abort
from models import Tournament
from sqlalchemy import desc
from streamlit import balloons, success

def get_all_tourneys() -> list[dict]:
    with get_db_session() as s:
        results = s.query(Tournament).all()
        return [e.k_v for e in results]

def get_all_tourneys_as_classes() -> list[Tournament]:
    with get_db_session() as s:
        return [_ for _ in s.query(Tournament).all()]

def get_tourney(name: str) -> list[Tournament]:
    with get_db_session() as s:
        tourney = s.query(Tournament).filter_by(name=name).all()
        return tourney or abort(404, f'Tournament named {name} not found')

def create_tourney(tourney):
    # TODO: re-write to accommodate parent_id/expiry concepts

    with get_db_session() as s:
        name = tourney.get('name')
        if s.query(Tournament).filter_by(name=name).one_or_none():
            abort(406, f'{name} already exists')

        max_parent_id_row = s.query(Tournament).order_by(desc(Tournament.parent_id)).first()
        tourney['parent_id'] = max_parent_id_row.id + 1
        tourney['effective_date'] = date(date.today().year, 1, 1)

        s.add(Tournament(**tourney))
        s.commit()
        success("Successfully added your tournament to the database")
        balloons()

def update_tourney(tourney):
    ...
