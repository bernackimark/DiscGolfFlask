from dataclasses import dataclass, field
from datetime import date
import json
from typing import Self

from db import get_db_session, get_cursor_w_commit
from models import Country, Event, Player, Tournament
from .event_pdga import PDGAEvent
from .player import get_all_players
from sqlalchemy import desc
from .tournament import get_all_tourneys


@dataclass(kw_only=True)
class NewEvent:
    governing_body: str
    designation: str
    start_date: date
    end_date: date
    city: str
    state: str
    country_code: str
    pdga_event_id: int
    winner_name: str = None
    winner_id: int = None
    tourney_id: int = None
    tourney_name: str = None
    division: str = field(init=False)

    def __post_init__(self):
        all_players = get_all_players()
        if self.winner_id is not None:
            winner_id, div = next(((p['pdga_id'], p['division']) for p in all_players
                                   if self.winner_id == p['pdga_id']), None)
            self.winner_id = winner_id
            self.division = div
        else:
            if self.winner_name not in {e['full_name'] for e in all_players}:
                raise ValueError(f"{self.winner_name} doesn't exist yet. Please create the player and re-run.")
            self.winner_id, self.division = next((player['pdga_id'], player['division']) for player in all_players
                                                 if self.winner_name == player['full_name'])

        all_tourneys = get_all_tourneys()
        if self.tourney_id is not None:
            self.tourney_name = next((t['name'] for t in all_tourneys if t['id'] == self.tourney_id), None)
            if not self.tourney_name:
                raise ValueError(f"Can't find tourney ID {self.tourney_id} in db")
        else:
            if self.tourney_name not in {e['name'] for e in all_tourneys}:
                raise ValueError(f"{self.tourney_name} doesn't exist yet. Please create the tournament and re-run.")
            self.tourney_id = next(tourney['id'] for tourney in all_tourneys if self.tourney_name == tourney['name'])

        with get_db_session() as s:
            all_events: list[dict] = get_all_events()
            for e in all_events:
                if self.tourney_name == e['tourney_name'] and self.end_date == e['end_date']:
                    existing_division = next(p['division'] for p in all_players if p['pdga_id'] == e['winner_id'])
                    if self.division == existing_division:
                        raise ValueError(f"{self.tourney_name} for the {self.division} division "
                                         f"ending on {self.end_date} already exists.")

        if self.governing_body not in {e['governing_body'] for e in all_events}:
            raise ValueError(f"{self.governing_body} is not a legitimate governing body")

        if self.end_date < self.start_date:
            raise ValueError(f"End date cannot be before start date")

    @classmethod
    def create_from_db_and_pdga_site(cls, pdga_event_id: int, designation: str, tourney_id: int, div: str) -> Self:
        pe = PDGAEvent(pdga_event_id)
        governing_body = 'PDGA' if designation == 'Major' else 'DGPT'
        return cls(governing_body=governing_body, designation=designation,
                   start_date=pe.begin_date, end_date=pe.end_date,
                   city=pe.city, state=pe.state_code, country_code=pe.country_code,
                   pdga_event_id=pdga_event_id, winner_id=pe.get_winner_by_division(div), tourney_id=tourney_id)

    @property
    def db_dict(self) -> dict:
        return {'governing_body': self.governing_body, 'designation': self.designation, 'start_date': self.start_date,
                'end_date': self.end_date, 'winner_id': self.winner_id, 'tourney_id': self.tourney_id,
                'city': self.city, 'state': self.state, 'country_code': self.country_code,
                'pdga_event_id': self.pdga_event_id}

    def create_event(self) -> None:
        with get_db_session() as s:
            s.add(Event(**self.db_dict))
            s.commit()

            pdga_event = PDGAEvent(self.pdga_event_id)
            try:
                update_dg_event(pdga_event, self.division)
            except ValueError as e:
                raise ValueError(e)

@dataclass
class EventResults:
    results: list[dict[str: dict]] = field(init=False)

    def __post_init__(self):
        self.results = self._get_all_event_result_data()

    @staticmethod
    def _get_all_event_result_data() -> list[dict[str: dict]]:
        """ Returns a list of nested dictionaries
        {'event': {'end_date': ...}, 'player': {'full_name': ...}}"""
        with get_db_session() as s:
            results = (s.query(Player, Event, Tournament, Country).
                       join(Player, Event.winner_id == Player.pdga_id).
                       join(Tournament, Event.tourney_id == Tournament.id).
                       join(Country, Player.country_code == Country.code)).all()
            return [{'event': event.k_v, 'player': player.k_v, 'country': country.k_v, 'tourney': tourney.k_v}
                    for player, event, tourney, country in results]

    @property
    def results_flat(self) -> list[dict]:
        """ Returns a single flattened dictionary for each event result.
        Because tables may have the same column names, fully qualify the keys as table_{db_col}"""
        flattened = []
        for event in self.results:
            new_event = {}
            for parent_key, data in event.items():
                for k, v in data.items():
                    new_event[f'{parent_key}_{k}'] = v
            flattened.append(new_event)
        return flattened

    @property
    def winners(self) -> list[str]:
        return sorted({e['player_full_name'] for e in self.results_flat if e['player_full_name']})

    @property
    def tourney_names(self) -> list[str]:
        return sorted({e['tourney_name'] for e in self.results_flat if e['tourney_name']})

    @property
    def last_added_event(self) -> dict:
        return sorted([e for e in self.results_flat], key=lambda x: x['event_end_date'], reverse=True)[0]


def get_all_events() -> list[dict]:
    with get_db_session() as s:
        events = s.query(Event).all()
        return [e.k_v for e in events]

def get_last_added_event() -> tuple[str, date]:
    """Used to support dg_admin, which only needs to see the last event"""
    with get_db_session() as s:
        e = s.query(Event).order_by(desc(Event.created_ts)).first()
        tourney_name = e.tourney.name
        tourney_end_date = e.end_date
        return tourney_name, tourney_end_date

def update_dg_event(pdga_event_obj: PDGAEvent, division: str):
    if not pdga_event_obj.is_complete:
        raise ValueError("The event hasn't been completed on the PDGA website.")

    div_results = pdga_event_obj.data['division_results'][division]

    with get_cursor_w_commit() as c:
        query = ("update dg_event set results = %s from dg_player p "
                 "where dg_event.pdga_event_id = %s and p.division = %s and dg_event.winner_id = p.pdga_id;")
        c.execute(query, (json.dumps(div_results), pdga_event_obj.pdga_event_id, division))

