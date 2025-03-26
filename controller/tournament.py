from datetime import date, datetime

from db import get_db_session
from flask import abort
from models import Tournament
from sqlalchemy import func

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

def create_tourney(new_tourney_name: str, expires_name: str = None, expires_id: int = None):
    with get_db_session() as s:
        if s.query(Tournament).filter_by(name=new_tourney_name).one_or_none():
            raise ValueError(f'{new_tourney_name} already exists')

        max_id = s.query(func.max(Tournament.id)).scalar()
        jan_1_this_yr = date(date.today().year, 1, 1)
        dec_31_last_yr = date(date.today().year - 1, 12, 31)

        try:
            if not expires_name:
                s.add(Tournament(parent_id=max_id+1, effective_date=jan_1_this_yr), name=new_tourney_name)
            else:
                s.add(Tournament(parent_id=expires_id, effective_date=jan_1_this_yr), name=new_tourney_name)
                s.query(Tournament).filter_by(id=expires_id
                                              ).update({'expiry_date': dec_31_last_yr, 'lmt': datetime.now()})
            s.commit()
        except Exception as e:
            raise e
