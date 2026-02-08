import streamlit as st
from pathlib import Path
from streamlit_option_menu import option_menu

import login as l
import history as h
from chatbot import load_faiss_index, answer, build_bm25

# ---------------- Config ----------------

SUGGESTED_QUESTIONS = [
    "O que é o PT2030?",
    "Qual é o objetivo principal do Programa Algarve 2030?",
    "Como as empresas podem obter a certificação PME?",
    "Qual é a diferença entre o PT2030, IAPMEI e Compete 2030?",
    "Como funciona o processo de candidatura a incentivos do PT2030?",
]


VECTOR_DIR = Path("data/05_vectorized/large")

st.set_page_config(
    page_title="PT2030 Chatbot | IAPMEI",
    page_icon="🤖",
    layout="wide"
)

# ---------------- Load RAG resources ----------------

@st.cache_resource
def load_resources():
    return load_faiss_index(VECTOR_DIR)

index, metadata = load_resources()
bm25 = build_bm25(metadata)

# ---------------- Session state ----------------

if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "PT2030 Chatbot"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_convo_idx" not in st.session_state:
    st.session_state.selected_convo_idx = 0

# Logged user
user_id = st.session_state.get("username")

# ---------------- Top Menu ----------------

selected = option_menu(
    menu_title=None,
    options=["PT2030 Chatbot", "Iniciar Sessão"],
    icons=["robot", "person"],
    orientation="horizontal",
    default_index=["PT2030 Chatbot", "Iniciar Sessão"].index(st.session_state.selected_tab)
)

if selected != st.session_state.selected_tab:
    st.session_state.selected_tab = selected
    st.rerun()

# ==================================================
# ===================== CHAT =======================
# ==================================================

# Define the user ID
user_id = st.session_state.get("username")

if st.session_state.selected_tab == "PT2030 Chatbot":

    st.title("🤖 Assistente PT2030 / IAPMEI")
    st.caption("Chatbot baseado em documentos oficiais (RAG)")

    # ---------- Sidebar: Suggested Questions ----------

    with st.sidebar:
        st.header("💡 Perguntas sugeridas")

        for q in SUGGESTED_QUESTIONS:
            if st.button(q, key=f"suggested_{q}"):
                st.session_state.pending_question = q


    # ---------- Conversation selector ----------

    selected_convo_idx = st.session_state.selected_convo_idx

    if user_id:
        conversations = h.load_user_history(user_id)
        options = [c["title"] for c in conversations] if conversations else []
        options = ["Nova conversa"] + options

        selected_option = st.selectbox(
            "Escolha uma conversa:",
            options=range(len(options)),
            format_func=lambda i: options[i],
            index=selected_convo_idx
        )

        # ---- NEW CONVERSATION ----
        if selected_option == 0:
            if selected_convo_idx == 0 and conversations and conversations[-1]["messages"] == []:
                pass
            else:
                h.start_new_conversation(
                    user_id,
                    f"Conversa {len(conversations) + 1}"
                )
                conversations = h.load_user_history(user_id)
                st.session_state.selected_convo_idx = len(conversations)
                st.session_state.messages = []
                st.rerun()

        # ---- EXISTING CONVERSATION ----
        else:
            st.session_state.selected_convo_idx = selected_option
            convo_idx = selected_option - 1

            convo = conversations[convo_idx]
            st.session_state.messages = convo["messages"]

            # Rename
            current_title = convo["title"]
            new_title = st.text_input(
                "Mudar o nome da conversa:",
                value=current_title,
                key=f"rename_convo_{selected_option}"
            )

            if new_title.strip() and new_title != current_title:
                conversations[convo_idx]["title"] = new_title.strip()
                h.save_user_history(user_id, conversations)
                st.rerun()

            # Delete
            if st.button("Eliminar esta conversa", key=f"delete_convo_{selected_option}"):
                del conversations[convo_idx]
                h.save_user_history(user_id, conversations)
                st.session_state.selected_convo_idx = 0
                st.session_state.messages = []
                st.rerun()
    else:
        st.info("🔐 Inicia sessão para guardar o histórico das conversas.")

    # ---------- Display chat history ----------

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ---------- Chat input ----------
    user_query = st.chat_input("Coloca a tua pergunta...")

    # Use suggested question if clicked
    if "pending_question" in st.session_state:
        user_query = st.session_state.pop("pending_question")

    if user_query:
        st.session_state.messages.append(
            {"role": "user", "content": user_query}
        )

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("A pensar..."):
                response, context_chunks = answer(
                    user_query,
                    index,
                    metadata,
                    bm25
                )
                st.markdown(response)

                if context_chunks:
                    with st.expander("📚 Fontes"):
                        for c in context_chunks:
                            st.markdown(f"- **{c['source_file']}**")

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

        # Save history
        if user_id and st.session_state.selected_convo_idx > 0:
            conversations = h.load_user_history(user_id)
            conversations[
                st.session_state.selected_convo_idx - 1
            ]["messages"] = st.session_state.messages
            h.save_user_history(user_id, conversations)

# ==================================================
# ===================== LOGIN ======================
# ==================================================

elif st.session_state.selected_tab == "Iniciar Sessão":
    l.login()
