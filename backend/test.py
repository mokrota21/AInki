from src import map_to_pages_doc_intelligence

with open("doc_intelligence.md", "r", encoding="utf-8") as f:
    text = f.read()

chunks = []
for i in range(0, len(text), 1000):
    chunk = text[i:i+1000]
    chunks.append(chunk)

chunks_mapping = map_to_pages_doc_intelligence(0, chunks)

import json

save_info = [{"chunk": chunks[i], "page": chunks_mapping[i]} for i in range(len(chunks))]

with open("chunks_mapping.json", "w", encoding="utf-8") as f:
    json.dump(save_info, f, indent=4)