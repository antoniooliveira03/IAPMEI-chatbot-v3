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

    with open(json_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)


    for chunk in chunks:
        vec = embedding(chunk["text"])

        if index is None:
            index = faiss.IndexFlatL2(len(vec))

        index.add(vec.reshape(1, -1))

        metadata.append({
            "source_file": chunk["source_file"],
            "chunk_id": chunk["chunk_id"]
        })

    return index, metadata

# Run
for json_file in chunk_dir.iterdir():

    index, metadata = db(json_file)

    out_index_file = vector_dir / (json_file.stem + ".index")
    faiss.write_index(index, str(out_index_file))

    print(f"[OK] {json_file.name}: FAISS index saved → {out_index_file.name}")
