
# Learning Chatbot API

Este projeto implementa uma API para um chatbot de aprendizado que utiliza o modelo `ChatGroq` da `langchain`. O chatbot mantém o contexto da conversa usando o `ChromaDB` para persistir o histórico das interações, permitindo que ele responda de maneira contextualizada e personalizada ao longo das sessões.

## Funcionalidades

- **Persistência do Histórico**: O histórico de conversas é armazenado no `ChromaDB`, garantindo que o chatbot mantenha o contexto entre as sessões.
- **Respostas Contextualizadas**: O chatbot responde com base no histórico de mensagens, adaptando o tom, idioma e estilo de resposta conforme as preferências do usuário.
- **Configurações Personalizadas**: O chatbot adapta-se a preferências de formalidade, idioma e modo de aprendizado.

## Tecnologias Utilizadas

- **Python**
- **FastAPI**: Para criação da API.
- **langchain**: Para processamento de linguagem e estruturação do prompt.
- **ChromaDB**: Para armazenamento persistente do histórico de conversas.
- **ChatGroq**: Modelo de linguagem utilizado para responder às mensagens do usuário.

## Estrutura do Projeto

```
project/
│
├── src/
│   ├── api/
│   │   └── app.py                # Definição da API com FastAPI e endpoints
│   │   └── instace_db.py         # Configuração do banco de dados ChromaDB
│   ├── agents/
│   │   └── learning_agent.py     # Implementação do agente de aprendizado (LearningAgent)
│   └── db/
│       └── vector_store.py       # Configuração e métodos para interação com o ChromaDB
│
├── .env                          # Arquivo para variáveis de ambiente (chave da API, etc.)
├── Dockerfile                    # Configuração do Docker para o projeto
├── docker-compose.yml            # Configuração para subir múltiplos containers
└── README.md                     # Documentação do projeto
```

## Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- Docker (opcional, se desejar rodar em contêiner)
- Variáveis de ambiente para chave da API (`GROQ_API_KEY`)

### Passos para Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/paullosergio/chatbot.git
   cd chatbot
   ```

2. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   Crie um arquivo `.env` e adicione suas configurações:
   ```
   GROQ_API_KEY=your_groq_api_key
   ```

### Execução com Docker-Compose

1. Certifique-se de que o Docker e o Docker Compose estão instalados no seu sistema.

2. Configure o arquivo .env na raiz do projeto com as variáveis necessárias:
  ```
  GROQ_API_KEY=your_groq_api_key
  ``` 

3. Execute o comando para iniciar o contêiner:
  ```
  docker-compose up -d
  ```

4. O chatbot estará disponível em http://localhost:8501.


## Endpoints da API

### `POST /chat`
Endpoint principal para envio de mensagens ao chatbot. O histórico é carregado do `ChromaDB` e incluído na resposta.

- **Parâmetros**:
  - `message` (str): A mensagem do usuário.
  - `context` (dict): Contexto adicional, incluindo preferências do usuário.

- **Exemplo de Resposta**:
  ```json
  {
    "response": "Hello! How can I help you today?",
    "metadata": {
      "context": {...},
      "language": "en"
    }
  }
  ```

### `GET /chat/history`
Retorna o histórico das últimas 10 mensagens, com ordenação pelo timestamp.

- **Exemplo de Resposta**:
  ```json
  {
    "history": [
      {
        "message": "What is your name?",
        "response": "I am your learning assistant!",
        "timestamp": "2024-11-08T12:34:56.789Z"
      },
      ...
    ]
  }
  ```

## Estrutura do Código

### `LearningAgent`
O agente principal que processa mensagens, mantém o contexto da conversa e gera respostas. As interações são salvas no `ChromaDB` para persistência de longo prazo.

- `process`: Método principal para processar uma mensagem, carregar o histórico e gerar uma resposta.
- `_prepare_chat_history`: Carrega o histórico de conversas diretamente do `ChromaDB`.
- `_calculate_confidence`: Calcula o nível de confiança da resposta com base no contexto.

### `VectorStore`
Classe responsável pela interação com o `ChromaDB`, que armazena todas as mensagens e respostas para manutenção do contexto.

## Problemas Conhecidos

- Certifique-se de que a chave da API `GROQ_API_KEY` seja válida e ativa.
