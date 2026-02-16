# Libraries
from pathlib import Path
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI()

chunk_size = 600
chunk_overlap = 60
embeddings_type = "small" # "large" or "small"


# Directories
chunk_dir = Path(f"data/03_chunked/c{chunk_size}_{chunk_overlap}")
vector_dir = Path(f"data/05_vectorized/{embeddings_type}/c{chunk_size}_{chunk_overlap}")
vector_dir.mkdir(parents=True, exist_ok=True)

# ---------- Embedding ----------
def embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model=f"text-embedding-3-{embeddings_type}",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

# ---------- FAISS DB ----------
def build_db(chunk_dir: Path):
    metadata = []
    index = None

    dim = 1536 if embeddings_type == "small" else 3072 # 3072 for text-embedding-3-large, 1536 for small

    index = faiss.IndexFlatIP(dim) 
    print(f"[INFO] FAISS index initialized with dim={dim}")

    for json_path in chunk_dir.glob("*.json"):
        source_file = json_path.stem

        with open(json_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        for chunk in chunks:
            #combined_text = " ".join(chunk.get("topics", []) + [chunk.get("summary", ""), chunk["content"]])
            combined_text = chunk["content"]
            vec = embedding(combined_text)
            vec = vec / np.linalg.norm(vec)

            index.add(vec.reshape(1, -1))

            metadata.append({
                "source_file": source_file,
                "url": chunk["url"],
                "chunk_id": chunk["chunk_id"],
                "fingerprint": chunk.get("fingerprint"),
                "content": chunk["content"],
              #  "summary": chunk.get("summary", ""),
              #  "topics": chunk.get("topics", []),
                "chunk_vector": vec.tolist()
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
