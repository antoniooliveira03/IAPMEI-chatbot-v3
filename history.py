import json
import os
from datetime import datetime


# Function to get the path for user conversation history
def get_history_path(user_id):
    os.makedirs("conversations", exist_ok=True)
    return f"conversations/{user_id}.json"

# Function to load user conversation history
def load_user_history(user_id):
    path = get_history_path(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

# Function to save user conversation history
def save_user_history(user_id, history):
    path = get_history_path(user_id)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)

# Function to start a new conversation
def start_new_conversation(user_id, title):
    history = load_user_history(user_id)
    new_convo = {
        "title": title,
        "started_at": datetime.now().isoformat(),
        "messages": []
    }
    history.append(new_convo)
    save_user_history(user_id, history)

# Function to add a message to the conversation
def add_message(user_id, role, message):
    history = load_user_history(user_id)
    if not history:
        raise Exception("No conversation started.")
    
    history[-1]["messages"].append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    save_user_history(user_id, history)
