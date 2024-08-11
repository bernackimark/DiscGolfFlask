from db import get_db_session
from models import Country

def get_countries() -> dict[str: dict]:
    with get_db_session() as s:
        res: list[Country] = s.query(Country).all()
        return {c.code: {'name': c.name, 'flag_emoji_code': c.flag_emoji_code, 'flag_emoji': c.flag_emoji} for c in res}

