import json
import re
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import hashlib

load_dotenv()

# ---------------- Setup ----------------

client = OpenAI()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)

# ---------------- Functions ----------------

def load_jsons(json_dir: str) -> List[Dict]:
    docs = []
    for path in Path(json_dir).glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    docs.append({"url": item["url"], "text": item["text"]})
            elif isinstance(data, dict):
                docs.append({"url": data["url"], "text": data["text"]})
    return docs

def simple_clean(text: str) -> str:
    # Basic cleaning: collapse whitespace
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str) -> List[str]:
    return splitter.split_text(text)

def chunk_fingerprint(text: str) -> str:
    return hashlib.md5(
        re.sub(r"\s+", " ", text.lower()).encode("utf-8")).hexdigest()



# ---------------- Semantic Metadata ----------------

class SemanticMetadata(BaseModel):
    summary: str = Field(..., description="One sentence summary")
    topics: list[str] = Field(..., description="Up to 5 keywords")

SEMANTIC_PROMPT = """
You are analyzing a web document.
Return ONLY a strict JSON object with keys "summary" and "topics" written in Portuguese language.
Do not include any other text.

Text:
"""

def extract_semantic_metadata(text: str) -> dict:
    """Generate validated semantic metadata using OpenAI and Pydantic."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": SEMANTIC_PROMPT + text[:3000]}],
        temperature=0
    )
    raw = response.choices[0].message.content.strip()
    
    try:
        # Attempt to parse JSON
        parsed = json.loads(raw)
        return SemanticMetadata(**parsed).model_dump()
    except Exception:
        # fallback empty
        return {"summary": "", "topics": []}

# ---------------- Main Pipeline ----------------

from pathlib import Path
import json

def main():
    input_dir = Path("data/02_clean")
    output_dir = Path("data/03_chunked")

    output_dir.mkdir(parents=True, exist_ok=True)

    for json_path in input_dir.glob("*.json"):
        print(f"\nProcessing file: {json_path.name}")

        with open(json_path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        chunked_docs = []
        # For chunk deduplication 
        seen_fingerprints = {}  

        for doc in docs:
            text = simple_clean(doc["text"])
            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                fingerprint = chunk_fingerprint(chunk)

                # ---------- Deduplication ----------
                if fingerprint in seen_fingerprints:
                    first = seen_fingerprints[fingerprint]

                    print("\n[DUPLICATE CHUNK DETECTED]")
                    print(f"First seen in: {first['url']} (chunk {first['chunk_id']})")
                    print(f"Duplicate in:  {doc['url']} (chunk {i})")
                    continue

                seen_fingerprints[fingerprint] = {
                        "url": doc["url"],
                        "chunk_id": i,
                        "preview": chunk[:200]
                    }

                semantic = extract_semantic_metadata(chunk)

                # Skip cookie boilerplate chunks
                if any(t.lower() == "cookies" for t in semantic.get("topics", [])):
                    continue

                chunked_docs.append({
                    "url": doc["url"],
                    "chunk_id": i,
                    "fingerprint": fingerprint,
                    "content": chunk,
                    "summary": semantic.get("summary", ""),
                    "topics": semantic.get("topics", [])
                })

        out_path = output_dir / json_path.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunked_docs, f, ensure_ascii=False, indent=2)

        print(f"Saved → {out_path} ({len(chunked_docs)} unique chunks)")

    print("\nAll files processed")


if __name__ == "__main__":
    main()
