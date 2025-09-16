import psycopg2
from fastapi import UploadFile
from io import BytesIO
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This makes it show in terminal
    ]
)

load_dotenv()
dbname = os.getenv("PG_DBNAME")
user = os.getenv("PG_USER")
host = os.getenv("PG_HOST")
password = os.getenv("PG_PASSWORD")

logger = logging.getLogger(__name__)

try:
    conn = psycopg2.connect(f"dbname='{dbname}' user='{user}' host='{host}' password='{password}'")
except:
    print("I am unable to connect to the database")

def insert_doc(conn: psycopg2.extensions.connection, doc: UploadFile):
    name = doc.filename
    size = doc.size / 1048576
    try:
        with conn.cursor() as cursor:
            insert_sql = """
            INSERT INTO public.docs_metadata (name, size_mb)
            VALUES (%s, %s);
            """
            cursor.execute(insert_sql, (name, size))
            conn.commit()
            logger.info(f"Succesfully inserted document {name} with size {size}")
    except Exception as e:
        logger.error(f"Failed to insert document {name} with size {size}: {e}")

from io import BytesIO
file_bytes = BytesIO(b"Hello World!")
file = UploadFile(
    file=file_bytes,
    filename="test.txt",
    size=len("Hello World!"),
    headers={"content-type": "text/plain"}
)
insert_doc(conn, file)
