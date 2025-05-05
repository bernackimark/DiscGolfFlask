from controller.country import get_countries
from controller.event import get_completed_unloaded_events, get_last_added_event, write_event_to_db
from controller.player import NewPlayer, get_last_added_player, get_all_players
from controller.player_scrape_pdga_id import scrape_id_and_country
from controller.tournament import create_tourney, get_all_tourneys
import streamlit as st

st.set_page_config(page_title='DG Admin', page_icon=':flying_disc:', layout='wide')

@st.cache_data
def get_all_countries() -> dict:
    return get_countries()


# all_countries: dict = get_all_countries()
# all_players: list = sorted({p['full_name'] for p in get_all_players()})
# all_tourneys: list = sorted({t['name'] for t in get_all_tourneys()})


# def countries_w_flag() -> list[str]:
#     return [f'{code} {data["flag_emoji"]}' for code, data in all_countries.items()]
#
# def country_from_country_w_flag(country_w_flag: str):
#     return country_w_flag.split(' ')[0]

# # This is a way to manually add a completed event; disabling this for now in favor of a more automated process
# # May want to retain this in case I want to load an unsanctioned event
# with col_add_event:
#     st.header('Add Event')
#     tourney_name, end_date = get_last_added_event()
#     st.caption(f"The last event added was {tourney_name} from {end_date}")
#
#     form_add_event = st.form('Add Event')
#     event = {
#         'designation': form_add_event.radio('Designation', ['Standard', 'Elevated', 'Major'], horizontal=True),
#         'start_date': form_add_event.date_input('Start Date', value=None),
#         'end_date': form_add_event.date_input('End Date', value=None),
#         'tourney_name': form_add_event.selectbox('Tournament', all_tourneys, index=None),
#         'city': form_add_event.text_input('City'),
#         'state': form_add_event.text_input('State', max_chars=2),
#         'country_code': form_add_event.selectbox('Country', countries_w_flag(), index=232),  # US
#         'pdga_event_id': form_add_event.number_input('PDGA Event ID', min_value=1, max_value=9999999),
#         'winner_name': form_add_event.selectbox('Winner', all_players, index=None)
#     }
#     form_add_event_submit = form_add_event.form_submit_button('Add Event')
#     if form_add_event_submit:
#         event['country_code'] = country_from_country_w_flag(event['country_code'])
#         event['governing_body'] = 'PDGA' if event['designation'] == 'Major' else 'DGPT'
#
#         for k, v in event.items():
#             if not v and not (event['country_code'] != 'US' and k == 'state'):
#                 st.error(f'Please fill out {k}')
#                 exit()
#
#         event_obj = NewEvent(**event)
#         if event_obj:
#             event_obj.create_event()


col_l, col_r = st.columns(2)
with col_l:
    st.header('Load Completed Events')

    tourney_name, end_date = get_last_added_event()
    st.caption(f"The last event added was {tourney_name} from {end_date}")

    if st.button('Load Completed Events'):
        cues: list[dict] = get_completed_unloaded_events()
        if not cues:
            st.info("No completed events to load")
        else:
            for cue in cues:
                try:
                    write_event_to_db(**cue)
                    st.success(f"Added PDGA Event # {cue['pdga_event_id']} for {cue['div']}")
                except ValueError as e:
                    st.error(e)


with col_l.container():
    st.header('Manual Load Completed Event')
    form_manual_event_load = st.form('Manual Load Completed Event')
    left, right = form_manual_event_load.columns(2)
    pdga_event_id = left.number_input('PDGA Event #', min_value=1, placeholder=None)
    designation = right.selectbox('Designation', ['Standard', 'Elevated', 'Major'], index=None)
    tourney_id = left.number_input('Tourney ID', min_value=1, placeholder=None)
    div = right.selectbox('Division', ['MPO', 'FPO'])

    if form_manual_event_load.form_submit_button('Load'):
        if not pdga_event_id > 1 or not designation or not tourney_id > 1 or not div:
            st.error('Please enter all values')
            exit()
        write_event_to_db(pdga_event_id, designation, tourney_id, div)

with col_r.container():
    st.header('Lookup PDGA #')
    form_player_lookup = st.form('Lookup PDGA#')
    co_first, co_last = form_player_lookup.columns(2)
    first = co_first.text_input('First Name')
    last = co_last.text_input('Last Name')
    co_btn, co_pdga_id, co_country = form_player_lookup.columns([2, 1, 1])
    btn_search = co_btn.form_submit_button('Search')
    pdga_id, country = None, None
    if btn_search:
        if scrape_id_and_country(first, last):
            pdga_id, country = scrape_id_and_country(first, last)
            co_pdga_id.subheader(pdga_id)
            co_country.subheader(country)
        else:
            co_country.subheader('No player found')

with col_r.container():
    st.header('Add Player')
    last_add = get_last_added_player()
    st.caption(f"The last player added was {last_add['full_name']} on {last_add['created_ts'].date()}")

    form_add_player = st.form('Add Player')
    co1, co2, co3 = form_add_player.columns([2, 2, 2])
    player = {'pdga_id': co1.number_input('PDGA #', min_value=1, max_value=1000000, format='%d', value=pdga_id),
              'first_name': co2.text_input('First Name', value=first if first else None),
              'last_name': co3.text_input('Last Name', value=last if last else None),
              'division': form_add_player.radio('Dvision', ['MPO', 'FPO'], horizontal=True),
              'photo_url': form_add_player.text_input('Photo URL (presently unsupported)', disabled=True),
              'country_code': form_add_player.text_input('Country Code (two-digit)', max_chars=2)}

    form_add_player_submit = form_add_player.form_submit_button('Add Player')
    if form_add_player_submit:
        for k, v in player.items():
            if k != 'photo_url' and not v:
                st.error(f'Please fill out {k}')
                exit()
            if k == 'pdga_id' and v <= 1:
                st.error(f'Please enter a valid PDGA #')
                exit()
        NewPlayer(**player)
        st.rerun()


with col_r.container():
    st.header('Add Tournament')
    form_add_tourney = st.form('Add Tournament')
    tourney_name = form_add_tourney.text_input('Name')

    tourney_names_and_ids = sorted([f"{t['name']} ({t['id']})" for t in get_all_tourneys()])
    expires_str = form_add_tourney.selectbox('Succeeds', tourney_names_and_ids, index=None)
    if expires_str:
        expires_name = expires_str[:expires_str.rfind(" (")]
        expires_id = int(expires_str[expires_str.rfind("(") + 1:].rstrip(")"))

    form_add_tourney_submit = form_add_tourney.form_submit_button('Add Tournament')

    if form_add_tourney_submit:
        if len(tourney_name) < 2:
            st.error(f'Please enter a name')
            exit()

        create_tourney(tourney_name, expires_name, expires_id) if expires_str else create_tourney(tourney_name)
        st.rerun()
