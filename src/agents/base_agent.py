# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentResponse(BaseModel):
    content: str
    confidence: float
    source: str
    metadata: Dict[str, Any]


class BaseAgent(ABC):
    @abstractmethod
    async def process(self, message: str, context: Dict[str, Any]) -> AgentResponse:
        pass
