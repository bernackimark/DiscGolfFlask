from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any
import requests
import streamlit as st

from UI.local_data import local_data
from countries import COUNTRIES_MAP

from events import EventResults

# DATA_URL = 'https://disc-golf.onrender.com/api/results'

MIN_POSSIBLE_DATE, MAX_POSSIBLE_DATE = date(1900, 1, 1), date(2099, 12, 31)
TODAY = date.today()
TIME_PERIODS = {
    'Last 30 Days': (TODAY - timedelta(days=30), TODAY),
    'Last Month': ((TODAY.replace(day=1) - timedelta(days=1)).replace(day=1), TODAY.replace(day=1) - timedelta(days=1)),
    'This Year': (date(TODAY.year, 1, 1), TODAY),
    'Last Year': (date(TODAY.year - 1, 1, 1), TODAY.replace(month=1, day=1) - timedelta(days=1)),
    'Last 365 Days': (TODAY - timedelta(days=365), TODAY),
    'All Time (DGPT Era)': (MIN_POSSIBLE_DATE, MAX_POSSIBLE_DATE)
}
TABLE_ROW_HEIGHT = 36

@st.cache_data
def get_data() -> list[dict]:
    results = EventResults()
    return results.event_results_flat
    resp = requests.get(DATA_URL)
    if resp.status_code != 200:
        raise ConnectionError("Could not connect to api")
    return resp.json()


def clean_data(dirty_data: list[dict]) -> list[dict]:
    designation_map = {'DGPT +': 'Elevated', 'Elite +': 'Elevated',
                       'Elite': 'Standard', 'DGPT Undesignated': 'Standard', 'Silver': 'Standard'}
    cleaned_data = []
    for row in dirty_data:
        # create some columns, including the flag emoji
        row['player_w_flag'] = f"{row['player_full_name']}  {row['country_flag_emoji']}"
        row['country_w_flag'] = f"{row['country_name']}  {row['country_flag_emoji']}"
        # clean up the designation concepts
        row['event_designation_map'] = designation_map.setdefault(row['event_designation'], row['event_designation'])
        cleaned_data.append(row)
    return cleaned_data


tmp_data = get_data()
data = clean_data(tmp_data)

def unique_sorted_values(key: str) -> list[str]:
    return sorted({row[key] for row in data if row[key]})

def populate_filters() -> dict:
    filter_elements = ['player_w_flag', 'country_w_flag', 'player_division', 'event_designation_map', 'tourney_name',
                       'tourney_state', 'tourney_country']
    return {e: unique_sorted_values(e) for e in filter_elements}

def populate_groupers() -> dict:
    grouper_elements = ['player_w_flag', 'tourney_name', 'tourney_state', 'tourney_country',
                        'event_designation_map', 'event_year']
    return {'event_grouper': grouper_elements}


filter_map = populate_filters()
grouper_map = populate_groupers()


def filter_data(data, filters) -> list[dict]:
    filtered_data = data
    for key, value in filters.items():
        if value and value != 'All':
            if key == "time_period":
                filtered_data = [entry for entry in filtered_data if value[0] <= entry['event_end_date'] <= value[1]]
            else:
                filtered_data = [entry for entry in filtered_data if entry[key] in value]
    return sorted(filtered_data, key=lambda x: x['event_end_date'], reverse=True)

def group_data(data, grouper) -> list[dict]:
    """ Returns [{'': Alice, ' ': 5}, {'': Bob}, ' ': 3].  It is ordered by the value descending.
    The keys are blanks because streamlit datatables must have keys, else default column headers are shown. """
    counter = Counter([row[grouper] for row in data if grouper])
    return sorted([{'': k, ' ': v} for k, v in counter.items()], key=lambda x: x[' '], reverse=True)


# DISPLAY THE DATA
# Sidebar - Groupers
with st.sidebar:
    st.sidebar.header('Grouper')
    selected_grouper = st.sidebar.selectbox('Grouper', options=grouper_map['event_grouper'], index=0)

# Sidebar - Filters
with st.sidebar:
    st.sidebar.header('Filters')

    selected_players = st.sidebar.multiselect('Winner', filter_map['player_w_flag'])
    selected_player_countries = st.sidebar.multiselect("Winner's Country", filter_map['country_w_flag'])
    filter_map['player_division'].append('All')
    selected_divisions = st.sidebar.radio('Division', filter_map['player_division'], horizontal=True, index=2)
    filter_map['event_designation_map'].append('All')
    selected_designations = st.sidebar.radio('Designation', filter_map['event_designation_map'], horizontal=True, index=3)
    selected_tournament_names = st.sidebar.multiselect('Tournament', filter_map['tourney_name'])

    # Place state & country side-by-side sidebar into two columns
    col1, col2 = st.sidebar.columns(2)
    selected_tournament_states = col1.multiselect('State', filter_map['tourney_state'])
    selected_tournament_countries = col2.multiselect('Country', filter_map['tourney_country'])

    selected_time_period = st.sidebar.selectbox('Time Period', list(TIME_PERIODS.keys()), index=5)
    start_date, end_date = TIME_PERIODS[selected_time_period]


# Apply filters to data
filters = {
    "player_w_flag": selected_players,
    "country_w_flag": selected_player_countries,
    "tourney_name": selected_tournament_names,
    "player_division": selected_divisions,
    "event_designation_map": selected_designations,
    "tourney_state": selected_tournament_states,
    "tourney_country": selected_tournament_countries,
    "time_period": (start_date, end_date)
}

filtered_data: list[dict] = filter_data(data, filters)
grouped_data: list[dict] = group_data(filtered_data, selected_grouper)

# Main pane - Leaderboard
with st.container():
    st.header('Leaderboard (DGPT Era)')
    lb_col_config = {'player_w_flag': {'': st.column_config.Column('Winner', width='large')},
                     'event_year': {'': st.column_config.NumberColumn('Year', format='%d')},
                     '_': {'': st.column_config.Column(selected_grouper.replace('_', ' ').title(), width='large')}}
    st.dataframe(grouped_data, column_config=lb_col_config.get(selected_grouper) or lb_col_config['_'], hide_index=True)

# Main pane - Table
with st.container():
    st.header('Events')
    column_order = ['event_year', 'player_w_flag', 'tourney_name', 'event_designation_map',
                    'player_division', 'tourney_state', 'tourney_country']
    column_config = {'event_year': st.column_config.NumberColumn('Year', format='%d'),
                     'player_w_flag': 'Winner', 'tourney_name': 'Tournament', 'event_designation_map': 'Designation',
                     'player_division': 'Division', 'tourney_state': 'State', 'tourney_country': 'Country'}
    height = (len(filtered_data) * TABLE_ROW_HEIGHT + TABLE_ROW_HEIGHT)
    st.dataframe(filtered_data, height=height, column_order=column_order, column_config=column_config,
                 use_container_width=True)
