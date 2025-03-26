from db import get_db_session
from models import Season

def get_all_seasons() -> list[dict]:
    with get_db_session() as s:
        events = s.query(Season).all()
        return [e.k_v for e in events]


