# Libraries
from pathlib import Path
from openai import OpenAI
import numpy as np
import faiss
import json
import hashlib
from dotenv import load_dotenv
import numpy as np
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

# ---------------- Query Embedding ----------------
def embed_query(query: str) -> np.ndarray:
    return embedding(query)

# ---------------- Retrieval ----------------
def rerank_by_similarity(query_vec, retrieved_docs):
    sims = []
    for doc in retrieved_docs:
        doc_vec = np.array(doc['chunk_vector']).reshape(1, -1)
        sim = cosine_similarity(query_vec, doc_vec)[0][0]
        sims.append(sim)
    # Sort by similarity only
    sorted_docs = [doc for _, doc in sorted(zip(sims, retrieved_docs), key=lambda x: x[0], reverse=True)]
    return sorted_docs


def retrieve_context(query: str, index, metadata, k=5, use_rerank=False):
    """
    Retrieve top-k chunks from FAISS index.
    If use_rerank=True, rerank the retrieved chunks by cosine similarity with query embedding.
    """
    q_vec = embed_query(query)
    D, I = index.search(q_vec, k * 2)  
    retrieved_docs = [metadata[i] for i in I[0]]

    if use_rerank:
        retrieved_docs = rerank_by_similarity(q_vec, retrieved_docs)
    
    return retrieved_docs[:5]  



# ---------------- Determine if context is needed ----------------
def needs_context(query: str, model="gpt-4o-mini") -> bool:
    prompt = f"""
        És um assistente que determina se uma pergunta necessita de contexto adicional para ser respondida.
        Responde com "SIM" se precisares de contexto dos documentos fornecidos, ou "NÃO" se puderes responder sem contexto.

        Pergunta: {query}
        Resposta (SIM ou NÃO):
        """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    answer = response.choices[0].message.content.strip().upper()
    return answer == "SIM"

# ---------------- Chatbot Answer ----------------
conversation_history = []

def answer(user_query: str, index, metadata, k=5, model="gpt-4o-mini", use_rerank=False):
    global conversation_history
    max_history = 10

    # Moderation
    mod_result = client.moderations.create(
        model="omni-moderation-latest",
        input=user_query
    )
    if mod_result.results[0].flagged:
        return "Query flagged by moderation."

    # Context check
    context_needed = needs_context(user_query)

    context_chunks = (
        retrieve_context(user_query, index, metadata, k, use_rerank)
        if context_needed else []
    )

    context_text = "\n\n".join(
        f"[{c['source_file']}]\nResumo: {c.get('summary','')}\nTexto: {c['content']}"
        for c in context_chunks
    )


    prompt = f"""
        És um assistente especialista em programas de incentivos a empresas portuguesas, PT2030 e IAPMEI.
        O teu trabalho é responder às perguntas dos utilizadores com base na informação a que tens acesso.

        Regras:
        - Responde sempre de forma concisa e clara.
        - Prioriza a exatidão dos factos; se não tiveres a resposta certa, indica que não tens informação suficiente e questiona se podes ajudar de outra maneira.
        - Sempre que possível, fornece a fonte utilizada (nome do ficheiro ou link).
        - Responde obrigatoriamente em Português de Portugal, com vocabulário formal.
        - Se a pergunta requer múltiplos passos, pensa passo a passo antes de responder.
        - Se a pergunta não estiver nos documentos, remete o utilizador ao website oficial com link.

        Exemplo:
        Pergunta: Quais os programas de incentivo disponíveis para PME em 2024?
        Resposta: Os programas incluem o Incentivo X (fonte) e o Incentivo Y (fonte).

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
        answer(user_query, index, metadata, k=5)

if __name__ == "__main__":
    main()
