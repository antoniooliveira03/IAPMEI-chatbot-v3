import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import gradio as gr
from chatbot.chatbot import load_faiss_index, build_bm25, answer
import json
import time
import uuid
from datetime import datetime



VECTOR_DIR = repo_root / "data/04_vectorized/small/c400_40"

HISTORY_DIR = repo_root / "conversation_history"
HISTORY_DIR.mkdir(exist_ok=True)

USERS_FILE = HISTORY_DIR / "users.json"
if not USERS_FILE.exists():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


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
]

# Helpers

def generate_session_id():
    """Generate a unique session ID using timestamp and UUID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_session_file(session_id):
    """Get the file path for a given session ID."""
    return HISTORY_DIR / f"{session_id}.json"

def list_sessions():
    """List all session IDs available in the history directory, sorted by most recent first."""
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    return [f.stem for f in files]

def load_session(user_email, session_id):
    """Load session data for a given user and session ID. Returns a default structure if not found."""
    path = HISTORY_DIR / user_email / f"{session_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"title": "Nova Conversa", "messages": []}


def save_session(user_email, session_id, data):
    """Save session data for a given user and session ID. Creates user folder if it doesn't exist."""
    user_folder = HISTORY_DIR / user_email
    user_folder.mkdir(parents=True, exist_ok=True)

    path = user_folder / f"{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def new_chat(user_email):
    """Start a new chat session for the logged-in user. If no user is logged in, do nothing."""
    if not user_email:
        # No user logged in
        return [], "", None, gr.update()

    # Generate new session
    new_session = generate_session_id()

    # Save initial session for this user
    save_session(user_email, new_session, {
        "title": "Nova Conversa",
        "messages": []
    })

    # Update conversation list for this user
    sessions = list_sessions(user_email)

    return (
        [],                     # Clear chat
        "",                     # Clear input box
        new_session,            # Update session_state
        gr.update(choices=sessions, value=new_session)  # Update dropdown
    )


def rename_session(new_title, session_id, user_email):
    """Rename the current session. If no user is logged in, do nothing."""
    if not user_email:
        return gr.update(), ""  # dropdown unchanged, clear rename box

    # Load session and update title
    session_data = load_session(user_email, session_id)
    session_data["title"] = new_title
    save_session(user_email, session_id, session_data)

    # Update conversation list dropdown and clear rename box
    return gr.update(
        choices=list_sessions(user_email),
        value=session_id
    ), ""  # <-- this clears the rename textbox



def load_selected_session(session_id):
    """Load the selected session's messages and format them for the chatbot. If no user is logged in, return empty."""
    session_data = load_session(session_id)
    
    chat_format = []
    for msg in session_data["messages"]:
        chat_format.append({"role": "user", "content": msg["user"]})
        chat_format.append({"role": "assistant", "content": msg["assistant"]})
    
    return chat_format, session_id

def list_sessions(user_email):
    """List all sessions for the logged-in user, sorted by most recent first. If no user is logged in, return empty."""
    if not user_email:
        return []

    user_folder = HISTORY_DIR / user_email
    if not user_folder.exists():
        return []

    files = sorted(user_folder.glob("*.json"), reverse=True)
    sessions = []

    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            sessions.append((data.get("title", "Nova Conversa"), f.stem))

    return sessions

def load_selected_session(session_id, user_email):
    """Load the selected session's messages and format them for the chatbot. If no user is logged in, return empty."""
    if not user_email:
        return [], None

    session_data = load_session(user_email, session_id)  # include user_email

    chat_format = []
    for msg in session_data["messages"]:
        chat_format.append({"role": "user", "content": msg["user"]})
        chat_format.append({"role": "assistant", "content": msg["assistant"]})

    return chat_format, session_id



def load_users():
    """Load users from the JSON file. Returns a dictionary of {email: password}."""
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def login_or_signup(email, password):
    if not email or not password:
        return "⚠️ Introduza email e password.", None

    users = load_users()

    if email in users:
        # Login
        if users[email] == password:
            return f"✅ Bem-vindo, {email}", email
        else:
            return "❌ Password incorreta.", None
    else:
        # Create account
        users[email] = password
        save_users(users)
        return f"🎉 Conta criada com sucesso ({email})", email

def handle_login(email, password):
    """Handle login/signup logic. Returns status message, user email (for state), and UI updates."""
    message, user_email = login_or_signup(email, password)

    if not user_email:
        # Login failed, leave inputs as they are
        return message, None, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), email, password

    # Login successful → load sessions
    sessions = list_sessions(user_email)

    # If no sessions, create first one
    if not sessions:
        new_session = generate_session_id()
        save_session(user_email, new_session, {
            "title": "Nova Conversa",
            "messages": []
        })
        sessions = list_sessions(user_email)
    else:
        new_session = sessions[0][1]

    # Return outputs: message, user_state, dropdown, buttons enabled, chat input enabled, and clear email/password boxes
    return (
        message,                         # login status
        user_email,                      # user_state
        gr.update(choices=sessions, value=new_session, interactive=True),  # conversation list
        gr.update(interactive=True),     # new_chat_btn
        gr.update(interactive=True),     # rename_box
        gr.update(interactive=True),     # rename_btn
        gr.update(interactive=True),     # user_input
        "",                              # clear email_input
        ""                               # clear password_input
    )

def send_suggested_question(question, chat_hist, session_id, user_email):
    """Handle clicks on suggested question buttons. It behaves like submitting a question, but the input box is not used (it remains unchanged)."""
    for hist, inp, sess in chat_stream(question, chat_hist, session_id, user_email):
        yield hist, inp, sess

# Chat function
def chat_stream(user_query, chat_history, session_id, user_email):

    """Process user query, generate bot response, and stream it character by character. Also handles saving the conversation if the user is logged in."""

    if not user_query.strip():
        yield chat_history, ""
        return

    if chat_history is None:
        chat_history = []

    if not session_id:
        session_id = generate_session_id()

    # Append user message
    chat_history.append({"role": "user", "content": user_query})
    chat_history.append({"role": "assistant", "content": ""})
    assistant_index = len(chat_history) - 1

    # Clear input immediately
    yield chat_history, "", session_id

    # Get bot response
    bot_response, _ = answer(user_query, index, metadata, bm25)

    # Stream character by character
    for char in bot_response:
        chat_history[assistant_index]['content'] += char
        yield chat_history, "", session_id

    # Save to JSON ONLY if logged in
    if user_email and session_id:
        history_file = load_session(user_email, session_id)
        history_file["messages"].append({
            "user": user_query,
            "assistant": bot_response
        })
        save_session(user_email, session_id, history_file)



# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Assistente PT2030 / IAPMEI")

    user_state = gr.State(None)
    session_state = gr.State(None)

    with gr.Row():

        # SIDEBAR
        with gr.Column(scale=0.25):

            # 🔐 Login Section
            gr.Markdown("### 🔐 Conta")

            email_input = gr.Textbox(label="Email")
            password_input = gr.Textbox(label="Password", type="password")

            login_btn = gr.Button("Entrar / Criar Conta", variant="primary")
            login_status = gr.Markdown()

            gr.Markdown("---")

            # Conversation Section
            new_chat_btn = gr.Button("🆕 Nova Conversa", interactive=False)

            conversation_list = gr.Dropdown(
                choices=[],
                label="📂 Conversas",
                interactive=False
            )

            rename_box = gr.Textbox(
                label="✏️ Renomear Conversa",
                placeholder="Novo nome...",
                interactive=False
            )

            rename_btn = gr.Button("Guardar Nome", interactive=False)

        # CHAT AREA
        with gr.Column(scale=0.75):

            chat_history = gr.Chatbot()

            user_input = gr.Textbox(
                placeholder="Escreve a tua pergunta...",
                lines=1,
                interactive=True
            )

            gr.Markdown(
                """
                <div style="font-size: 12px; color: gray; margin-top: 10px;">
                ⚖️ As informações enviadas destinam-se exclusivamente à prestação de esclarecimentos.
                Os dados poderão ser armazenados até 180 dias para melhoria do serviço.
                Ao utilizar este assistente, aceita os termos e condições aplicáveis.
                </div>
                """
            )

            gr.Markdown("### 💡 Perguntas sugeridas")
            suggested_buttons = []

            with gr.Row():  # first row
                with gr.Column():
                    btn1 = gr.Button(SUGGESTED_QUESTIONS[0])
                    suggested_buttons.append(btn1)
                with gr.Column():
                    btn2 = gr.Button(SUGGESTED_QUESTIONS[1])
                    suggested_buttons.append(btn2)

            with gr.Row():  # second row
                with gr.Column():
                    btn3 = gr.Button(SUGGESTED_QUESTIONS[2])
                    suggested_buttons.append(btn3)
                with gr.Column():
                    btn4 = gr.Button(SUGGESTED_QUESTIONS[3])
                    suggested_buttons.append(btn4)


    for btn, question in zip(suggested_buttons, SUGGESTED_QUESTIONS):
        btn.click(
            send_suggested_question,
            inputs=[gr.State(question), chat_history, session_state, user_state],
            outputs=[chat_history, user_input, session_state],
            queue=True
        )

    # Button connections
    new_chat_btn.click(
        new_chat,
        inputs=[user_state],  # passes current logged-in user email
        outputs=[chat_history, user_input, session_state, conversation_list]
    )



    conversation_list.change(
        load_selected_session,
        inputs=[conversation_list, user_state],  # user_state included
        outputs=[chat_history, session_state]
    )

    rename_btn.click(
        rename_session,
        inputs=[rename_box, session_state, user_state],
        outputs=[conversation_list, rename_box]  # second output clears the box
    )


    user_input.submit(
        chat_stream,
        inputs=[user_input, chat_history, session_state, user_state],  # user_state included
        outputs=[chat_history, user_input],
        queue=True
    )


    login_btn.click(
        handle_login,
        inputs=[email_input, password_input],
        outputs=[
            login_status,        # Markdown
            user_state,          # State
            conversation_list,   # Dropdown
            new_chat_btn,        # Button
            rename_box,          # Textbox
            rename_btn,          # Button
            user_input,          # Chat input
            email_input,         # Clear email
            password_input       # Clear password
        ]
    )


# Launch the app
demo.launch(share=True)