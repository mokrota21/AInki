from src import *
import os

reader = DocIntelligenceReader()
with open(r"C:\torrent\Scherm_afbeelding_2025-10-06_om_13.55.08.pdf", "rb") as f:
    file_bytes = f.read()
    file_type = "pdf"
    md = reader.get_md(file_bytes, file_type)

import json

with open("pages.json", "w", encoding="utf-8") as f:
    json.dump(md, f, indent=4)
