from controller.country import get_countries
from controller.event import NewEvent, get_last_added_event
from controller.player import NewPlayer, get_last_added_player, get_all_players
from controller.tournament import create_tourney, get_all_tourneys
import streamlit as st

st.set_page_config(page_title='DG Admin', page_icon=':flying_disc:', layout='wide')

@st.cache_data
def get_all_countries() -> dict:
    return get_countries()


all_countries: dict = get_all_countries()
all_players: list = sorted({p['full_name'] for p in get_all_players()})
all_tourneys: list = sorted({t['name'] for t in get_all_tourneys()})


def countries_w_flag() -> list[str]:
    return [f'{code} {data["flag_emoji"]}' for code, data in all_countries.items()]

def country_from_country_w_flag(country_w_flag: str):
    return country_w_flag.split(' ')[0]


col_add_event, col_add_player = st.columns(2)
with col_add_event:
    st.header('Add Event')
    tourney_name, end_date = get_last_added_event()
    st.caption(f"The last event added was {tourney_name} from {end_date}")

    form_add_event = st.form('Add Event')
    event = {
        'designation': form_add_event.radio('Designation', ['Standard', 'Elevated', 'Major'], horizontal=True),
        'start_date': form_add_event.date_input('Start Date', value=None),
        'end_date': form_add_event.date_input('End Date', value=None),
        'tourney_name': form_add_event.selectbox('Tournament', all_tourneys, index=None),
        'city': form_add_event.text_input('City'),
        'state': form_add_event.text_input('State', max_chars=2),
        'country_code': form_add_event.selectbox('Country', countries_w_flag(), index=232),  # US
        'winner_name': form_add_event.selectbox('Winner', all_players, index=None)
    }
    form_add_event_submit = form_add_event.form_submit_button('Add Event')
    if form_add_event_submit:
        event['country_code'] = country_from_country_w_flag(event['country_code'])
        event['governing_body'] = 'PDGA' if event['designation'] == 'Major' else 'DGPT'

        for k, v in event.items():
            if not v and not (event['country_code'] != 'US' and k == 'state'):
                st.error(f'Please fill out {k}')
                exit()

        event_obj = NewEvent(**event)
        if event_obj:
            event_obj.create_event()

with col_add_player:
    st.header('Add Player')
    last_add = get_last_added_player()
    st.caption(f"The last player added was {last_add['full_name']} on {last_add['created_ts'].date()}")
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

        NewPlayer(**player)
        st.rerun()

with col_add_player:
    st.header('Add Tournament')
    form_add_tourney = st.form('Add Tournament')
    tourney = {'name': form_add_tourney.text_input('Name')}
    form_add_tourney_submit = form_add_tourney.form_submit_button('Add Tournament')

    if form_add_tourney_submit:
        for k, v in tourney.items():
            if not v:
                st.error(f'Please fill out {k}')
                exit()

        create_tourney(tourney)
        st.rerun()
