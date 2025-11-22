# Libraries
from pathlib import Path
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

# Directories
clean_dir = Path("data/02_clean")
chunk_dir = Path("data/03_chunked")
chunk_dir.mkdir(parents=True, exist_ok=True)

# Chunk
def chunk(clean_dir: Path, chunk_dir: Path, chunk_size, chunk_overlap):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda x: len(x.split())
    )

    text = file_path.read_text(encoding="utf-8")
    chunks = splitter.split_text(text)

    json_chunks = [
        {"source_file": file_path.name, 
         "chunk_id": i+1, 
         "text": chunk} for i, chunk in enumerate(chunks)
    ]

    output_file = chunk_dir / f"{file_path.stem}_chunks.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_chunks, f, ensure_ascii=False, indent=2)

    print(f"[OK] {file_path.name}: {len(chunks)} chunks saved → {output_file.name}")



# Run
for file_path in clean_dir.iterdir():
    chunk(file_path, chunk_dir, chunk_size=400, chunk_overlap=100)
    



