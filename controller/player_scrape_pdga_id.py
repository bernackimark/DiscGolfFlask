import requests

STATUS = 'Current'
CLASS = 'P'  # Pro
ID_START = '<td class="views-field views-field-PDGANum pdga-number" >'
ID_END = '<'
COUNTRY_START = '<td class="views-field views-field-Country country" >'
COUNTRY_END = '<'

def scrape_id_and_country(first_name: str, last_name: str,
                          status: str = STATUS, class_: str = CLASS) -> tuple[int, str] | None:
    """Required params: first_name & last_last_name; option status (current/expired) & class (P/A).
    If there are multiple current pro's w the same name, only the first will be returned.
    Currently, PDGA.com sorts by PDGA# ascending.
    If found, a pdga_id (int) & the player country (str) is returned as a tuple.
    Example: (73986, 'Estonia')"""
    url = f'https://www.pdga.com/players'
    html = requests.get(url, params={'FirstName': first_name, 'LastName': last_name,
                                     'Status': status, 'Class': class_}).text
    try:
        id_start_pos = html.index(ID_START) + len(ID_START)
        id_char_count = html[id_start_pos:].index(ID_END)
        pdga_id = int(html[id_start_pos:id_start_pos + id_char_count].strip())
        country_start_pos = html.index(COUNTRY_START) + len(COUNTRY_START)
        country_char_count = html[country_start_pos:].index(COUNTRY_END)
        country = html[country_start_pos:country_start_pos + country_char_count].strip()
        return pdga_id, country if pdga_id > 1 else None  # is the search is blank, the first record is PDGA# 1
    except ValueError as e:
        print(e)
