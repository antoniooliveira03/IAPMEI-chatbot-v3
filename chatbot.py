# Libraries
from pathlib import Path
from openai import OpenAI
import numpy as np
import faiss
import json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
vector_dir = Path("data/04_vectorized")
chunk_dir = Path("data/03_chunked")

# Load Vectors and Metadata

def load_all_indexes(vector_dir: Path, chunk_dir: Path):

    all_indexes = []

    for index_file in vector_dir.glob("*.index"):

        # Load FAISS index
        index = faiss.read_index(str(index_file))

        # Load metadata JSON from 03_chunked
        meta_file = chunk_dir / (index_file.stem + ".json")

        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        all_indexes.append({
            "index": index,
            "metadata": metadata,
            "name": index_file.stem
        })
        
    return all_indexes


# Embed Query
def embed_query(query: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)

# Get Context
def retrieve_context_single(query: str, index: faiss.IndexFlatL2, metadata: list, k=5):
    q_vec = embed_query(query)
    D, I = index.search(q_vec, k)
    return [metadata[i] for i in I[0]]

def retrieve_context(query: str, all_indexes: list, k=5):
    all_chunks = []

    for idx_dict in all_indexes:
        index = idx_dict["index"]
        metadata = idx_dict["metadata"]
        chunks = retrieve_context_single(query, index, metadata, k=k)
        all_chunks.extend(chunks)

    return all_chunks


# User Input
user_query = input("Enter your question: ")

# Answer
def answer(user_query: str, all_indexes, k=5, model="gpt-4o-mini") -> str:

    # Safety Check
    mod_result = client.moderations.create(
                    model="omni-moderation-latest",
                    input=user_query)

    if mod_result.results[0].flagged:
        return "Query flagged by moderation. Unable to provide an answer."
    
    # Retrieve Context
    context_chunks = retrieve_context(user_query, all_indexes, k=k)

    context_text = "\n\n".join([c["text"] for c in context_chunks])

    # Prompt
    prompt = f"""
            És um assistente que responde às perguntas dos utilizadores com base nos documentos fornecidos.
            Prioriza a exactidão dos factos; quando não tiveres a certeza, indica-o e fornece as fontes.
            Mantém as respostas concisas e fornece referências (nome do ficheiro sempre que aplicável.
            Responde sempre em Português de Portugal.

            Se as questões do utilizador forem fora do âmbito dos documentos, responde educadamente que não tens essa informação. 
            Podes também sugerir perguntas às quais possas responder com base nos documentos, tais como:
            - Quais são os principais serviços oferecidos pelo IAPMEI?
            - Como posso beneficiar do apoio do IAPMEI para a minha PME?
            - Em que consiste o programa de Incentivos PT2030?

            {context_text}

            Question: {user_query}
            Answer:
            """

    # LLM
    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0
                    )

    final_answer = response.choices[0].message.content

    print(final_answer)


# Load all indexes
all_indexes = load_all_indexes(vector_dir, chunk_dir)

# Get answer
answer(user_query, all_indexes, k=5)