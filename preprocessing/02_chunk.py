# Libraries
import json
import re
import hashlib
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from urllib.parse import urlparse

# Setup
chunk_size = 600
chunk_overlap = 60

splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size, 
    chunk_overlap=chunk_overlap, 
    separators=["\n\n", "\n", ".", "!", "?"]
)

# Helpers 
def get_chunk_source(doc: dict, file_name: str):
    """Determine the source text and URL for chunking, based on document structure."""
    # Scraped page
    if "text" in doc and "url" in doc:
        return doc["text"], doc["url"], True  # chunkable=True

    # Q&A style
    if "Q" in doc and "A" in doc:
        text = f"Q: {doc['Q']}\n\nA: {doc['A']}"
        url = f"qa://{file_name}#{hash(doc['Q'])}"
        return text, url, False  # chunkable=False

    # Unknown → skip safely
    return None, None, None


def url_to_title(url: str, max_words=7):
    """Generate a human-readable title from a URL, using path segments or domain as fallback."""
    parsed = urlparse(url)
    path = parsed.path  # e.g., /programas/inovacao-e-sustentabilidade
    domain = parsed.netloc.replace("www.", "")  # fallback if path is empty

    segments = [seg for seg in path.split("/") if seg]  # remove empty
    if segments:
        # take last segment and split by "-"
        title_words = segments[-1].split("-")[:max_words]
        title = " ".join(title_words).capitalize()
        return title
    else:
        # fallback to domain name
        return domain if domain else "Página Sem Título"


def simple_clean(text: str) -> str:
    """Basic cleaning: normalize whitespace and trim."""
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str):
    """Use RecursiveCharacterTextSplitter to chunk the text based on the configured chunk size and overlap."""
    return splitter.split_text(text)


def chunk_fingerprint(text: str) -> str:
    """Generate a fingerprint for a chunk by normalizing and hashing its content."""
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

# Main pipeline

def main():
    """Main chunking pipeline: read cleaned JSON files, extract and chunk content, deduplicate, and save results."""

    input_dir = Path("data/02_clean")
    output_dir = Path(f"data/03_chunked/c{chunk_size}_{chunk_overlap}")
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_path in input_dir.glob("*.json"):
        print(f"\n[PHASE 1] Processing: {json_path.name}")

        with open(json_path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        seen_fingerprints = {}   # fingerprint → first occurrence
        unique_chunks = []

        for doc in docs:
            text, source_url, chunkable = get_chunk_source(doc, json_path.name)

            if not text:
                continue

            text = simple_clean(text)

            # Chunkable content (web pages)
            if chunkable:
                chunks = chunk_text(text)
                for i, chunk in enumerate(chunks):
                    fingerprint = chunk_fingerprint(chunk)

                    if fingerprint in seen_fingerprints:
                        first = seen_fingerprints[fingerprint]
                        print("\n[DUPLICATE CHUNK]")
                        print(f"First seen in: {first['url']} (chunk {first['chunk_id']})")
                        print(f"Duplicate in:  {source_url} (chunk {i})")
                        continue

                    seen_fingerprints[fingerprint] = {"url": source_url, "chunk_id": i}

                    unique_chunks.append({
                        "url": source_url,
                        "chunk_id": i,
                        "fingerprint": fingerprint,
                        "content": f"Fonte: {url_to_title(source_url)}: {chunk}"
                    })

            # Non-chunkable content (Q&A)
            else:
                fingerprint = chunk_fingerprint(text)
                if fingerprint in seen_fingerprints:
                    continue

                seen_fingerprints[fingerprint] = {"url": source_url, "chunk_id": 0}

                unique_chunks.append({
                    "url": source_url,
                    "chunk_id": 0,
                    "fingerprint": fingerprint,
                    "content": text
                })

        # Save AFTER all docs are processed
        out_path = output_dir / json_path.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(unique_chunks, f, ensure_ascii=False, indent=2)

        print(f"\nSaved → {out_path} ({len(unique_chunks)} unique chunks)")

    print("\n[PHASE 2 COMPLETE]")


# Execution entry point
if __name__ == "__main__":
    main()
