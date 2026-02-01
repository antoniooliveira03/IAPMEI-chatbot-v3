import streamlit as st
import json
import os


USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def login():
    st.subheader("Inicie sessão ou crie uma conta")

    users = load_users()

    mode = st.radio("Escolha uma opção:", ["Iniciar sessão", "Criar conta"])

    with st.form("auth_form"):
        username = st.text_input("Nome de utilizador")
        password = st.text_input("Palavra-passe", type="password")
        submit_btn = st.form_submit_button("Confirmar")

        if submit_btn:
            if mode == "Iniciar sessão":
                if username in users and users[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success(f"Sessão iniciada com sucesso! Bem-vindo(a), {username}.")
                else:
                    st.error("Credenciais inválidas")
            elif mode == "Criar conta":
                if username in users:
                    st.error("Este nome de utilizador já existe. Escolha outro nome de utilizador.")
                elif not username or not password:
                    st.error("O nome de utilizador e a palavra-passe não podem estar vazias.")
                else:
                    users[username] = password
                    save_users(users)
                    st.success(f"Conta criada com sucesso para {username}. Já pode iniciar sessão.")