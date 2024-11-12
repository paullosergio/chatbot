import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from .base_agent import AgentResponse, BaseAgent

# Configuração do logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LearningAgent(BaseAgent):
    def __init__(self, api_key: str):
        # Inicializa o modelo ChatGroq
        self.llm = ChatGroq(api_key=api_key, model_name="llama-3.1-70b-versatile", temperature=0.7)

        # Define o prompt do sistema
        system_prompt = (
            "You are an intelligent learning assistant. Use the following context and guidelines to respond accurately.\n\n"
            "Context: {context}\n\n"
            "Guidelines:\n"
            "1. **Verify Accuracy**: Ensure that all factual claims are accurate. If uncertain, respond with caution or ask for clarification if appropriate.\n"
            "2. **Learn from Corrections**: Incorporate user feedback and corrections in future responses, adjusting your understanding and approach accordingly.\n"
            "3. **Maintain Conversational Flow**: Keep track of the ongoing conversation context. Use past exchanges to enhance relevance and coherence in responses.\n"
            "4. **Adapt Tone**: Adjust your tone based on the user's formality preference, responding neutrally, formally, or informally as specified in the context.\n"
            "5. **Language Preference**: Ignore the conversation language and respect the language preferences specified in the context.\n"
            "6. **Learning Mode**: Adjust responses based on the learning mode in the user's preferences:\n"
            "   - If **active**, be proactive in offering information and clarifications.\n"
            "   - If **passive**, provide information only when explicitly asked, maintaining a more reserved approach.\n"
            "7. **Be Concise but Complete**: Deliver responses that are brief yet thorough, addressing all aspects of the user’s query without unnecessary detail.\n"
            "8. **Clarity and Simplicity**: Ensure responses are clear, especially in complex explanations. Avoid technical jargon unless relevant and appropriate.\n\n"
            "Respond thoughtfully and adaptively based on this guidance."
        )

        # Cria o grafo de estado
        self.workflow = StateGraph(state_schema=MessagesState)

        # Define a função que chama o modelo
        def call_model(state: MessagesState):
            print(state)
            messages = [
                SystemMessage(
                    content=system_prompt.format(
                        context=state.get("context", "No context provided")
                    )
                )
            ] + state["messages"]
            response = self.llm.invoke(messages)
            return {"messages": response}

        # Adiciona o nó e a aresta ao grafo
        self.workflow.add_node("model", call_model)
        self.workflow.add_edge(START, "model")

        # Adiciona o checkpointer de memória
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

    async def process(self, message: str, context: Dict[str, Any] = None):
        try:
            # Garante que o contexto não seja nulo
            if context is None:
                context = {}

            # Cria a mensagem do usuário
            user_message = HumanMessage(content=message)

            # Invoca o grafo com a mensagem do usuário e o contexto
            result = self.app.invoke(
                {"messages": [user_message], "context": context},
                config={"configurable": {"thread_id": "1"}},
            )

            # Extrai a resposta do modelo
            response_message = result["messages"][-1]
            response_content = response_message.content
            logger.info("Response: %s", response_content)  # Log da resposta para depuração

            # Calcula o nível de confiança
            confidence = self._calculate_confidence(context)

            return AgentResponse(
                content=response_content,
                confidence=confidence,
                source="learning_agent",
                metadata={
                    "context": context,
                    "language": context.get("preferences", {}).get("language", "en"),
                },
            )

        except Exception as e:
            logger.error("Error in processing: %s", str(e))
            return AgentResponse(
                content="Sorry, I encountered an error processing your request.",
                confidence=0,
                source="learning_agent",
                metadata={"error": str(e)},
            )

    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """Calcula a pontuação de confiança com base no contexto"""
        base_confidence = 0.9

        # Ajusta com base na correspondência de preferência de idioma
        preferred_language = context.get("preferences", {}).get("language", "en")
        if preferred_language != "en":
            # Confiança ligeiramente menor para respostas em idiomas diferentes do inglês
            base_confidence *= 0.95

        return min(base_confidence, 1.0)  # Garante que a confiança não exceda 1.0
