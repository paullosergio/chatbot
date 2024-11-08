import asyncio
import json
from datetime import datetime
from typing import Any, Dict

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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(call_chat_api(prompt, context))
    finally:
        loop.close()


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
