from collections import Counter
from datetime import date, datetime, timedelta
import requests
import streamlit as st

from UI.local_data import local_data
from countries import COUNTRIES_MAP

DATA_URL = 'https://disc-golf.onrender.com/api/results'

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
DESIGNATION_MAP = {'DGPT +': 'Elevated', 'Elite +': 'Elevated',
                   'Elite': 'Standard', 'DGPT Undesignated': 'Standard', 'Silver': 'Standard'}

@st.cache_data
def get_data() -> list[dict]:
    return local_data
    resp = requests.get(DATA_URL)
    if resp.status_code != 200:
        raise ConnectionError("Could not connect to api")
    return resp.json()


def clean_data(api_data: list[dict]) -> list[dict]:
    cleaned_data = []
    for row in api_data:
        # convert serialized dt to python date
        row['end_date'] = datetime.strptime(row['end_date'], "%a, %d %b %Y %H:%M:%S %Z").date()
        # create some columns, including the flag emoji
        row['player'] = f"{row['player_name']}  {COUNTRIES_MAP.get(row['player_country_code'])}"
        row['country_w_flag'] = f"{row['player_country_code']}  {COUNTRIES_MAP.get(row['player_country_code'])}"
        # clean up the designation concepts
        row['designation_map'] = DESIGNATION_MAP.setdefault(row['designation'], row['designation'])
        cleaned_data.append(row)
    return cleaned_data


tmp_data = get_data()
data = clean_data(tmp_data)

def unique_sorted_values(key: str) -> list[str]:
    return sorted({row[key] for row in data if row[key]})


filter_elements = ['player', 'country_w_flag', 'division', 'designation_map', 'tourney_name', 'state', 'country']
filter_map = {e: unique_sorted_values(e) for e in filter_elements}
filter_map['division'].append('All')
filter_map['designation_map'].append('All')

groupers = ['player', 'tourney_name', 'state', 'country', 'designation_map', 'year']


def filter_data(data, filters) -> list[dict]:
    filtered_data = data
    for key, value in filters.items():
        if value and value != 'All':
            if key == "time_period":
                start_date, end_date = value
                filtered_data = [entry for entry in filtered_data if start_date <= entry["end_date"] <= end_date]
            else:
                filtered_data = [entry for entry in filtered_data if entry[key] in value]
    return sorted(filtered_data, key=lambda x: x['end_date'], reverse=True)

def group_data(data, grouper) -> list[dict]:
    """ Returns [{'': Alice, ' ': 5}, {'': Bob}, ' ': 3].  It is ordered by the value descending.
    The keys are blanks because streamlit datatables must have keys, else default column headers are shown. """
    counter = Counter([row[grouper] for row in data if grouper])
    return sorted([{'': k, ' ': v} for k, v in counter.items()], key=lambda x: x[' '], reverse=True)


# DISPLAY THE DATA
# Sidebar - Filters
with st.sidebar:
    st.sidebar.header('Filters')

    selected_players = st.sidebar.multiselect('Winner', filter_map['player'])
    selected_player_countries = st.sidebar.multiselect("Winner's Country", filter_map['country_w_flag'])
    selected_divisions = st.sidebar.radio('Division', filter_map['division'], horizontal=True, index=2)
    selected_designations = st.sidebar.radio('Designation', filter_map['designation_map'], horizontal=True, index=3)
    selected_tournament_names = st.sidebar.multiselect('Tournament', filter_map['tourney_name'])

    # Place state & country side-by-side sidebar into two columns
    col1, col2 = st.sidebar.columns(2)
    selected_tournament_states = col1.multiselect('State', filter_map['state'])
    selected_tournament_countries = col2.multiselect('Country', filter_map['country'])

    selected_time_period = st.sidebar.selectbox('Time Period', list(TIME_PERIODS.keys()), index=5)
    start_date, end_date = TIME_PERIODS[selected_time_period]

# Sidebar - Groupers
with st.sidebar:
    st.sidebar.header('Grouper')
    selected_grouper = st.sidebar.selectbox('Grouper', options=groupers, index=0)

# Apply filters to data
filters = {
    "player": selected_players,
    "country_w_flag": selected_player_countries,
    "tourney_name": selected_tournament_names,
    "division": selected_divisions,
    "designation_map": selected_designations,
    "state": selected_tournament_states,
    "country": selected_tournament_countries,
    "time_period": (start_date, end_date)
}

filtered_data: list[dict] = filter_data(data, filters)
grouped_data: list[dict] = group_data(filtered_data, selected_grouper)
print(grouped_data)

# Main pane - Leaderboard
with st.container():
    st.header('Leaderboard (DGPT Era)')

    if selected_grouper == 'player':
        leaderboard_column_config = {'group': st.column_config.ImageColumn('Winner', width='large')}
    if selected_grouper == 'year':
        leaderboard_column_config = {'group': st.column_config.NumberColumn('Year', format='%d')}
    else:
        leaderboard_column_config = {'group': st.column_config.Column(selected_grouper.replace('_', ' ').title(),
                                                                      width='large')}

    st.dataframe(grouped_data, column_config=leaderboard_column_config)

# Main pane - Table
with st.container():
    st.header('Events')

    column_order = ['year', 'player', 'tourney_name', 'designation_map', 'division', 'state', 'country']
    column_config = {'year': st.column_config.NumberColumn('Year', format='%d'),
                     'player': 'Winner', 'tourney_name': 'Tournament', 'designation_map': 'Designation',
                     'division': 'Division', 'state': 'State', 'country': 'Country'}

    height = (len(filtered_data) * TABLE_ROW_HEIGHT + TABLE_ROW_HEIGHT)

    st.dataframe(filtered_data, height=height, column_order=column_order, column_config=column_config,
                 use_container_width=True)
