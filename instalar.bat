@echo off
echo Instalando dependencias do EstoqueApp...
pip install streamlit pandas sqlalchemy psycopg2-binary plotly openpyxl python-dotenv reportlab
echo.
echo Instalacao concluida! Para rodar o sistema:
echo     streamlit run app.py
pause
