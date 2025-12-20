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


# Load Vectors and Metadata
def load_single_index(vector_dir: Path):

    index_path = vector_dir / f"corpus.index"
    meta_path = vector_dir / f"corpus_metadata.json"

    # Load FAISS index
    index = faiss.read_index(str(index_path))

    # Load metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return index, metadata




# Embed Query
def embed_query(query: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)

# Get Context
def retrieve_context(query: str, index: faiss.IndexFlatL2, metadata: list, k=5):
    q_vec = embed_query(query)
    D, I = index.search(q_vec, k)
    return [metadata[i] for i in I[0]]


# Context Necessary?
def needs_context(query: str, model="gpt-4o-mini") -> bool:
    prompt = f"""
            És um assistente que determina se uma pergunta necessita de contexto adicional para ser respondida.
            Responde com "SIM" se precisares de contexto dos documentos fornecidos, ou "NÃO" se puderes responder sem contexto.

            Pergunta: {query}
            Resposta (SIM ou NÃO):
            """

    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": prompt}
                        ],
                        temperature=0
                    )

    answer = response.choices[0].message.content.strip().upper()

    return answer == "SIM"


# Answer
def answer(user_query: str, index, metadata,  k=5, model="gpt-4o-mini") -> str:

    global conversation_history
    max_history = 10 

    # Safety Check
    mod_result = client.moderations.create(
                    model="omni-moderation-latest",
                    input=user_query)

    if mod_result.results[0].flagged:
        return "Query flagged by moderation. Unable to provide an answer."
    
    # Embed query
    q_vec = embed_query(user_query)
    
    # Retrieve Context
    context_needed = needs_context(user_query)
    context_chunks, distances = [], []

    context_text = ""
    if context_needed:
        D, I = index.search(q_vec, k)
        context_chunks = [metadata[i] for i in I[0]]
        distances = D[0] 

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
    messages = [{"role": "system", "content": prompt}]

    conversation_history = conversation_history[-max_history:]

    for msg in conversation_history:
        messages.append(msg)

    messages.append({
        "role": "user",
        "content": f"Contexto:\n{context_text}\n\nPergunta: {user_query}"
    })


    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages = messages,
                        temperature=0
                    )

    final_answer = response.choices[0].message.content

    conversation_history.append({"role": "user", "content": user_query})
    conversation_history.append({"role": "assistant", "content": final_answer})


    print(final_answer)

    return final_answer, context_chunks, distances


# Save conversation history
conversation_history = []

# Load all indexes
index, metadata = load_single_index(vector_dir)

# Get answer
def main():
    index, metadata = load_single_index(vector_dir)
    while True:
        user_query = input("\nPergunta: \n")
        if user_query.lower().strip() in ["sair", "exit", "quit"]:
            print("Assistente: Até à próxima!")
            break
        answer(user_query, index, metadata, k=5)

if __name__ == "__main__":
    main()