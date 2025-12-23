import json
import re
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

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
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str) -> List[str]:
    return splitter.split_text(text)

# ---------------- Semantic Metadata ----------------

class SemanticMetadata(BaseModel):
    summary: str = Field(..., description="One sentence summary")
    topics: list[str] = Field(..., description="Up to 5 keywords")

SEMANTIC_PROMPT = """
You are analyzing a web document.
Return ONLY a strict JSON object with keys "summary" and "topics".
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

def main():
    json_dir = "test"  # folder with your JSON files
    output_file = "chunked_with_metadata.json"

    print("Loading JSON files...")
    docs = load_jsons(json_dir)

    print("Cleaning text...")
    for doc in docs:
        doc["text"] = simple_clean(doc["text"])

    print("Chunking text and generating semantic metadata per chunk...")
    chunked_docs = []
    for doc in docs:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i} of {doc['url']} ...")
            semantic = extract_semantic_metadata(chunk)
            
            # Skip chunks whose topics include "cookies" (case-insensitive)
            if any(topic.lower() == "cookies" for topic in semantic.get("topics", [])):
                print(f"Skipping chunk {i} of {doc['url']} (topic contains 'cookies')")
                continue
            
            chunked_docs.append({
                "url": doc["url"],
                "chunk_id": i,
                "content": chunk,
                "summary": semantic.get("summary", ""),
                "topics": semantic.get("topics", [])
            })

    print(f"Saving chunked docs with metadata to {output_file} ...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunked_docs, f, ensure_ascii=False, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
