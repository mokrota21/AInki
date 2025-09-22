import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
dbname = os.getenv("PG_DBNAME")
user = os.getenv("PG_USER")
host = os.getenv("PG_HOST")
password = os.getenv("PG_PASSWORD")

try:
    conn = psycopg2.connect(f"dbname='{dbname}' user='{user}' host='{host}' password='{password}'")
except:
    print("I am unable to connect to the database")

def insert_chunk(chunk: str, doc_id: int, order_idx: int):
    char_count = len(chunk)
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.chunks (chunk, doc_id, order_idx, char_count)
            VALUES (%s, %s, %s, %s)
            """
            (chunk, doc_id, order_idx, char_count)
        )
        conn.commit()
