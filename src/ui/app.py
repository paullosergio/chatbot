import asyncio
from datetime import datetime

import httpx
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Learning Chatbot", layout="wide", initial_sidebar_state="expanded")

# Inicialização do estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "formality": "neutral",
        "language": "pt",
        "learning_mode": "active",
    }


# Função assíncrona para carregar o histórico de mensagens
async def load_chat_history() -> list:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://api:8000/chat/history", timeout=30.0)
            if response.status_code == 200:
                return response.json().get("history", [])
            else:
                st.error("Erro ao carregar histórico do chat.")
                return []
        except Exception as e:
            st.error(f"Erro ao conectar ao servidor: {e}")
            return []


# Verifica se o histórico de mensagens já foi carregado
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

# Carrega o histórico de mensagens uma única vez
if not st.session_state.history_loaded:
    chat_history = asyncio.run(load_chat_history())

    recent_history = chat_history if len(chat_history) > 10 else chat_history

    for message in reversed(recent_history):
        st.session_state.messages.append({"role": "user", "content": message["message"]})
        st.session_state.messages.append({"role": "bot", "content": message["response"]})
    st.session_state.history_loaded = True


# Função assíncrona para fazer a chamada à API
async def call_chat_api(prompt: str, context: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://api:8000/chat",
                json={"message": prompt, "context": context},
                timeout=30.0,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(e)
            return {"response": f"Erro na API: {str(e)}", "metadata": {"error": str(e)}}
        except Exception as e:
            return {"response": f"Erro na comunicação: {str(e)}", "metadata": {"error": str(e)}}


# Função para executar a chamada assíncrona
def get_chat_response(prompt: str, context: dict) -> dict:
    try:
        return asyncio.run(call_chat_api(prompt, context))  # Optimized event loop management
    except Exception as e:
        return {"response": "Erro ao processar a resposta", "metadata": {"error": str(e)}}


# Sidebar para configurações
with st.sidebar:
    st.title("Configurações")

    formality = st.select_slider(
        "Nível de Formalidade",
        options=["informal", "neutral", "formal"],
        value=st.session_state.preferences["formality"],
    )

    language = st.selectbox(
        "Idioma",
        options=["Português", "English"],
        index=0 if st.session_state.preferences["language"] == "pt" else 1,
    )

    learning_mode = st.radio(
        "Modo de Aprendizado",
        options=["Ativo", "Passivo"],
        index=0 if st.session_state.preferences["learning_mode"] == "active" else 1,
    )

    if st.button("Atualizar Preferências"):
        st.session_state.preferences.update(
            {
                "formality": formality,
                "language": "pt" if language == "Português" else "en",
                "learning_mode": "active" if learning_mode == "Ativo" else "passive",
            }
        )
        st.success("Preferências atualizadas!")

# Interface principal
st.title("🤖 Chatbot Inteligente")

# Área do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "metadata" in message:
            with st.expander("Detalhes"):
                st.json(message["metadata"])

# Input do usuário
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Chamada à API
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            context = {
                "preferences": st.session_state.preferences,
                "timestamp": datetime.now().isoformat(),
            }

            data = get_chat_response(prompt, context)

            st.write(data["response"])
            if "metadata" in data:
                with st.expander("Detalhes da Resposta"):
                    st.json(data["metadata"])

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": data["response"],
                    "metadata": data.get("metadata", {}),
                }
            )
