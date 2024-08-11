from dataclasses import dataclass, field
from datetime import date

from db import get_db_session
from models import Country, Event, Player, Tournament
from players import get_all_players
from sqlalchemy import desc
from sqlalchemy.engine.row import Row
from streamlit import balloons, error, success
from tournaments import get_all_tourneys


@dataclass
class NewEvent:
    governing_body: str
    designation: str
    start_date: date
    end_date: date
    winner_name: str
    tourney_name: str
    city: str
    state: str
    country_code: str
    winner_id: int = field(init=False)
    division: str = field(init=False)
    tourney_id: int = field(init=False)

    def __post_init__(self):
        all_players = get_all_players()
        if self.winner_name not in {e['full_name'] for e in all_players}:
            error(f"{self.winner_name} doesn't exist yet. Please create the player and re-run.")
            exit()
        self.winner_id, self.division = next((player['pdga_id'], player['division']) for player in all_players
                                             if self.winner_name == player['full_name'])

        all_tourneys = get_all_tourneys()
        if self.tourney_name not in {e['name'] for e in all_tourneys}:
            error(f"{self.tourney_name} doesn't exist yet. Please create the tournament and re-run.")
            exit()
        self.tourney_id = next(tourney['id'] for tourney in all_tourneys if self.tourney_name == tourney['name'])

        with get_db_session() as s:
            all_events: list[dict] = get_all_events()
            for e in all_events:
                if self.tourney_name == e['tourney_name'] and self.end_date == e['end_date']:
                    existing_division = next(p['division'] for p in all_players if p['pdga_id'] == e['winner_id'])
                    if self.division == existing_division:
                        error(f"{self.tourney_name} for the {self.division} division ending on {self.end_date} already exists.")
                        exit()

        if self.governing_body not in {e['governing_body'] for e in all_events}:
            error(f"{self.governing_body} is not a legitimate governing body")
            exit()

        if self.end_date < self.start_date:
            error(f"End date cannot be before start date")
            exit()

    @property
    def db_dict(self) -> dict:
        return {'governing_body': self.governing_body, 'designation': self.designation, 'start_date': self.start_date,
                'end_date': self.end_date, 'winner_id': self.winner_id, 'tourney_id': self.tourney_id,
                'city': self.city, 'state': self.state, 'country_code': self.country_code}

    def create_event(self) -> None:
        with get_db_session() as s:
            s.add(Event(**self.db_dict))
            s.commit()
            success("Successfully added your event to the database")
            balloons()


@dataclass
class EventResults:
    results: list[Row] = field(init=False)

    def __post_init__(self):
        self.results = self._get_all_event_result_data()

    @staticmethod
    def _get_all_event_result_data() -> list[Row]:
        with get_db_session() as s:
            results = (s.query(Player, Event, Tournament, Country).
                       join(Player, Event.winner_id == Player.pdga_id).
                       join(Tournament, Event.tourney_id == Tournament.id).
                       join(Country, Player.country_code == Country.code)).all()
            return [_ for _ in results]

    @property
    def event_results_nested(self) -> list[dict[str, dict]]:
        """ Returns a list of nested dictionaries
        {'event': {'end_date': ...}, 'player': {'full_name': ...}}"""
        return [{'event': event.k_v, 'player': player.k_v, 'country': country.k_v, 'tourney': tourney.k_v}
                for player, event, tourney, country in self.results]

    @property
    def event_results_flat(self) -> list[dict]:
        """ Returns a single flattened dictionary for each event result.
        Because tables may have the same column names, fully qualify the keys as table_{db_col}"""
        event_results = []
        for player, event, tourney, country in self.results:
            p = {f'player_{k}': v for k, v in player.k_v.items()}
            e = {f'event_{k}': v for k, v in event.k_v.items()}
            t = {f'tourney_{k}': v for k, v in tourney.k_v.items()}
            c = {f'country_{k}': v for k, v in country.k_v.items()}
            event_results.append({**p, **e, **t, **c})
        return event_results

    @property
    def winners(self) -> list[str]:
        return sorted({e['player_full_name'] for e in self.event_results_flat if e['player_full_name']})

    @property
    def tourney_names(self) -> list[str]:
        return sorted({e['tourney_name'] for e in self.event_results_flat if e['tourney_name']})

    @property
    def last_added_event(self) -> dict:
        return sorted([e for e in self.event_results_flat], key=lambda x: x['event_end_date'], reverse=True)[0]


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
