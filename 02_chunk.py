import json
import re
import hashlib
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------- Setup ----------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)

# ---------------- Helpers ----------------

def simple_clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str):
    return splitter.split_text(text)

def chunk_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

# ---------------- Phase 1 ----------------

def main():
    input_dir = Path("data/02_clean")
    output_dir = Path("data/03_chunked")
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_path in input_dir.glob("*.json"):
        print(f"\n[PHASE 1] Processing: {json_path.name}")

        with open(json_path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        seen_fingerprints = set()
        unique_chunks = []

        for doc in docs:
            text = simple_clean(doc["text"])
            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                fingerprint = chunk_fingerprint(chunk)

                if fingerprint in seen_fingerprints:
                    continue

                seen_fingerprints.add(fingerprint)

                unique_chunks.append({
                    "url": doc["url"],
                    "chunk_id": i,
                    "fingerprint": fingerprint,
                    "content": chunk
                })

        out_path = output_dir / json_path.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(unique_chunks, f, ensure_ascii=False, indent=2)

        print(f"Saved → {out_path} ({len(unique_chunks)} unique chunks)")

    print("\n[PHASE 1 COMPLETE]")

if __name__ == "__main__":
    main()
