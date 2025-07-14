from datetime import date, datetime
import json
import requests

from bs4 import BeautifulSoup
from controller.country import get_countries
from states import states
from utilnacki.soup import list_of_dicts_from_soup_table


EVENT_BASE_URL = 'https://www.pdga.com/tour/event/'


class PDGAEvent:
    PDGA_COMPLETED_EVENT_STATUS = 'Event complete; official ratings processed.'
    EVENT_IDS_W_NO_PDGA_EVENT_ID = {6, 80, 159, 233}

    def __init__(self, pdga_event_id: int):
        self.pdga_event_id = pdga_event_id
        self._scraped_data: dict = self._scrape_event_page()
        self.data: dict = self._clean_division_result_data()

    @property
    def data_as_json(self):
        return json.dumps(self.data)

    @property
    def begin_date(self) -> date:
        _, begin_day_month_str, *_, end_date_str = self.data['dates'].split()
        begin_date_str = begin_day_month_str + '-' + end_date_str[-4:]
        return datetime.strptime(begin_date_str, "%d-%b-%Y").date()

    @property
    def end_date(self) -> date:
        *_, end_date_str = self.data['dates'].split()
        return datetime.strptime(end_date_str, "%d-%b-%Y").date()

    @property
    def status(self) -> str:
        return self.data['status']

    @property
    def location(self) -> tuple[str, str, str]:
        """Returns city, state code | '', country code"""
        location = self.data['location']
        string = location[location.index(': ') + 2:]
        city, *state_full, country_full = string.split(', ')
        country_code = next((code for code, data in get_countries().items() if data['name'] == country_full), None)
        state_full = state_full[0] if state_full else None
        state_code = next((code for code, name in states.items() if name == state_full), '')
        if not country_code:
            raise ValueError(f"Country not found from country name: {country_full}")
        return city, state_code, country_code

    @property
    def city(self) -> str:
        return self.location[0]

    @property
    def state_code(self) -> str | None:
        return self.location[1]

    @property
    def country_code(self) -> str:
        return self.location[2]

    @property
    def is_complete(self) -> bool:
        return self.status == PDGAEvent.PDGA_COMPLETED_EVENT_STATUS

    def get_winner_by_division(self, division: str) -> int:
        return self.data['division_results'][division.upper()][0]['PDGA#']

    def _scrape_event_page(self) -> dict:
        response = requests.get(f'{EVENT_BASE_URL}{self.pdga_event_id}')

        if response.status_code != 200:
            print(f"Failed to fetch from URL f'{EVENT_BASE_URL}{self.pdga_event_id}'. Status code: {response.status_code}")
            exit()

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        divisions: list[str] = [div_tag['id'] for div_tag in soup.find_all(class_="division")]

        # Find all tables on the page
        tables = soup.find_all("table")

        # the first table is the event status
        event_status_html = tables[0]
        event_status_data_row = event_status_html.find_all("tr")[1]

        event_data = {'pdga_event_id': self.pdga_event_id,
                      'status': event_status_data_row.find(class_="status").text,
                      'player_cnt': event_status_data_row.find(class_="players").text,
                      'purse': event_status_data_row.find(class_="purse").text,
                      'dates': soup.find(class_="tournament-date").text,
                      'location': soup.find(class_='tournament-location').text,
                      'name': soup.find("h1").text,
                      'division_results': {}}

        # Iterate over the division results table
        for idx, table in enumerate(tables[1:]):  # the event status table is handled above
            division = divisions[idx]
            event_data['division_results'][division] = list_of_dicts_from_soup_table(table)

        return event_data

    def _clean_division_result_data(self) -> dict[str: list[dict]]:
        """Cleans data from [{'Name': 'Drew Gibson', 'PDGA#': '48346', 'Par': 'E', '': ''} ...] to:
        [{'Name': 'Drew Gibson', 'PDGA#': 48346, 'Par': 0} ...]"""
        for div, table_data in self._scraped_data['division_results'].items():
            if div not in ('MPO', 'FPO'):
                continue
            div_results_clean = []
            for d_dirty in table_data:
                d_clean = {}
                for k, v in d_dirty.items():
                    if k == '':  # ignoring round rating cols whose keys are ''
                        continue
                    if k == 'Par' and v == 'E':
                        value = 0
                    elif k in ('Place', 'PDGA#', 'Rating', 'Par', 'Rd1', 'Rd2', 'Rd3', 'Rd4', 'Finals', 'Total'):
                        try:
                            value = int(v)
                        except ValueError:
                            value = None  # handle DNFs
                    elif k == 'Points':
                        value = float(v) if v else 0
                    elif k == 'Prize':
                        value = float(v.replace("$", "").replace(",", "")) if v else 0
                    else:
                        value = v
                    d_clean[k] = value
                div_results_clean.append(d_clean)
            self._scraped_data['division_results'][div] = div_results_clean

        return self._scraped_data
