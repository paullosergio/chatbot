import os

import chromadb
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

os.environ["GROQ_API_KEY"] = config("GROQ_API_KEY")

# Configuração do ChromaDB
chroma_client = chromadb.PersistentClient(path='/root/.cache/chroma/db')
chroma_collection = chroma_client.get_or_create_collection(name="user_interactions")


class AIBot:
    def __init__(self):
        self.__chat = ChatGroq(model="llama-3.1-70b-versatile")

    def invoke(self, question):

        # Busca no ChromaDB para ver se já temos uma resposta
        results = chroma_collection.query(
            query_texts=[question], 
            n_results=1,
            where={"question": question}  # Filtra as respostas pelos metadados "question"
        )
        if any(results['documents']):
            return results['documents'][0][0]

        prompt = PromptTemplate(
            input_variables=["texto"],
            template="""
                Você é um assistente de IA especializado em traduzir textos de português para inglês.
                Sua tarefa é traduzir o seguinte texto para o inglês de forma precisa e natural:

                <texto>
                {texto}
                </texto>
                """,
        )

        # Executa o pipeline de tradução
        chain = prompt | self.__chat | StrOutputParser()
        response = chain.invoke({"texto": question})

        chroma_collection.add(
            documents=[response],
            metadatas=[{"question": question}],
            ids=[str(hash(question))],
        )

        return response
