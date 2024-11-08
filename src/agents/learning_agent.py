from typing import Any, Dict

from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from .base_agent import AgentResponse, BaseAgent


class LearningAgent(BaseAgent):
    def __init__(self, api_key: str):
        # Initialize the ChatGroq model
        self.llm = ChatGroq(api_key=api_key, model_name="llama-3.1-70b-versatile", temperature=0.7)

        # Initialize memory
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Create chat prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "system",
                    """Consider the following context and provide a response.
                         Context: {context}
                         
                         Guidelines:
                         1. Verify any factual claims
                         2. Learn from user corrections
                         3. Maintain conversation context
                         4. Adapt tone based on user preference
                      """,
                ),
                ("human", "{user_input}"),
            ]
        )

        # Create the chain with string output parser
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self._prepare_chat_history(
                    self.memory.load_memory_variables({})["chat_history"]
                )
            )
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _prepare_chat_history(self, chat_history):
        """Convert chat history messages to strings to avoid unsupported types."""
        processed_history = []
        for message in chat_history:
            if isinstance(message, (HumanMessage, AIMessage)):
                processed_history.append(message.content)  # Extract content as string
            else:
                processed_history.append(str(message))  # Convert any other types to string
        return processed_history

    async def process(self, message: str, context: Dict[str, Any]):
        try:

            inputs = {"user_input": message, "context": context}
            print("Inputs:", inputs)  # Log inputs for debugging

            # Load chat history from memory and log it for debugging
            chat_history = self.memory.load_memory_variables({})["chat_history"]
            print("Chat History:", chat_history)  # Log chat_history for debugging

            # Run the chain
            response = await self.chain.ainvoke(inputs)
            print("Response:", response)  # Log response for debugging

            # Update memory with string messages
            self.memory.save_context({"input": message}, {"output": response})

            # Calculate confidence level
            confidence = self._calculate_confidence(context)

            return AgentResponse(
                content=response,
                confidence=confidence,
                source="learning_agent",
                metadata={
                    "context": context,
                    "language": context.get("preferences", {}).get("language", "en"),
                },
            )

        except Exception as e:
            print(f"Error in processing: {str(e)}")
            return {
                "content": "Sorry, I encountered an error processing your request.",
                "confidence": 0,
                "source": "learning_agent",
                "metadata": {"error": str(e)},
            }

    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence score based on context"""
        base_confidence = 0.9

        # Adjust confidence based on available context
        if not context.get("relevant_knowledge"):
            base_confidence *= 0.8

        # Adjust based on language preference match
        preferred_language = context.get("preferences", {}).get("language", "en")
        if preferred_language != "en":
            # Slightly lower confidence for non-English responses
            base_confidence *= 0.95

        return min(base_confidence, 1.0)  # Ensure confidence doesn't exceed 1.0
