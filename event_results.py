from dataclasses import dataclass
from datetime import date

from models import Country, Event, Player, session, Tournament
from sqlalchemy.engine.row import Row


def _get_all_event_result_data() -> list[Row]:
    result_list = []
    mpo_results = (session.query(Player, Event, Tournament, Country).
                   join(Player, Event.mpo_champ_id == Player.pdga_id).
                   join(Tournament, Event.tourney_id == Tournament.id).
                   join(Country, Player.country_code == Country.code)).all()
    fpo_results = (session.query(Player, Event, Tournament, Country).
                   join(Player, Event.fpo_champ_id == Player.pdga_id).
                   join(Tournament, Event.tourney_id == Tournament.id).
                   join(Country, Player.country_code == Country.code)).all()
    for row in mpo_results:
        result_list.append(row)
    for row in fpo_results:
        result_list.append(row)
    return result_list


def get_all_event_results_as_nested_dicts(records: list[Row]) -> list[dict[str, dict]]:
    """ Returns a list of nested dictionaries
    {'event': {'end_date': ...}, 'player': {'full_name': ...}}
    """
    return [{'event': event.k_v, 'player': player.k_v, 'country': country.k_v, 'tourney': tourney.k_v} for player, event, tourney, country in records]


def get_all_event_results_as_flat_dict(records: list[Row]) -> list[dict]:
    """ Returns a single flattened dictionary for each event result.  Note: some column names are shared across tables,
    and only one such column name will get in"""
    return [{**player.k_v, **event.k_v, **tourney.k_v, **country.k_v} for player, event, tourney, country in records]


x = get_all_event_results_as_nested_dicts(_get_all_event_result_data())
y = get_all_event_results_as_flat_dict(_get_all_event_result_data())

for row in y:
    print(row)
    break
