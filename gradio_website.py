import gradio as gr
from chatbot import load_faiss_index, build_bm25, answer
from pathlib import Path
import json
import time
import uuid
from datetime import datetime



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

# ---------------- Session Helpers ----------------

def generate_session_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_session_file(session_id):
    return HISTORY_DIR / f"{session_id}.json"

def list_sessions():
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    return [f.stem for f in files]

def load_session(session_id):
    path = get_session_file(session_id)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"title": "Nova Conversa", "messages": []}

def save_session(session_id, data):
    path = get_session_file(session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def new_chat():
    new_session = generate_session_id()

    save_session(new_session, {
        "title": "Nova Conversa",
        "messages": []
    })

    return (
        [],                     # Clear chat
        "",                     # Clear textbox
        new_session,            # Update session state
        gr.update(
            choices=list_sessions(),
            value=new_session   # IMPORTANT: select it immediately
        )
    )


def rename_session(new_title, session_id):
    session_data = load_session(session_id)
    session_data["title"] = new_title
    save_session(session_id, session_data)

    return gr.update(choices=list_sessions(), value=session_id)


def load_selected_session(session_id):
    session_data = load_session(session_id)
    
    chat_format = []
    for msg in session_data["messages"]:
        chat_format.append({"role": "user", "content": msg["user"]})
        chat_format.append({"role": "assistant", "content": msg["assistant"]})
    
    return chat_format, session_id

def list_sessions():
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    sessions = []
    
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            sessions.append((data.get("title", "Nova Conversa"), f.stem))
    
    return sessions  # list of (title, session_id)

def load_selected_session(session_id):
    session_data = load_session(session_id)

    chat_format = []
    for msg in session_data["messages"]:
        chat_format.append({"role": "user", "content": msg["user"]})
        chat_format.append({"role": "assistant", "content": msg["assistant"]})

    return chat_format, session_id


# ---------------- Chat function ----------------
def chat_stream(user_query, chat_history, session_id):
    if not user_query.strip():
        yield chat_history, "", session_id

    session_data = load_session(session_id)

    if chat_history is None:
        chat_history = []

    chat_history.append({"role": "user", "content": user_query})
    chat_history.append({"role": "assistant", "content": ""})
    assistant_index = len(chat_history) - 1

    yield chat_history, "", session_id

    bot_response, _ = answer(user_query, index, metadata, bm25)

    for char in bot_response:
        chat_history[assistant_index]["content"] += char
        yield chat_history, "", session_id

    # Save full session
    session_data["messages"].append({
        "user": user_query,
        "assistant": bot_response,
        "timestamp": datetime.now().isoformat()
    })

    # Auto-generate title from first question
    if len(session_data["messages"]) == 1:
        session_data["title"] = user_query[:40]

    save_session(session_id, session_data)


# ---------------- Gradio Interface ----------------
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Assistente PT2030 / IAPMEI")

    initial_session = generate_session_id()

    save_session(initial_session, {
        "title": "Nova Conversa",
        "messages": []
    })

    session_state = gr.State(initial_session)

    with gr.Row():

        # Sidebar
        with gr.Column(scale=0.25):

            new_chat_btn = gr.Button("Nova Conversa", variant="primary")

            conversation_list = gr.Dropdown(
                choices=list_sessions(),
                label="📂 Conversas",
                value =initial_session,
                interactive=True
            )

            rename_box = gr.Textbox(
                label="✏️ Renomear Conversa",
                placeholder="Novo nome...",
                lines=1
            )

            rename_btn = gr.Button("Guardar Nome")

            gr.Markdown("### 💡 Perguntas sugeridas")
            suggested_buttons = []
            for q in SUGGESTED_QUESTIONS:
                btn = gr.Button(q)
                suggested_buttons.append(btn)


        # Chat
        with gr.Column(scale=0.75):
            chat_history = gr.Chatbot()
            user_input = gr.Textbox(
                placeholder="Escreve a tua pergunta...",
                lines=1
            )

            user_input.submit(
                chat_stream,
                inputs=[user_input, chat_history, session_state],
                outputs=[chat_history, user_input, session_state],
                queue=True
            )

            gr.Markdown(
            """
            <div style="font-size: 12px; color: gray; margin-top: 10px;">
            ⚖️ As informações enviadas destinam-se exclusivamente à prestação de esclarecimentos e não produzem efeitos na sua situação atual.
            Os dados poderão ser armazenados até 180 dias para melhoria do serviço.
            Ao utilizar este assistente, aceita os termos e condições aplicáveis.
            </div>
            """,
            elem_id="legal_notice"
        )


    # Button connections
    new_chat_btn.click(
        new_chat,
        outputs=[chat_history, user_input, session_state, conversation_list]
    )

    conversation_list.change(
        load_selected_session,
        inputs=[conversation_list],
        outputs=[chat_history, session_state]
    )

    rename_btn.click(
        rename_session,
        inputs=[rename_box, session_state],
        outputs=[conversation_list]
    )


    for btn, question in zip(suggested_buttons, SUGGESTED_QUESTIONS):
        btn.click(lambda q=question: q, outputs=[user_input])

demo.launch()