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
                    """You are an intelligent learning assistant. Use the following context and guidelines to respond accurately.

                    Context: {context}
                    
                    Guidelines:
                    1. **Verify Accuracy**: Ensure that all factual claims are accurate. If uncertain, respond with caution or ask for clarification if appropriate.
                    2. **Learn from Corrections**: Incorporate user feedback and corrections in future responses, adjusting your understanding and approach accordingly.
                    3. **Maintain Conversational Flow**: Keep track of the ongoing conversation context. Use past exchanges to enhance relevance and coherence in responses.
                    4. **Adapt Tone**: Adjust your tone based on the user's formality preference, responding neutrally, formally, or informally as specified in the context.
                    5. **Language Preference**:  Ignore the conversation language and respect the language preferences specified in the context.
                    6. **Learning Mode**: Adjust responses based on the learning mode in the user's preferences:
                        - If **active**, be proactive in offering information and clarifications.
                        - If **passive**, provide information only when explicitly asked, maintaining a more reserved approach.
                    7. **Be Concise but Complete**: Deliver responses that are brief yet thorough, addressing all aspects of the user’s query without unnecessary detail.
                    8. **Clarity and Simplicity**: Ensure responses are clear, especially in complex explanations. Avoid technical jargon unless relevant and appropriate.

                    Respond thoughtfully and adaptively based on this guidance.
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

            # Run the chain
            response = await self.chain.ainvoke(inputs)
            print("Response:", response)  # Log response for debugging

            # Load updated chat history from memory and log it
            self.memory.save_context({"input": message}, {"output": response})
            chat_history = self.memory.load_memory_variables({})["chat_history"]
            print("Updated Chat History:", chat_history)  # Log updated chat_history for debugging

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

        # Adjust based on language preference match
        preferred_language = context.get("preferences", {}).get("language", "en")
        if preferred_language != "en":
            # Slightly lower confidence for non-English responses
            base_confidence *= 0.95

        return min(base_confidence, 1.0)  # Ensure confidence doesn't exceed 1.0
