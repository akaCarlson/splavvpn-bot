import os
import psycopg

from pathlib import Path
from dotenv import load_dotenv
from psycopg.rows import dict_row

def get_conn():
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

    dsn = os.environ["BOT_DB_DSN"]
    return psycopg.connect(dsn, row_factory=dict_row)
