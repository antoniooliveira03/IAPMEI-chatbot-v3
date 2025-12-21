# Libraries
from pathlib import Path
import fitz
from trafilatura import extract
import re

# Directories
raw_dir = Path("data/01_raw")
clean_dir = Path("data/02_clean")
clean_dir.mkdir(parents=True, exist_ok=True)


# Load Documents
def extract_text_from_html(file_path: Path) -> str:
    """Extract main readable text from an HTML file using trafilatura."""
    try:
        html = file_path.read_text(encoding="utf-8", errors="ignore")
        text = extract(html, include_comments=False, include_tables=False)
        return text.strip() if text else ""
    except Exception as e:
        print(f"[HTML ERROR] {file_path.name}: {e}")
        return ""
    
    
def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text")

        #  Cleaning steps

        # Remove control characters
        text = re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', text)
        # Merge lines that are not paragraph breaks
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        # Collapse multiple blank lines into a single paragraph break
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        # Collapse multiple spaces/tabs into one
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace sequences of 4 or more dots with a paragraph break
        text = re.sub(r'\.{4,}', '\n', text)
        # Strip leading/trailing whitespace
        text = text.strip()

        return text
    
    except Exception as e:
        print(f"[PDF ERROR] {file_path.name}: {e}")
        return ""
    

def extract_text_from_txt(file_path: Path) -> str:
    """Load and lightly clean text from a TXT file."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        # Basic cleaning (similar to PDF but lighter)
        text = re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        return text.strip()

    except Exception as e:
        print(f"[TXT ERROR] {file_path.name}: {e}")
        return ""


# Run
for file_path in raw_dir.iterdir():
    suffix = file_path.suffix.lower()

    if suffix in [".html", ".htm"]:
        text = extract_text_from_html(file_path)
    elif suffix == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif suffix == ".txt":
        text = extract_text_from_txt(file_path)
    else:
        print(f"[UNSUPPORTED FILE TYPE] {file_path.name}")
        continue
    
    # Save cleaned text
    output_file = clean_dir / (file_path.stem + ".txt")
    output_file.write_text(text, encoding="utf-8")

    print(f"[OK] Saved cleaned text → {output_file.name}")