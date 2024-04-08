from dataclasses import dataclass
from datetime import date, datetime
from flask import abort

from models import Event, Player, session, Tournament


@dataclass
class EventResult:
    pdga_id: int
    player_name: str
    division: str
    player_photo_url: str
    year: int
    end_date: date
    governing_body: str
    designation: str
    tourney_name: str
    city: str
    state: str
    country: str

    @property
    def k_v(self) -> dict:
        return {k: v for idx, (k, v) in enumerate(self.__dict__.items())}


def get_all_event_results() -> list[dict]:
    result_list = []
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    mpo_results = (session.query(Player, Event, Tournament).
                   join(Player, Event.mpo_champ_id == Player.pdga_id).
                   join(Tournament, Event.tourney_id == Tournament.id)).all()
    for player, event, tournament in mpo_results:
        er = EventResult(player.pdga_id, player.full_name, player.division, player.photo_url,
                         event.year, event.end_date, event.governing_body, event.designation,
                         tournament.name, tournament.city, tournament.state, tournament.country)
        result_list.append(er.__dict__)
    fpo_results = (session.query(Player, Event, Tournament).
                   join(Player, Event.fpo_champ_id == Player.pdga_id).
                   join(Tournament, Event.tourney_id == Tournament.id)).all()
    for player, event, tournament in fpo_results:
        er = EventResult(player.pdga_id, player.full_name, player.division, player.photo_url,
                         event.year, event.end_date, event.governing_body, event.designation,
                         tournament.name, tournament.city, tournament.state, tournament.country)
        result_list.append(er.__dict__)
    return result_list

def _get_all_event_results_as_classes() -> list[EventResult]:
    result_list = []
    mpo_results = (session.query(Player, Event, Tournament).
                   join(Player, Event.mpo_champ_id == Player.pdga_id).
                   join(Tournament, Event.tourney_id == Tournament.id)).all()
    for player, event, tournament in mpo_results:
        er = EventResult(player.pdga_id, player.full_name, player.division, player.photo_url,
                         event.year, event.end_date, event.governing_body, event.designation,
                         tournament.name, tournament.city, tournament.state, tournament.country)
        result_list.append(er)
    fpo_results = (session.query(Player, Event, Tournament).
                   join(Player, Event.fpo_champ_id == Player.pdga_id).
                   join(Tournament, Event.tourney_id == Tournament.id)).all()
    for player, event, tournament in fpo_results:
        er = EventResult(player.pdga_id, player.full_name, player.division, player.photo_url,
                         event.year, event.end_date, event.governing_body, event.designation,
                         tournament.name, tournament.city, tournament.state, tournament.country)
        result_list.append(er)
    return result_list

def get_all_events() -> list[dict]:
    results = session.query(Event).all()
    return [e.__dict__ for e in results]

def _get_all_events_as_classes() -> list[Event]:
    return session.query(Event).all()


# NEXT: EVEN ANVIL REQUIRES THE DATA TO BE SERIALIZED ... I THINK I CAN GET AWAY W RETURNING PYTHON DICTS ...
# HAVE GET_ALL_EVENTS return a list of dicts


def get_event_results_with_kw(**kwargs) -> list[dict]:
    """For any given count of keyword arguments, filter the event results,
    returning only those which match all kwargs"""
    all_results = _get_all_event_results_as_classes()
    events = []
    for event in all_results:
        for key, value in kwargs.items():
            if event.k_v[key] != value:
                break
        else:
            if event not in events:
                events.append(event)
    return [e.k_v for e in events]


def create_event(event):
    tourney_id, end_date, year = event.get('tourney_id'), event.get('end_date'), event.get('end_date').year
    # because year is a class property (not a db column), to use comparisons, must obtain the instance objects first
    tourney_and_year = [e for e in _get_all_events_as_classes() if e.tourney_id == tourney_id and e.year == year]
    if tourney_and_year:
        tourney_name = session.query(Tournament.name).filter_by(id=tourney_id).first()[0]
        abort(406, f"{tourney_name} from {year} already exists")

    session.add(Event(**event))
    session.commit()
