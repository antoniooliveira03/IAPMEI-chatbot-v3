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


# Vectorize
def embedding(text: str):

    embedding_model = client.embeddings.create(
        model = "text-embedding-3-small",
        input = text
    )

    vector = np.array(embedding_model.data[0].embedding, dtype=np.float32)

    return vector

# VDb
def db(json_file: Path):

    metadata = []
    index = None

    for json_file in chunk_dir.iterdir():

        with open(json_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)


        for chunk in chunks:
            vec = embedding(chunk["text"])

            if index is None:
                index = faiss.IndexFlatL2(len(vec))

            index.add(vec.reshape(1, -1))

            metadata.append({
                "source_file": chunk["source_file"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"]
            })

    return index, metadata

# Run

# Create FAISS index and metadata
index, metadata = db(chunk_dir)
# Save FAISS index and metadata
faiss_index_path = vector_dir / "db.index"
metadata_path = vector_dir / "db.json"

faiss.write_index(index, str(faiss_index_path))

# Save metadata
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print("\n[OK] Single FAISS index saved")