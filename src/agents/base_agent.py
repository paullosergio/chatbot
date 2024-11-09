from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, validator


class AgentResponse(BaseModel):
    """
    A standardized response format for all agents.

    Attributes:
        content (str): The response content.
        confidence (float): Confidence level of the response.
        source (str): Source identifier of the agent.
        metadata (Dict[str, Any]): Additional metadata.
    """

    content: str = Field(..., description="The content of the agent's response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level between 0 and 1")
    source: str
    metadata: Dict[str, Any]

    @field_validator("confidence")
    def validate_confidence(cls, value):
        if not (0 <= value <= 1):
            raise ValueError("Confidence must be between 0 and 1")
        return value


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Methods:
        process (str, Dict[str, Any]) -> AgentResponse: Processes a message with context and returns a response.
    """

    @abstractmethod
    async def process(self, message: str, context: Dict[str, Any]) -> AgentResponse:
        pass
