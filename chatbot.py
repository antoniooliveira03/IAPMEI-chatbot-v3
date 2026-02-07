# Libraries
from pathlib import Path
from openai import OpenAI
import numpy as np
import faiss
import json
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re


load_dotenv()
client = OpenAI()

# Directories
VECTOR_DIR = Path("data/05_vectorized")

# ---------------- Embedding ----------------
def embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)

def embed_query(query: str) -> np.ndarray:
    return embedding(query)

# ---------------- FAISS Loader ----------------
def load_faiss_index(vector_dir: Path):
    index_path = vector_dir / "db.index"
    meta_path = vector_dir / "db.json"

    index = faiss.read_index(str(index_path))

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return index, metadata

# ---------------- BM25 ----------------
def tokenize(text):
    return re.findall(r"\w+", text.lower())

def build_bm25(metadata):
    corpus = [tokenize(doc["content"] + " " + doc.get("summary","")) for doc in metadata]
    bm25 = BM25Okapi(corpus)
    return bm25

# ---------------- Retrieval ----------------
def tokenize(text):
    return re.findall(r"\w+", text.lower())

def build_bm25(metadata):
    corpus = [tokenize(doc["content"]) for doc in metadata]
    bm25 = BM25Okapi(corpus)
    return bm25


# ---------------- Hybrid Retrieval ----------------
def retrieve_hybrid(query, index, metadata, bm25, k=5, weight_dense=0.5, weight_sparse=0.5):
    # Dense retrieval
    q_vec = embed_query(query)
    D, I = index.search(q_vec, k*2)
    dense_scores = D[0]
    dense_indices = I[0]
    dense_scores = (dense_scores - dense_scores.min()) / (dense_scores.max() - dense_scores.min() + 1e-8)

    # Sparse retrieval
    tokenized_query = tokenize(query)
    sparse_scores = bm25.get_scores(tokenized_query)
    sparse_scores = (sparse_scores - np.min(sparse_scores)) / (np.max(sparse_scores) - np.min(sparse_scores) + 1e-8)

    # Combine scores
    hybrid_scores = {}
    for idx, dense_score in zip(dense_indices, dense_scores):
        hybrid_scores[idx] = weight_dense * dense_score + weight_sparse * sparse_scores[idx]

    ranked_indices = sorted(hybrid_scores.keys(), key=lambda x: hybrid_scores[x], reverse=True)
    return [metadata[i] for i in ranked_indices[:k]]


# ---------------- Chatbot Answer ----------------
conversation_history = []

def answer(user_query: str, index, 
           metadata, bm25, k=10, 
           model="gpt-4o-mini"):

    global conversation_history
    max_history = 10

    # Moderation
    mod_result = client.moderations.create(
        model="omni-moderation-latest",
        input=user_query
    )

    if mod_result.results[0].flagged:
        return "Query flagged by moderation.", []

    # Retrieve context
    context_chunks = retrieve_hybrid(user_query, index, metadata, bm25, k=k)

    context_text = "\n\n".join(
        f"[{c['source_file']}]\nResumo: {c.get('summary','')}\nTexto: {c['content']}"
        for c in context_chunks
    )

    prompt = f"""
        És um assistente especialista em programas de incentivos nacionais e regionais, como o PT2030, Compete2030, Alentejo2030, etc.
        Responde sempre em Português de Portugal.

        Regras:
        - Responde de forma clara e concisa.
        - Baseia-te no contexto fornecido para responder.
        - Se não souberes a resposta ou se não houver informação no contexto, informa o utilizador e pergunta se podes ajudar noutro tema.
        - Sempre que possível, indica a fonte (link ou nome do ficheiro).

        Contexto:
        {context_text}

        Pergunta: {user_query}
        Resposta:
        """

    messages = [{"role": "system", "content": prompt}]
    conversation_history = conversation_history[-max_history:]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_query})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )

    final_answer = response.choices[0].message.content.strip()

    conversation_history.append({"role": "user", "content": user_query})
    conversation_history.append({"role": "assistant", "content": final_answer})

    print("\nAssistente:", final_answer)
    return final_answer, context_chunks

# ---------------- Main Loop ----------------
def main():
    index, metadata = load_faiss_index(VECTOR_DIR)
    bm25 = build_bm25(metadata)

    while True:
        user_query = input("\nPergunta: ").strip()
        if user_query.lower() in ["sair", "exit", "quit"]:
            print("Assistente: Até à próxima!")
            break
        answer(user_query, index, metadata, bm25, k=5)

if __name__ == "__main__":
    main()
