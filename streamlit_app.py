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
    'All Time': (MIN_POSSIBLE_DATE, MAX_POSSIBLE_DATE)
}
TABLE_ROW_HEIGHT = 36

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
        # create a column for player, concatenating name & flag
        row['player'] = f"{row['player_name']} {COUNTRIES_MAP.get(row['player_country_code'])}"
        cleaned_data.append(row)
    return cleaned_data


tmp_data = get_data()
data = clean_data(tmp_data)

def unique_sorted_values(key: str) -> list[str]:
    return sorted({row[key] for row in data if row[key]})


FILTER_MAP = {
    'player': unique_sorted_values('player'),
    'player_country_code': unique_sorted_values('player_country_code'),
    'division': unique_sorted_values('division'),
    'governing_body': unique_sorted_values('governing_body'),
    'tourney_name': unique_sorted_values('tourney_name'),
    'state': unique_sorted_values('state'),
    'country': unique_sorted_values('country'),
}

FILTER_MAP['division'].append('All')
FILTER_MAP['governing_body'].append('All')


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
    if grouper == 'player':
        grouper = 'player_photo_url'
    groups = {row[grouper] for row in data if row.get(grouper)}
    values = [row[grouper] for row in data if row.get(grouper)]
    groups_values = [{'group': g, 'count': values.count(g)} for g in groups]
    return sorted(groups_values, key=lambda x: [x['count'], x['group']], reverse=True)


# DISPLAY THE DATA
# Sidebar - Filters
with st.sidebar:
    st.sidebar.header('Filters')

    selected_players = st.sidebar.multiselect('Winner', FILTER_MAP['player'])
    selected_player_country_codes = st.sidebar.multiselect("Winner's Country", FILTER_MAP['player_country_code'])
    selected_divisions = st.sidebar.radio('Division', FILTER_MAP['division'], horizontal=True, index=2)
    selected_governing_bodies = st.sidebar.radio('Governing Body', FILTER_MAP['governing_body'], horizontal=True, index=2)
    selected_tournament_names = st.sidebar.multiselect('Tournament', FILTER_MAP['tourney_name'])

    # Place state & country side-by-side sidebar into two columns
    col1, col2 = st.sidebar.columns(2)

    with col1:
        selected_tournament_states = col1.multiselect('State', FILTER_MAP['state'])

    with col2:
        selected_tournament_countries = col2.multiselect('Country', FILTER_MAP['country'])

    selected_time_period = st.sidebar.selectbox('Time Period', list(TIME_PERIODS.keys()), index=5)

    start_date, end_date = TIME_PERIODS[selected_time_period]

# Sidebar - Groupers
with st.sidebar:
    st.sidebar.header('Grouper')
    groupers = [None, 'player', 'tourney_name', 'state', 'country', 'designation']
    selected_grouper = st.sidebar.selectbox('Grouper', options=groupers, index=0)

# Apply filters to data
filters = {
    "player": selected_players,
    "player_country_code": selected_player_country_codes,
    "tourney_name": selected_tournament_names,
    "division": selected_divisions,
    "governing_body": selected_governing_bodies,
    "state": selected_tournament_states,
    "country": selected_tournament_countries,
    "time_period": (start_date, end_date)
}

filtered_data: list[dict] = filter_data(data, filters)
grouped_data: list[dict] = group_data(filtered_data, selected_grouper)

# Main pane - Leaderboard
with st.container():
    div_str = selected_divisions if selected_divisions != 'All' else ''
    gov_str = selected_governing_bodies if selected_governing_bodies != 'All' else ''
    time_period_str = selected_time_period if selected_time_period != 'All Time' else ''
    player_str = ', '.join([_ for _ in selected_players])
    tourney_str = ', '.join([_ for _ in selected_tournament_names])
    nationality_str = ', '.join([_ for _ in selected_player_country_codes])
    st.header(f'{div_str} {gov_str} {time_period_str} Leaderboard for {player_str} {tourney_str} {nationality_str}')

    leaderboard_column_config = {'group': selected_grouper} if selected_grouper != 'player' \
        else {'group': st.column_config.ImageColumn(width='large')}

    if selected_grouper:
        st.dataframe(grouped_data, column_config=leaderboard_column_config)

# Main pane - Table
with st.container():
    st.header('Events')

    column_order = ['year', 'player', 'tourney_name', 'designation', 'division', 'state', 'country']
    column_config = {'year': st.column_config.NumberColumn('Year', format='%d'),
                     'player': 'Winner', 'tourney_name': 'Tournament', 'designation': 'Designation',
                     'division': 'Division', 'state': 'State', 'country': 'Country'}

    height = (len(filtered_data) * TABLE_ROW_HEIGHT + TABLE_ROW_HEIGHT)

    st.dataframe(filtered_data, height=height, column_order=column_order, column_config=column_config,
                 use_container_width=True)
