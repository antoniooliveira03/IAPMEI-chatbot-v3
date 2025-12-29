# Libraries
from pathlib import Path
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI()

# Directories
chunk_dir = Path("data/03_chunked")
vector_dir = Path("data/04_vectorized")
vector_dir.mkdir(parents=True, exist_ok=True)

# ---------- Embedding ----------
def embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

# ---------- FAISS DB ----------
def build_db(chunk_dir: Path):
    metadata = []
    index = None

    for json_path in chunk_dir.glob("*.json"):
        source_file = json_path.stem

        with open(json_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        for chunk in chunks:
            vec = embedding(chunk["content"])

            if index is None:
                index = faiss.IndexFlatL2(len(vec))

            index.add(vec.reshape(1, -1))

            metadata.append({
                "source_file": source_file,
                "url": chunk["url"],
                "chunk_id": chunk["chunk_id"],
                "fingerprint": chunk.get("fingerprint"),
                "content": chunk["content"],
                "summary": chunk.get("summary", ""),
                "topics": chunk.get("topics", [])
            })

    return index, metadata

# ---------- Run ----------
index, metadata = build_db(chunk_dir)

faiss_index_path = vector_dir / "db.index"
metadata_path = vector_dir / "db.json"

faiss.write_index(index, str(faiss_index_path))

with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print("\n[OK] FAISS index and metadata saved")
