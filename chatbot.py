# Libraries
from pathlib import Path
from openai import OpenAI
import numpy as np
import faiss
import json
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

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

# ---------------- FAISS Loader ----------------
def load_faiss_index(vector_dir: Path):
    index_path = vector_dir / "db.index"
    meta_path = vector_dir / "db.json"

    index = faiss.read_index(str(index_path))

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return index, metadata

# ---------------- Reranking ----------------
def rerank_by_similarity(query_vec, retrieved_docs):
    scores = []
    for doc in retrieved_docs:
        doc_vec = np.array(doc['chunk_vector']).reshape(1, -1)
        sim = cosine_similarity(query_vec, doc_vec)[0][0]
        scores.append(sim)

    sorted_docs = [
        doc for _, doc in
        sorted(zip(scores, retrieved_docs), key=lambda x: x[0], reverse=True)
    ]
    return sorted_docs

# ---------------- Retrieval ----------------
def retrieve_context(
    query: str,
    index,
    metadata,
    k_retrieve=20,
    k_prompt=5,
    use_rerank=False
):
    """
    1) Retrieve k_retrieve chunks from FAISS
    2) Optionally rerank
    3) Return only top k_prompt chunks for LLM
    """

    query_vec = embedding(query)

    # Retrieve more for better reranking
    D, I = index.search(query_vec, k_retrieve)
    retrieved_docs = [metadata[i] for i in I[0]]

    if use_rerank:
        retrieved_docs = rerank_by_similarity(query_vec, retrieved_docs)

    return retrieved_docs[:k_prompt]

# ---------------- Chatbot Answer ----------------
conversation_history = []

def answer(
    user_query: str,
    index,
    metadata,
    k_retrieve=20,
    k_prompt=5,
    model="gpt-4o-mini",
    use_rerank=False
):
    global conversation_history
    max_history = 10

    # Moderation
    mod_result = client.moderations.create(
        model="omni-moderation-latest",
        input=user_query
    )

    if mod_result.results[0].flagged:
        return "Query flagged by moderation.", []

    # Always retrieve context
    context_chunks = retrieve_context(
        user_query,
        index,
        metadata,
        k_retrieve=k_retrieve,
        k_prompt=k_prompt,
        use_rerank=use_rerank
    )

    context_text = "\n\n".join(
        f"[{c['source_file']}]\nResumo: {c.get('summary','')}\nTexto: {c['content']}"
        for c in context_chunks
    )

    prompt = f"""
És um assistente especialista em programas de incentivos a empresas portuguesas, PT2030 e IAPMEI.
Responde sempre em Português de Portugal.

Regras:
- Responde de forma clara e concisa.
- Baseia-te apenas no contexto fornecido.
- Se a resposta não estiver no contexto, diz que não tens informação suficiente.
- Sempre que possível, indica a fonte (nome do ficheiro ou link).

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

    while True:
        user_query = input("\nPergunta: ").strip()

        if user_query.lower() in ["sair", "exit", "quit"]:
            print("Assistente: Até à próxima!")
            break

        answer(
            user_query,
            index,
            metadata,
            k_retrieve=20,   # retrieve more
            k_prompt=5,      # send fewer to LLM
            use_rerank=True  # toggle on/off
        )

if __name__ == "__main__":
    main()
