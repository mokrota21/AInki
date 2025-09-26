import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
dbname = os.getenv("PG_DBNAME")
user = os.getenv("PG_USER")
host = os.getenv("PG_HOST")
password = os.getenv("PG_PASSWORD")

try:
    conn = psycopg2.connect(f"dbname='{dbname}' user='{user}' host='{host}' password='{password}'")
except:
    print("I am unable to connect to the database")

def insert_user(gmail: str, password: str, username: str):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.users (gmail, password, username)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (gmail, password, username)
        )
        id = cursor.fetchone()[0]
        conn.commit()
    return id

def login(password: str, name_or_gmail: str):
    assert name_or_gmail is not None
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM public.users WHERE password = %s AND (username = %s OR gmail = %s)
            RETURN id
            """,
            (password, name_or_gmail)
        )
        id = cursor.fetchone()[0]
    return id