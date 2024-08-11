from datetime import date, datetime, timedelta
from dotenv import load_dotenv  # pip install python-dotenv
import os

load_dotenv()
DB_CONN_STR = os.getenv('DB_PROD_CONN_STR')
THE_ODDS_API_KEY = os.getenv('THE_ODDS_API_KEY')
NOW = datetime.now()
TODAY = date.today()
