import streamlit as st
from pathlib import Path
from chatbot import *

VECTOR_DIR = Path("data/05_vectorized")

# Page config
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Assistente PT2030 / IAPMEI")
st.caption("Chatbot baseado em documentos oficiais")

# Load index once
@st.cache_resource
def load_resources():
    return load_faiss_index(VECTOR_DIR)

index, metadata = load_resources()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_query = st.chat_input("Coloca a tua pergunta...")

if user_query:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("A pensar..."):
            response, context_chunks = answer(
                user_query,
                index,
                metadata,
                k=5
            )
            st.markdown(response)

            # Optional: show sources
            if context_chunks:
                with st.expander("📚 Fontes"):
                    for c in context_chunks:
                        st.markdown(f"- **{c['source_file']}**")

    st.session_state.messages.append({"role": "assistant", "content": response})
