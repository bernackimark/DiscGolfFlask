from collections import Counter, defaultdict
from datetime import date
import time

import altair as alt
from controller.event import EventResults
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from utilnacki.dates import TIME_PERIODS

# DATA_URL = 'https://disc-golf.onrender.com/api/results_flat'

TABLE_ROW_HEIGHT = 36

st.set_page_config(page_title='Bernacki DiscGolf', page_icon=':flying_disc:', layout='wide')
st.session_state['filters'] = {}
st.session_state['groupers'] = {}


class StreamlitData:
    def __init__(self, records: list[dict], filters: list[str], groupers: dict[str: tuple[str, ...]]):
        self._dirty_data = records
        self.data: list[dict] = self.clean_data()
        self.filters = filters
        self.groupers = groupers
        self.filter_dropdowns: dict = self.populate_filter_dropdowns()
        self.filtered_data: list[dict] = self.data.copy()
        self.grouped_data: list[dict] | None = None

    @property
    def players(self) -> list:
        return sorted({p['player_w_flag'] for p in self.filtered_data})

    @property
    def years(self) -> list:
        return sorted({r['event_year'] for r in self.filtered_data if r.get('event_year')})

    def clean_data(self) -> list[dict]:
        designation_map = {'DGPT +': 'Elevated', 'Elite +': 'Elevated',
                           'Elite': 'Standard', 'DGPT Undesignated': 'Standard', 'Silver': 'Standard'}
        cleaned_data = []
        for row in self._dirty_data:
            # create/clean/map some columns
            row['player_w_flag'] = f"{row['player_full_name']}  {row['country_flag_emoji']}"
            row['country_w_flag'] = f"{row['country_name']}  {row['country_flag_emoji']}"
            row['event_state'] = '' if not row['event_state'] else row['event_state']
            # group the designations
            row['event_designation_map'] = designation_map.setdefault(row['event_designation'],
                                                                      row['event_designation'])
            cleaned_data.append(row)
        return cleaned_data

    def populate_filter_dropdowns(self) -> dict[str: list]:
        filter_dropdowns = {f: set() for f in self.filters}
        for r in self.data:
            for k, v in r.items():
                if k in self.filters:
                    filter_dropdowns[k].add(v)
        return {k: sorted(v, key=lambda x: (x is None, x)) for k, v in filter_dropdowns.items()}

    def filter_data(self, filters: dict, sort_key: str = None, time_period_col: str = None) -> None:
        """Accepts a dictionary whose keys are 'columns' and whose list of values are the 'column' data.
        Data that meets the provided filters is stored in self.filtered_data, ordered by date descending.
        'Special keys': If the filter's value is 'All', that filter is ignored.
        If the key is 'time_period', it expects a tuple of two dates, saving dates that are between (inclusive).
        This is done on the parameter 'time_period_col'. """
        if not filters:
            self.filtered_data = self.data
        filtered = self.data.copy()
        for key, value in filters.items():
            if value and value != 'All':
                if key == 'time_period':
                    filtered = [entry for entry in filtered if value[0] <= entry[time_period_col] <= value[1]]
                else:
                    filtered = [entry for entry in filtered if entry[key] in value]
        self.filtered_data = sorted(filtered, key=lambda x: x[sort_key], reverse=True) if sort_key else filtered

    def group_data_by_player_year(self) -> None:
        """Returns list of dicts, such as:
        {'player_w_flag': 'Kristin Tattar  :flag-ee', 'event_year': 2021, 'season_wins: 3, 'cumulative_wins': 4}"""
        grouped = defaultdict(lambda: {'player_w_flag': None, 'event_year': None, 'season_wins': 0, 'cumulative_wins': 0})
        cumulative_totals = defaultdict(int)  # Cumulative wins by player

        # For each player and year combination, process and update wins
        for year in self.years:
            for player in self.players:
                key = (player, year)

                # Filter out records for this player-year if present
                player_records = [r for r in self.filtered_data if r['player_w_flag'] == player and r['event_year'] == year]

                # If there are records for this player-year, count the wins
                wins = len(player_records)
                if wins > 0:
                    cumulative_totals[player] += wins  # Update cumulative wins

                # Update grouped data for the player-year with wins and cumulative wins
                grouped[key]['player_w_flag'] = player
                grouped[key]['event_year'] = year
                grouped[key]['season_wins'] = wins
                grouped[key]['cumulative_wins'] = cumulative_totals[player]

        # Convert the grouped data back to a list
        self.grouped_data = list(grouped.values())

    def group_and_count(self, grouper_key: str, desired_count_key: str) -> list[dict]:
        """Accepts a column on which to group; returns a list of dicts whose count has a key of the desired count key"""
        values_to_group = [r[grouper_key] for r in self.filtered_data]
        counter = Counter(values_to_group)
        return [{grouper_key: group, desired_count_key: count} for group, count in counter.items()]

    @staticmethod
    def rank_data(unranked_data: list[dict], value_key: str) -> list[dict] | None:
        """Appends a key called 'rank' with a value of the rank; it handles ties"""
        if not unranked_data:
            return None
        sorted_data = sorted(unranked_data, key=lambda x: x[value_key], reverse=True)
        sorted_data[0]['rank'] = 1
        for i, row in enumerate(sorted_data[1:], start=2):
            row['rank'] = i if row[value_key] != sorted_data[i-2][value_key] else sorted_data[i-2]['rank']
        return sorted_data

@st.cache_data
def get_data() -> list[dict]:
    results = EventResults()
    return results.results_flat


data = StreamlitData(get_data()
                     , filters=['player_w_flag', 'country_w_flag', 'player_division',
                                'event_designation_map', 'tourney_name', 'event_state', 'event_country_name']
                     , groupers={'event_grouper': ('player_w_flag', )})  # focused on just grouping by player wins

# FILTER & GROUP THE DATA
# Sidebar
with st.sidebar:
    st.sidebar.header('Grouper')
    st.session_state['groupers']['event_grouper'] = st.sidebar.selectbox('Grouper', options=data.groupers['event_grouper'], index=0)

with st.sidebar:
    st.sidebar.header('Filters')
    st.session_state['filters']['player_w_flag'] = st.sidebar.multiselect('Winner', data.filter_dropdowns['player_w_flag'])
    st.session_state['filters']['country_w_flag'] = st.sidebar.multiselect("Winner's Country", data.filter_dropdowns['country_w_flag'])
    data.filter_dropdowns['player_division'].append('All')
    st.session_state['filters']['player_division'] = st.sidebar.radio('Division', data.filter_dropdowns['player_division'], horizontal=True, index=2)
    data.filter_dropdowns['event_designation_map'].append('All')
    st.session_state['filters']['event_designation_map'] = st.sidebar.radio('Designation', data.filter_dropdowns['event_designation_map'], horizontal=True, index=3)
    st.session_state['filters']['tourney_name'] = st.sidebar.multiselect('Tournament', data.filter_dropdowns['tourney_name'])

    # Place state & country side-by-side sidebar into two columns
    col1, col2 = st.sidebar.columns(2)
    st.session_state['filters']['event_state'] = col1.multiselect('State', data.filter_dropdowns['event_state'])
    st.session_state['filters']['event_country_name'] = col2.multiselect('Country', data.filter_dropdowns['event_country_name'])

    selected_time_period = st.sidebar.selectbox('Time Period', list(TIME_PERIODS.keys()), index=5)
    st.session_state['filters']['time_period']: tuple[date, date] = TIME_PERIODS[selected_time_period]


data.filter_data(st.session_state['filters'], sort_key='event_end_date', time_period_col='event_end_date')
data.group_data_by_player_year()
players_and_wins: list[dict] = data.group_and_count('player_w_flag', 'wins')
ranked_players = data.rank_data(players_and_wins, 'wins')
top_7_names = [d['player_w_flag'] for d in ranked_players if d['rank'] <= 7]
df_ranked = pd.DataFrame([r for r in data.grouped_data if r['player_w_flag'] in top_7_names])


# DISPLAY THE DATA
# Player Wins Line Chart
with st.container():
    st.header('Top Players (DGPT Era)')
    st.caption('Max seven players (plus ties).  Group by player to see the chart.')
    each_or_cumulative = st.radio('', ['Wins By Year', 'Cumulative Career Wins (line)',
                                       'Cumulative Career Wins (animated bar)'], horizontal=True)
    if each_or_cumulative in ('Wins By Year', 'Cumulative Career Wins (line)'):
        # Altair Line Chart
        y_key = 'season_wins' if each_or_cumulative == 'Wins By Year' else 'cumulative_wins'
        chart = alt.Chart(df_ranked).mark_line().encode(x='event_year:O', y=f'{y_key}:Q', color='player_w_flag:N')
        st.altair_chart(chart, use_container_width=True)
    else:
        # Plotly Animation
        placeholder = st.empty()
        with placeholder:
            st.header('Animation on Cumulative Wins')

            for year in data.years:
                fig, ax = plt.subplots(figsize=(8, 3))
                ax.clear()

                # Streamlit's default dark theme
                fig.patch.set_facecolor('#0E1117')
                ax.set_facecolor('#0E1117')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')

                year_data = df_ranked[df_ranked['event_year'] == year].sort_values('cumulative_wins', ascending=False)
                x, y = year_data['player_w_flag'], year_data['cumulative_wins']
                ax.barh(x, y, color='#FF4B4B')  # Streamlit's primary color
                for index, value in enumerate(y):
                    plt.text(value - 1, index, str(value), color='white', va='center', ha='right')

                ax.set_title(f'Most Career Wins in the DGPT Era: {year}', fontsize=16)
                ax.set_xlim(0, df_ranked['cumulative_wins'].max() + 5)
                ax.invert_yaxis()  # Highest rank at the top

                # Update the placeholder with the new plot
                with placeholder.container():
                    plt.tight_layout()
                    st.pyplot(fig)

                plt.close(fig)
                time.sleep(0.05)


col_l, col_c, col_r = st.columns(3)
# Leaderboard Table
with col_l.container():
    st.header('Most Wins')
    st.caption('DGPT Era')
    lb_col_config = {'rank': 'Rank', 'player_w_flag': 'Winner', 'wins': 'Wins'}
    column_order = list(lb_col_config.keys())
    table_data = data.rank_data(data.group_and_count('player_w_flag', 'wins'), 'wins')
    st.dataframe(table_data, column_order=column_order, column_config=lb_col_config, hide_index=True)


# Best Avg Finish All-time
with col_c.container():
    st.header('Lowest Avg Finish')
    st.caption('Min 10 events; players w no DGPT Era win shown by PDGA#')
    player_finishes = defaultdict(list)
    # {73986: [2, 1, 3, 5, 1], ...}
    for e in data.filtered_data:
        if e['event_results']:
            for player_result in e['event_results']:
                player_finishes[player_result['PDGA#']].append(player_result['Place'])

    # {73986: 2.4, ...}
    player_avg_finish = {}
    for pdga_id, finishes in player_finishes.items():
        if len(finishes) >= 10:
            player_avg_finish[pdga_id] = round(sum(finishes) / len(finishes), 1)

    top_x = 10
    p_avg_finish_top_10: list[tuple[int, float]] = sorted(player_avg_finish.items(), key=lambda item: item[1])[:top_x]

    final_avg_finish = []
    for pdga_id, avg_finish in p_avg_finish_top_10:
        player_w_flag = next((e['player_w_flag'] for e in data.filtered_data if e['event_winner_id'] == pdga_id), None)
        final_avg_finish.append({'player_w_flag': player_w_flag or f'PDGA#: {pdga_id}', 'avg_finish': avg_finish})

    st.dataframe(final_avg_finish, column_config={'player_w_flag': 'Winner', 'avg_finish': 'Avg Place'})

# All Results Table
with st.expander('Event Results'):
    column_config = {'event_year': st.column_config.NumberColumn('Year', format='%d'),
                     'player_w_flag': 'Winner', 'tourney_name': 'Tournament', 'event_designation_map': 'Designation',
                     'player_division': 'Division', 'event_state': 'State', 'event_country_name': 'Country'}
    column_order = list(column_config.keys())
    height = (len(data.filtered_data) * TABLE_ROW_HEIGHT + TABLE_ROW_HEIGHT)
    st.dataframe(data.filtered_data, height=height, column_order=column_order, column_config=column_config,
                 hide_index=True, use_container_width=True)
