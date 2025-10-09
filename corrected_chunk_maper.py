from typing import List
import pandas as pd

def from_content_to_pages_corrected(df: pd.DataFrame) -> List[str]:
    """
    Corrected version of from_content_to_pages function.
    Properly recreates text from content list JSON data.
    """
    pages = []
    current = ""
    df_i = 0
    
    while df_i < len(df):
        # Get current row data
        current_page_idx = df.loc[df_i, 'page_idx']
        text_content = df.loc[df_i, 'text']
        text_level = df.loc[df_i, 'text_level']
        
        # Check if we need to start a new page
        if df_i == 0 or current_page_idx != df.loc[df_i - 1, 'page_idx']:
            # Save previous page if it exists
            if current.strip():  # Only add non-empty pages
                pages.append(current)
            # Start new page
            current = ""
        
        # Add content to current page
        if text_content and text_content.strip():  # Only add non-empty text
            current += "\n\n"  # Add spacing between elements
            
            if text_level is not None and text_level > 0:
                # Add markdown headers based on text_level
                current += f"{"#" * text_level} {text_content}"
            else:
                # Regular text
                current += text_content
    
        df_i += 1
    
    # Don't forget the last page
    if current.strip():
        pages.append(current)
    
    return pages

# Test with sample data structure
def test_function():
    # Create sample data that matches the JSON structure
    sample_data = [
        {"type": "text", "text": "Chapter 2", "text_level": 1, "page_idx": 0},
        {"type": "text", "text": "Starting at the beginning: the natural numbers", "text_level": 1, "page_idx": 0},
        {"type": "text", "text": "In this text, we will review...", "text_level": None, "page_idx": 0},
        {"type": "text", "text": "", "text_level": None, "page_idx": 1},  # Empty text
        {"type": "text", "text": "This question is more difficult...", "text_level": None, "page_idx": 1},
        {"type": "text", "text": "2.1 The Peano axioms", "text_level": 1, "page_idx": 2},
        {"type": "text", "text": "We now present one standard way...", "text_level": None, "page_idx": 2},
    ]
    
    df = pd.DataFrame(sample_data)
    pages = from_content_to_pages_corrected(df)
    
    print(f"Number of pages: {len(pages)}")
    for i, page in enumerate(pages):
        print(f"\n--- Page {i} ---")
        print(page[:200] + "..." if len(page) > 200 else page)

if __name__ == "__main__":
    test_function()
