from dataclasses import dataclass, field
from datetime import date
from sqlalchemy.engine.row import Row
from streamlit import balloons, error, success

from models import Country, Event, Player, session, Tournament
from players import get_all_players_as_classes
from tournaments import get_all_tourneys_as_classes


@dataclass
class IncomingEvent:
    governing_body: str
    designation: str
    start_date: date
    end_date: date
    winner_name: str
    tourney_name: str
    winner_id: int = field(init=False)
    division: str = field(init=False)
    tourney_id: int = field(init=False)

    def __post_init__(self):
        all_players = get_all_players_as_classes()
        if self.winner_name not in {e.full_name for e in all_players}:
            error(f"{self.winner_name} doesn't exist yet. Please create the player and re-run.")
            exit()
        self.winner_id, self.division = next((player.pdga_id, player.division) for player in all_players if self.winner_name == player.full_name)

        all_tourneys = get_all_tourneys_as_classes()
        if self.tourney_name not in {e.name for e in all_tourneys}:
            error(f"{self.tourney_name} doesn't exist yet. Please create the tournament and re-run.")
            exit()
        self.tourney_id = next(tourney.id for tourney in all_tourneys if self.tourney_name == tourney.name)

        all_events: list[Event] = session.query(Event).all()
        for e in all_events:
            if self.tourney_id == e.tourney_id and self.end_date == e.end_date:
                existing_division = next(p.division for p in all_players if p.pdga_id == e.winner_id)
                if self.division == existing_division:
                    error(f"{self.tourney_name} for the {self.division} division ending on {self.end_date} already exists.")
                    exit()

        if self.governing_body not in {e.governing_body for e in all_events}:
            error(f"{self.governing_body} is not a legitimate governing body")
            exit()

        if self.end_date < self.start_date:
            error(f"End date cannot be before start date")
            exit()

    @property
    def db_dict(self) -> dict:
        return {'governing_body': self.governing_body, 'designation': self.designation, 'start_date': self.start_date,
                'end_date': self.end_date, 'winner_id': self.winner_id, 'tourney_id': self.tourney_id}

    def create_event(self) -> None:
        session.add(Event(**self.db_dict))
        session.commit()
        success("Successfully added your event to the database")
        balloons()


@dataclass
class EventResults:
    results: list[Row] = field(init=False)

    def __post_init__(self):
        self.results = self._get_all_event_result_data()

    @staticmethod
    def _get_all_event_result_data() -> list[Row]:
        results = (session.query(Player, Event, Tournament, Country).
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
