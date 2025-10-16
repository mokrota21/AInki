from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from dotenv import load_dotenv
import os

load_dotenv()

endpoint = os.getenv("DOC_ENDPOINT")
key = os.getenv("DOC_KEY")

client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))

with open(r"C:\Users\mokrota\Documents\GitHub\AInki\backend\uploads\1664976801-pages (1).pdf", "rb") as f:
     poller = client.begin_analyze_document("prebuilt-layout", f, output_content_format="markdown")

result = poller.result()

print(result.content)
with open("doc_intelligence.md", "w", encoding="utf-8") as f:
    f.write(result.content)
