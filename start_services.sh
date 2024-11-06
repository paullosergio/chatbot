#!/bin/bash

# Inicia o backend Flask em segundo plano
poetry run python backend/app.py &

# Inicia o frontend Streamlit
poetry run streamlit run frontend/chatbot_frontend.py --server.port=8501 --server.address=0.0.0.0
