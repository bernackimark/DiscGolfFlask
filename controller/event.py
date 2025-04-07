from dataclasses import dataclass, field
from datetime import date
import json

from db import get_db_session, get_cursor_w_commit
from models import Country, Event, Player, Tournament
from .event_pdga import PDGAEvent
from .player import get_all_players
from .season import get_all_seasons
from sqlalchemy import desc
from .tournament import get_all_tourneys


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
    """Updates dg_event.results column on an existing dg_event record"""
    if not pdga_event_obj.is_complete:
        raise ValueError("The event hasn't been completed on the PDGA website.")

    div_results = pdga_event_obj.data['division_results'][division]

    with get_cursor_w_commit() as c:
        query = ("update dg_event set results = %s from dg_player p "
                 "where dg_event.pdga_event_id = %s and p.division = %s and dg_event.winner_id = p.pdga_id;")
        c.execute(query, (json.dumps(div_results), pdga_event_obj.pdga_event_id, division))

def write_event_to_db(pdga_event_id: int, designation: str, tourney_id: int, div: str) -> None:
    pe = PDGAEvent(pdga_event_id)
    governing_body = 'PDGA' if designation == 'Major' else 'DGPT'
    winner_id = pe.get_winner_by_division(div)
    winner_div = next(p['division'] for p in get_all_players() if p['pdga_id'] == winner_id)

    if pe.status != pe.PDGA_COMPLETED_EVENT_STATUS:
        raise ValueError(f"Event results for the {pe.end_date} event aren't finalized on the PDGA site.")

    if winner_id not in {p['pdga_id'] for p in get_all_players()}:
        raise ValueError(f"Player w PDGA# {winner_id} doesn't exist yet. Please create the player and re-run.")

    if tourney_id not in {t['id'] for t in get_all_tourneys()}:
        raise ValueError(f"Can't find tourney ID {tourney_id} in db. Please create the tournament & re-run.")

    for e in get_all_events():
        if e['tourney_id'] == tourney_id and e['end_date'] == pe.end_date and winner_div == div:
            raise ValueError(f"Tournament ID {tourney_id} for {div} ending on {pe.end_date} already exists.")

    if governing_body not in {e['governing_body'] for e in get_all_events()}:
        raise ValueError(f"{governing_body} is not a legitimate governing body")

    with get_db_session() as s:
        s.add(Event(governing_body=governing_body, designation=designation,
                    start_date=pe.begin_date, end_date=pe.end_date,
                    city=pe.city, state=pe.state_code, country_code=pe.country_code,
                    pdga_event_id=pdga_event_id, winner_id=winner_id, tourney_id=tourney_id,
                    results=json.dumps(pe.data['division_results'][div])))
        s.commit()

def get_completed_unloaded_events() -> list[dict | None]:
    """Query dg_season & dg_event to find unloaded events. Returns a list of dicts with data needed for write_to_db()"""
    events_to_write = []
    completed_season_events: list[dict] = [e for e in get_all_seasons() if e['end_date'] < date.today()]
    loaded_pdga_event_ids: list[int] = [e['pdga_event_id'] for e in get_all_events()]
    for se in completed_season_events:
        if se['pdga_event_id'] in loaded_pdga_event_ids:
            continue
        for div in se['divisions']:
            events_to_write.append({'pdga_event_id': se['pdga_event_id'], 'designation': se['event_designation'],
                                    'tourney_id': se['tourney_id'], 'div': div})
    return events_to_write
