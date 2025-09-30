from psycopg2 import connect
import os
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv("PG_DBNAME")
user = os.getenv("PG_USER")
host = os.getenv("PG_HOST")
password = os.getenv("PG_PASSWORD")

def get_connection():
    return connect(dbname=dbname, user=user, host=host, password=password)