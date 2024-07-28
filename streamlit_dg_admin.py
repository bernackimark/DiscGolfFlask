from datetime import date
import streamlit as st

from countries import COUNTRIES_MAP
from events import EventResults, IncomingEvent
from players import IncomingPlayer, get_last_added_player, get_all_players_as_classes
from tournaments import create_tourney, get_all_tourneys_as_classes

st.set_page_config(page_title='DG Admin', page_icon=':flying_disc:', layout='wide')

all_players: list = sorted({p.full_name for p in get_all_players_as_classes()})
all_tourneys: list = sorted({t.name for t in get_all_tourneys_as_classes()})

def countries_w_flag() -> list[str]:
    return [f'{k} {v}' for k, v in COUNTRIES_MAP.items()]

def country_from_country_w_flag(country_w_flag: str):
    return country_w_flag.split(' ')[0]


col_add_event, col_add_player = st.columns(2)
with col_add_event:
    st.header('Add Event')
    event_results = EventResults()
    last_e = event_results.last_added_event
    st.caption(f"The last event added was {last_e['tourney_name']} from {last_e['event_end_date']}")

    form_add_event = st.form('Add Event')
    event = {
        'governing_body': form_add_event.radio('Governing Body', ['DGPT', 'PDGA'], horizontal=True),
        'designation': form_add_event.radio('Designation', ['Standard', 'Elevated', 'Major'], horizontal=True),
        'start_date': form_add_event.date_input('Start Date', value=None),
        'end_date': form_add_event.date_input('End Date', value=None),
        'winner_name': form_add_event.selectbox('Winner', all_players, index=None),
        'tourney_name': form_add_event.selectbox('Tournament', all_tourneys, index=None)
    }
    form_add_event_submit = form_add_event.form_submit_button('Add Event')
    if form_add_event_submit:
        for k, v in event.items():
            if not v:
                st.error(f'Please fill out {k}')
                exit()
        event_obj = IncomingEvent(**event)
        if event_obj:
            event_obj.create_event()

with col_add_player:
    st.header('Add Player')
    last_add = get_last_added_player()
    st.caption(f"The last player added is {last_add['first_name']} {last_add['last_name']} on {last_add['created_ts'].date()}")
    form_add_player = st.form('Add Player')
    player = {'pdga_id': form_add_player.number_input('PDGA #', min_value=1, max_value=1000000, format='%d'),
              'first_name': form_add_player.text_input('First Name'),
              'last_name': form_add_player.text_input('Last Name'),
              'division': form_add_player.radio('Dvision', ['MPO', 'FPO'], horizontal=True),
              'photo_url': form_add_player.text_input('Photo URL (presently unsupported)', disabled=True),
              'country_code': form_add_player.text_input('Country Code (two-digit)', max_chars=2)}
    form_add_player_submit = form_add_player.form_submit_button('Add Player')
    if form_add_player_submit:
        for k, v in player.items():
            if k != 'photo_url' and not v:
                st.error(f'Please fill out {k}')
                exit()
        player_obj = IncomingPlayer(**player)
        if player_obj:
            player_obj.create_player()
            st.rerun()

with col_add_player:
    st.header('Add Tournament')
    form_add_tourney = st.form('Add Tournament')
    tourney = {'name': form_add_tourney.text_input('Name'),
               'city': form_add_tourney.text_input('City'),
               'state': form_add_tourney.text_input('State (US)', max_chars=2),
               'country': form_add_tourney.selectbox('Country', countries_w_flag())}
    form_add_tourney_submit = form_add_tourney.form_submit_button('Add Tournament')

    if tourney['country']:
        tourney['country'] = country_from_country_w_flag(tourney['country'])

    if form_add_tourney_submit:
        for k, v in tourney.items():
            if not v:
                if k == 'state' and tourney.get('country') != 'US':
                    pass
                else:
                    st.error(f'Please fill out {k}')
                    exit()

        create_tourney(tourney)
        st.rerun()
