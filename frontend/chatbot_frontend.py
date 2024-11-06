import streamlit as st
import requests
from datetime import datetime
from backend.bot import chroma_collection

# Configuração básica do título e cabeçalho
st.set_page_config(page_title="Chatbot", layout="centered")
st.title("🤖 Chatbot")

# Configura o histórico da conversa para armazenar as mensagens
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Função para enviar a pergunta ao backend Flask
def get_bot_response(question):
    # url = "http://backend:5000/"
    url = "http://localhost:5000/"
    payload = {"question": question}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("answer", "Erro na resposta")
        else:
            return "Erro ao se comunicar com o backend"
    except requests.exceptions.RequestException as e:
        return f"Erro na requisição: {e}"

# Função para buscar o histórico no ChromaDB
def fetch_chat_history_from_chromadb():

    # Consulta ao ChromaDB para buscar o histórico
    results = chroma_collection.query(query_texts=[""], n_results=100)
    
    # Processa os resultados e armazena no histórico de sessão
    if results["metadatas"] and results["documents"]:
        for i in range(len(results["metadatas"][0])):
            user_message = results["metadatas"][0][i]["question"]
            bot_response = results["documents"][0][i]
            timestamp = datetime.now().strftime("%H:%M")  # Pode substituir pela data real se disponível
            
            # Adiciona a mensagem do usuário e a resposta do bot ao histórico
            st.session_state.chat_history.append({
                "message": user_message,
                "is_user": True,
                "timestamp": timestamp
            })
            st.session_state.chat_history.append({
                "message": bot_response,
                "is_user": False,
                "timestamp": timestamp
            })

# Busca o histórico do ChromaDB apenas uma vez no início
if "initialized" not in st.session_state:
    fetch_chat_history_from_chromadb()
    st.session_state.initialized = True

# Entrada do usuário
user_message = st.text_input("Digite sua mensagem e pressione Enter:")

# Envia a pergunta e armazena no histórico
if user_message:
    # Armazena a mensagem do usuário
    st.session_state.chat_history.append({
        "message": user_message,
        "is_user": True,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    # Recebe a resposta do chatbot
    bot_response = get_bot_response(user_message)
    st.session_state.chat_history.append({
        "message": bot_response,
        "is_user": False,
        "timestamp": datetime.now().strftime("%H:%M")
    })

# Exibe o histórico da conversa
for chat in st.session_state.chat_history:
    if chat["is_user"]:
        # Exibe a mensagem do usuário alinhada à direita
        st.markdown(
            f'<div style="text-align: right; padding: 8px; background-color: #aec999; border-radius: 8px; margin-bottom: 5px;">'
            f'<b>Você:</b> {chat["message"]}<br><small>{chat["timestamp"]}</small></div>',
            unsafe_allow_html=True,
        )
    else:
        # Exibe a resposta do bot alinhada à esquerda
        st.markdown(
            f'<div style="text-align: left; background-color: #98fb98; color: black; padding: 8px; border-radius: 8px; margin-bottom: 5px;">'
            f'<b>Bot:</b> {chat["message"]}<br><small>{chat["timestamp"]}</small></div>',
            unsafe_allow_html=True,
        )
