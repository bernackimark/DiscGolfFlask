from bs4 import BeautifulSoup as soup
from dataclasses import dataclass, field
import requests

BASE_URL = 'https://www.pdga.com/player/'
PLAYER_IMG_DEFAULT_URL = 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png'

@dataclass
class PlayerPhotoUpdater:
    ids: list[tuple[int, str]]
    updated_records: list[dict] = field(init=False)

    def __post_init__(self):
        self.updated_records = self._get_updated_player_photo_urls()

    def _get_updated_player_photo_urls(self) -> list[dict]:
        """If the player has a new picture, save that new url.  If the player's photo url is None (they were a new add),
        save the default photo constant.  Return a list of dicts with pdga_id & photo_url."""
        new_photos = []
        for pdga_id, photo_url in self.ids:
            online_image_url = self._get_player_image_url(pdga_id)
            if online_image_url and online_image_url != photo_url:
                new_record = {'pdga_id': pdga_id, 'photo_url': online_image_url}
                new_photos.append(new_record)
            elif photo_url is None:
                new_record = {'pdga_id': pdga_id, 'photo_url': PLAYER_IMG_DEFAULT_URL}
                new_photos.append(new_record)
        return new_photos

    @staticmethod
    def _get_player_image_url(pdga_id: int) -> str | None:
        url = BASE_URL + str(pdga_id)
        r = requests.get(url).content
        s = soup(r, 'html.parser')
        if photo_element := s.find(rel="gallery-player_photo"):
            return photo_element.find('img').get('src')
        return None
