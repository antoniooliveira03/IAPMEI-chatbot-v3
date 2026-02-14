import gradio as gr
from chatbot import load_faiss_index, build_bm25, answer
from pathlib import Path
import json
import time


VECTOR_DIR = Path("data/05_vectorized/large")
HISTORY_DIR = Path("conversation_history")
HISTORY_DIR.mkdir(exist_ok=True)

# Load FAISS index and metadata once
index, metadata = load_faiss_index(VECTOR_DIR)
bm25 = build_bm25(metadata)

USER_ID = "default_user" 

# Suggested questions
SUGGESTED_QUESTIONS = [
    "O que é o PT2030?",
    "Qual é o objetivo principal do Programa Algarve 2030?",
    "Como as empresas podem obter a certificação PME?",
    "Qual é a diferença entre o PT2030, IAPMEI e Compete 2030?",
    "Como funciona o processo de candidatura a incentivos do PT2030?",
]

# ---------------- Helper functions ----------------
def get_history_file(user_id):
    return HISTORY_DIR / f"{user_id}.json"

def load_history(user_id):
    path = get_history_file(user_id)
    if path.exists():
        if path.stat().st_size == 0:  # empty file
            return []
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # invalid JSON
    return []


def save_history(user_id, history):
    path = get_history_file(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ---------------- Chat function ----------------
def chat_stream(user_query, chat_history):
    if not user_query.strip():
        yield chat_history, ""  # ignore empty input

    if chat_history is None:
        chat_history = []

    # Append user message
    chat_history.append({"role": "user", "content": user_query})
    chat_history.append({"role": "assistant", "content": ""})
    assistant_index = len(chat_history) - 1

    # Clear input immediately
    yield chat_history, ""

    # Get bot response
    bot_response, _ = answer(user_query, index, metadata, bm25)

    # Stream character by character
    for char in bot_response:
        chat_history[assistant_index]['content'] += char
        yield chat_history, ""

    # Save to JSON
    history_file = load_history(USER_ID)
    history_file.append({"prompt": user_query, "response": bot_response})
    save_history(USER_ID, history_file)



# ---------------- Gradio Interface ----------------
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Assistente PT2030 / IAPMEI")

    with gr.Row():
        # Sidebar
        with gr.Column(scale=0.2):
            gr.Markdown("### 💡 Perguntas sugeridas")
            suggested_buttons = []
            for q in SUGGESTED_QUESTIONS:
                btn = gr.Button(q)
                suggested_buttons.append(btn)

        # Main chat
        with gr.Column(scale=6):
            chat_history = gr.Chatbot()
            user_input = gr.Textbox(
                placeholder="Escreve a tua pergunta...",
                lines=1
            )

            # Submit user input directly to streaming chat
            user_input.submit(
                chat_stream,
                inputs=[user_input, chat_history],
                outputs=[chat_history, user_input],
                queue=True
            )

    # Connect sidebar buttons to fill the textbox
    for btn, question in zip(suggested_buttons, SUGGESTED_QUESTIONS):
        btn.click(lambda q=question: q, inputs=[], outputs=[user_input])

demo.launch()

