from datetime import date, datetime, timedelta
from dotenv import load_dotenv  # pip install python-dotenv
import os

load_dotenv()
DB_CONN_STR = os.getenv('DB_PROD_CONN_STR')
CONN_STR_UNPACKED = os.getenv('CONN_STR')
NOW = datetime.now()
TODAY = date.today()
