import os
from typing import Any, Dict, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.agents.learning_agent import LearningAgent

from .instace_db import vector_store

load_dotenv()

app = FastAPI(title="Learning Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    response: str
    metadata: Dict[str, Any]


# Memory for conversation history
conversation_history = []

agent = LearningAgent(api_key=os.getenv("GROQ_API_KEY"))


@app.get("/")
async def root():
    return vector_store.interaction_collection.query(query_texts=[""], n_results=100)


@app.get("/chat/history")
async def get_chat_history():
    try:

        results = vector_store.interaction_collection.query(query_texts=[""], n_results=100)

        history = sorted(
            [
                {
                    "message": item["document"],
                    "response": item["metadata"]["response"],
                    "timestamp": item["metadata"].get("timestamp"),
                }
                for item in vector_store._format_results(results)
            ],
            key=lambda x: x["timestamp"],
            reverse=True,
        )

        return JSONResponse(content={"history": history})
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Buscar interações anteriores com base na similaridade
        results = vector_store.interaction_collection.query(
            query_texts=[request.message], n_results=4
        )

        # Verifica se há resultados e filtra as interações relevantes
        relevant_interactions = (
            [res for res in vector_store._format_results(results) if res["distance"] < 0.6]
            if results["ids"][0]
            else []
        )

        # Constrói o contexto a partir de interações relevantes, se houver
        additional_context = (
            {"previous_responses": [item["metadata"]["response"] for item in relevant_interactions]}
            if relevant_interactions
            else {}
        )

        # Processa a mensagem usando o agente, passando o contexto adicional, se houver
        agent_response = await agent.process(
            request.message, {**request.context, **additional_context}
        )

        # Usa a resposta do agente como a principal resposta
        response_content = agent_response.content

        # Armazena a interação para análise futura
        await vector_store.add_interaction(
            text=request.message,
            metadata={"response": response_content, "source": "user_interaction"},
        )

        return ChatResponse(response=response_content, metadata=agent_response.metadata)
    except Exception as e:
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
