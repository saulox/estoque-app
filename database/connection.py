import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# ── Lê DATABASE_URL de várias fontes ─────────────────────────────────────────
# 1. Streamlit Cloud → st.secrets
# 2. Arquivo .env local
# 3. Variável de ambiente
# 4. Fallback SQLite local (desenvolvimento)

def _get_database_url() -> str:
    """Obtém a URL do banco priorizando configuração para Supabase/PostgreSQL."""
    # Streamlit secrets (produção)
    try:
        import streamlit as st
        for key in ("DATABASE_URL", "SUPABASE_DB_URL"):
            url = st.secrets.get(key, "")
            if url:
                return url
    except Exception:
        pass

    # Arquivo .env local
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    for key in ("DATABASE_URL", "SUPABASE_DB_URL"):
        url = os.getenv(key, "")
        if url:
            return url

    # Fallback local para desenvolvimento
    return "sqlite:///estoque.db"

DATABASE_URL = _get_database_url()

# Compatibilidade com SQLAlchemy + psycopg
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# PostgreSQL / Supabase
if DATABASE_URL.startswith("postgresql"):
    connect_args = {}
    if "supabase.co" in DATABASE_URL or os.getenv("DB_SSLMODE", "require") == "require":
        connect_args["sslmode"] = os.getenv("DB_SSLMODE", "require")

    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
else:
    # SQLite — desenvolvimento local
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Retorna uma sessão do banco de dados."""
    return SessionLocal()


def _garantir_migracoes_basicas():
    """Aplica pequenas migrações compatíveis sem depender de Alembic."""
    inspector_sql = {
        "sqlite": "PRAGMA table_info(usuarios)",
        "postgresql": "SELECT column_name FROM information_schema.columns WHERE table_name = 'usuarios'",
    }
    dialect = engine.dialect.name
    sql = inspector_sql.get(dialect)
    if not sql:
        return

    with engine.begin() as conn:
        rows = conn.execute(text(sql)).fetchall()
        colunas = {row[1] if dialect == "sqlite" else row[0] for row in rows}
        if "deve_trocar_senha" not in colunas:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN deve_trocar_senha INTEGER DEFAULT 0"))
            elif dialect == "postgresql":
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS deve_trocar_senha INTEGER DEFAULT 0"))


def init_db():
    """Cria todas as tabelas no banco de dados e aplica migrações simples."""
    from database.models import Base  # noqa
    Base.metadata.create_all(bind=engine)
    _garantir_migracoes_basicas()


def testar_conexao() -> dict:
    """Testa se o banco está acessível. Útil para debug."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "tipo": "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"}
    except Exception as e:
        return {"ok": False, "erro": str(e)}
