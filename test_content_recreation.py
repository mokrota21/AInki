import json
import pandas as pd
from typing import List

def from_content_to_pages(df: pd.DataFrame) -> List[str]:
    pages = []
    current = ""
    df_i = 0
    while df_i < len(df):
        if df.loc[df_i, 'page_idx'] != len(pages):
            pages.append(current)
            current = ""
        current += "\n\n" 
        if df.loc[df_i, 'text_level'] is None:
            current += df.loc[df_i, 'text']
        else:
            current += f"{"#" * df.loc[df_i, 'text_level']}{df.loc[df_i, 'text']}"
        df_i += 1
    return pages

# Load the JSON data
with open('output/1664976801-pages (1)/auto/1664976801-pages (1)_content_list.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

print("DataFrame info:")
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Page indices: {sorted(df['page_idx'].unique())}")
print(f"Text levels: {sorted(df['text_level'].dropna().unique())}")

print("\nFirst few rows:")
print(df.head())

print("\nTesting the function...")
try:
    pages = from_content_to_pages(df)
    print(f"Number of pages created: {len(pages)}")
    
    for i, page in enumerate(pages):
        print(f"\n--- Page {i} (first 200 chars) ---")
        print(repr(page[:200]))
        
        if i >= 2:  # Only show first 3 pages
            break
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
