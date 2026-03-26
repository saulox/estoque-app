#!/bin/bash
echo "Instalando dependências do EstoqueApp..."
pip install streamlit pandas sqlalchemy psycopg2-binary plotly openpyxl python-dotenv reportlab
echo ""
echo "Instalação concluída! Para rodar:"
echo "    streamlit run app.py"
