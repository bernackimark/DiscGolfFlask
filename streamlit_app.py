from datetime import date, datetime, timedelta
import json
import requests
import streamlit as st

from UI.local_data import local_data

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

@st.cache_data
def get_data() -> list[dict]:
    return local_data
    resp = requests.get(DATA_URL)
    if resp.status_code != 200:
        raise ConnectionError("Could not connect to api")
    return resp.json()


data = get_data()

# Convert serialized end_date to datetime
for entry in data:
    entry["end_date"] = datetime.strptime(entry["end_date"], "%a, %d %b %Y %H:%M:%S %Z").date()

# Function to filter data based on selected criteria
def filter_data(data, filters):
    filtered_data = data
    for key, value in filters.items():
        if value and value != 'All':
            if key == "time_period":
                start_date, end_date = value
                filtered_data = [entry for entry in filtered_data if start_date <= entry["end_date"] <= end_date]
            else:
                filtered_data = [entry for entry in filtered_data if entry[key] in value]
    return sorted(filtered_data, key=lambda x: x['end_date'], reverse=True)

def group_data(data, grouper):
    groups = {row[grouper] for row in data if row.get(grouper)}
    values = [row[grouper] for row in data if row.get(grouper)]
    groups_values = [{'group': g, 'count': values.count(g)} for g in groups]
    return sorted(groups_values, key=lambda x: [x['count'], x['group']], reverse=True)


# Sidebar - Filters
with st.sidebar:
    st.sidebar.header('Filters')

    distinct_player_names = sorted({entry["player_name"] for entry in data})
    selected_player_names = st.sidebar.multiselect('Winner', distinct_player_names)

    distinct_divisions = sorted({entry['division'] for entry in data if entry['division']})
    distinct_divisions.append('All')
    selected_divisions = st.sidebar.radio('Division', distinct_divisions, horizontal=True, index=2)

    distinct_governing_bodies = sorted({entry['governing_body'] for entry in data if entry['governing_body']})
    distinct_governing_bodies.append('All')
    selected_governing_bodies = st.sidebar.radio('Governing Body', distinct_governing_bodies, horizontal=True, index=2)

    distinct_tournament_names = sorted({entry["tourney_name"] for entry in data})
    selected_tournament_names = st.sidebar.multiselect('Tournament', distinct_tournament_names)

    # Place state & country side-by-side sidebar into two columns
    col1, col2 = st.sidebar.columns(2)

    with col1:
        distinct_tournament_states = sorted({entry["state"] for entry in data if entry["state"]})
        selected_tournament_states = col1.multiselect('State', distinct_tournament_states)

    with col2:
        distinct_tournament_countries = sorted({entry["country"] for entry in data})
        selected_tournament_countries = col2.multiselect('Country', distinct_tournament_countries)

    selected_time_period = st.sidebar.selectbox('Time Period', list(TIME_PERIODS.keys()), index=5)

    start_date, end_date = TIME_PERIODS[selected_time_period]

# Sidebar - Groupers
with st.sidebar:
    st.sidebar.header('Grouper')
    groupers = [None, 'player_name', 'tourney_name', 'state', 'country', 'designation']
    selected_grouper = st.sidebar.selectbox('Grouper', options=groupers, index=0)

# Apply filters to data
filters = {
    "player_name": selected_player_names,
    "tourney_name": selected_tournament_names,
    "division": selected_divisions,
    "governing_body": selected_governing_bodies,
    "state": selected_tournament_states,
    "country": selected_tournament_countries,
    "time_period": (start_date, end_date)
}

filtered_data = filter_data(data, filters)
grouped_data = group_data(filtered_data, selected_grouper)

# Main pane - Leaderboard
with st.container():
    div_str = selected_divisions if selected_divisions != 'All' else ''
    gov_str = selected_governing_bodies if selected_governing_bodies != 'All' else ''
    time_period_str = selected_time_period if selected_time_period != 'All Time' else ''
    player_str = ', '.join([_ for _ in selected_player_names])
    tourney_str = ', '.join([_ for _ in selected_tournament_names])
    st.header(f'{div_str} {gov_str} {time_period_str} Leaderboard for {player_str} {tourney_str}')

    leaderboard_column_config = {'group': selected_grouper}

    if selected_grouper:
        st.dataframe(grouped_data, column_config=leaderboard_column_config)

# Main pane - Table
with st.container():
    st.header('Events')

    column_order = ['year', 'player_name', 'tourney_name', 'designation',
                    'division', 'state', 'country']
    column_config = {'year': st.column_config.NumberColumn('Year', format='%d'),
                     'player_name': 'Winner', 'tourney_name': 'Tournament',
                     'designation': 'Designation',
                     'division': 'Division', 'state': 'State', 'country': 'Country'}

    height = (len(filtered_data) * 36 + 36)

    st.dataframe(filtered_data, height=height, column_order=column_order, column_config=column_config)
