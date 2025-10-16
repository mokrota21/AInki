from .pg_connection import get_connection
from .paths import make_content_path
from typing import List
import json, re
import pandas as pd
from .chunker import DefaultChunker

def chunk_maper(doc_id: int, chunk_id_s: int, chunk_id_e: int) -> str:
    conn = get_connection()
    content = ""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT content FROM public.chunks WHERE doc_id = %s AND order_idx BETWEEN %s AND %s
            """,
            (doc_id, chunk_id_s, chunk_id_e)
        )
        for row in cursor.fetchall():
            content += row[0]
    return content

def from_content_to_pages(df: pd.DataFrame) -> List[str]:
    pages = []
    current = ""
    df_i = 0
    while df_i < len(df):
        if df.loc[df_i, 'page_idx'] != len(pages):
            pages.append(current)
            current = ""
        current += "\n\n"  if df.loc[df_i, 'text'] != "" else ""
        if pd.isna(df.loc[df_i, 'text_level']):
            current += df.loc[df_i, 'text'].strip()
        else:
            current += f"{"#" * int(df.loc[df_i, 'text_level'])} {df.loc[df_i, 'text'].strip()}"
        df_i += 1
    pages.append(current)
    return pages

# TODO: Make it for each reader
def map_to_pages_mineru(doc_id: int, chunks: List[str]) -> List[int]:
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT name, folder FROM public.docs_metadata WHERE id = %s
            """,
            (doc_id,)
        )
        try:
            name, folder = cursor.fetchone()
        except:
            raise ValueError(f"No document with id {doc_id} found")
    path = make_content_path(name, folder)
    df = pd.read_json(path)
    pages = from_content_to_pages(df)
    with open('page.json', 'w') as f:
        json.dump(pages, f, indent=4)
    all_content = "".join(pages)
    with open('content.txt', 'w', encoding='utf-8') as f:
        f.write(all_content)
    page_mapping = []
    offset = 0
    for page in pages:
        page_mapping.append(offset + len(page))
        offset += len(page)
    chunk_mapping = []
    offset = 0
    current_page = 0
    for chunk in chunks:
        if all_content.find(chunk) == -1:
            raise ValueError(f"Chunk {chunk} not found in document {doc_id}")
        offset += len(chunk)
        if offset > page_mapping[current_page]:
            current_page += 1
        chunk_mapping.append(current_page)
    return chunk_mapping

def map_to_pages_doc_intelligence(doc_id: int, chunks: List[str]) -> List[int]:
    full_text = "".join(chunks)
    page_break_patterns = (
        r'<!--\s*PageBreak\s*-->'                      # PageBreak (required)
        r'(?:\s*<!--\s*PageNumber="\d+"\s*-->)?'       # Optional PageNumber
        r'(?:\s*<!--\s*PageHeader="[^"]+"\s*-->)?'     # Optional PageHeader
    )

    # Split BEFORE each pattern, keeping the pattern with the following page
    pages = re.split(f'(?={page_break_patterns})', full_text)
    chunk_mapping = []
    current_page_left = len(pages[0])
    page_idx = 0
    chunk_idx = 0
    current_chunk_left = len(chunks[0])
    while chunk_idx < len(chunks):
        if current_chunk_left > current_page_left:
            page_idx += 1
            current_chunk_left -= current_page_left
            current_page_left = len(pages[page_idx])
        else:
            chunk_idx += 1
            chunk_mapping.append(page_idx)
            current_page_left -= current_chunk_left
            current_chunk_left = len(chunks[chunk_idx]) if chunk_idx < len(chunks) else 0
    return chunk_mapping


fun_map = {
    "MineruReader": map_to_pages_mineru,
    "DocIntelligence": map_to_pages_doc_intelligence,
}

def map_to_pages(doc_id: int, chunks: List[str], reader: str):
    return fun_map[reader](doc_id, chunks)

def chunk_to_page(chunk_idx: int, doc_id: int) -> int:
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT page_idx FROM public.chunks WHERE doc_id = %s AND order_idx = %s
            """,
            (doc_id, chunk_idx)
        )
        return cursor.fetchone()[0]

def chunks_in_page(page_idx: int, doc_id: int) -> List[int]:
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM public.chunks WHERE doc_id = %s AND page_idx = %s
            """,
            (doc_id, page_idx)
        )
        return [row[0] for row in cursor.fetchall()]