# src/api/main.py
import os
from typing import Any, Dict, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agents.learning_agent import LearningAgent
from src.db.vector_store import VectorStore

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


# Initialize services
vector_store = VectorStore(
    host=os.getenv("CHROMADB_HOST", "localhost"),
    port=int(os.getenv("CHROMADB_PORT", 8000)),
)
agent = LearningAgent(api_key=os.getenv("GROQ_API_KEY"))

@app.get("/")
async def root():
    print("oi")
    return {"message": "Hello World"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Search for relevant knowledge
        knowledge = await vector_store.search_knowledge(request.message)

        # Add knowledge to context
        context = {**request.context, "relevant_knowledge": knowledge}

        # Process message
        response = await agent.process(request.message, context)

        # Store interaction
        await vector_store.add_interaction(
            text=request.message,
            metadata={
                "response": response.content,
                "confidence": response.confidence,
                "source": response.source,
            },
        )

        return ChatResponse(response=response.content, metadata=response.metadata)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
