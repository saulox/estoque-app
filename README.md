# 📦 EstoqueApp — Sistema de Controle de Almoxarifado

Sistema web completo para controle de almoxarifado com Streamlit + PostgreSQL.

---

## 🚀 Deploy no Streamlit Cloud (produção)

### 1. Banco de dados — Supabase
1. Crie um projeto em **supabase.com**
2. Vá em **Settings → Database → URI** e copie a connection string
3. Guarde a string — usará no passo 3

### 2. GitHub
```bash
git init
git add .
git commit -m "EstoqueApp v1.0"
git remote add origin https://github.com/SEU-USUARIO/estoqueapp.git
git push -u origin main
```

### 3. Streamlit Cloud
1. Acesse **share.streamlit.io** → "New app"
2. Selecione o repositório → branch `main` → arquivo `app.py`
3. Clique em **"Advanced settings"** → **Secrets** → cole:
```toml
DATABASE_URL = "postgresql://postgres:SENHA@db.CODIGO.supabase.co:5432/postgres"
```
4. Clique em **Deploy** ✅

### Primeiro acesso
- Use o usuário administrador padrão criado pelo sistema no primeiro boot
- **Troque a senha imediatamente após entrar**

---

## 💻 Rodar localmente (desenvolvimento)

```bash
# Windows
instalar.bat

# Linux/Mac
chmod +x instalar.sh && ./instalar.sh

# Rodar
streamlit run app.py
```

Para usar SQLite local (sem configurar banco):
```bash
# Não precisa fazer nada — SQLite é criado automaticamente
streamlit run app.py
```

Para usar Supabase localmente ou em produção, crie `.env` ou configure em `.streamlit/secrets.toml`:
```
DATABASE_URL=postgresql://postgres:SUA-SENHA@db.PROJETO.supabase.co:5432/postgres
```

Também é aceito:
```
SUPABASE_DB_URL=postgresql://postgres:SUA-SENHA@db.PROJETO.supabase.co:5432/postgres
```

---

## 📁 Estrutura

```
estoque/
├── app.py                    # Dashboard principal
├── auth.py                   # Login e controle de acesso
├── theme.py                  # Tema visual marrom
├── gerar_pdf_nota.py         # PDF de notas de serviço
├── gerar_pdf_pedido.py       # PDF de pedidos de compra
├── pages/
│   ├── 0_Usuarios.py         # Gestão de usuários (admin)
│   ├── 1_Produtos.py         # Cadastro de produtos
│   ├── 2_Movimentacoes.py    # Entradas e saídas
│   ├── 3_Relatorios.py       # Gráficos e exportação
│   ├── 4_Estoque_Financeiro.py
│   ├── 5_Alertas.py          # Alertas de estoque
│   ├── 6_Notas_Servico.py    # Notas de serviço em PDF
│   ├── 7_Configuracoes.py    # Config empresa + alertas
│   ├── 8_Inventario.py       # Contagem física
│   └── 9_Fornecedores.py     # Fornecedores e pedidos de compra
├── database/
│   ├── models.py             # Tabelas (SQLAlchemy)
│   ├── crud.py               # Operações de estoque
│   ├── crud_notas.py         # Operações de notas
│   ├── crud_usuarios.py      # Operações de usuários
│   └── crud_fornecedores.py  # Operações de fornecedores
├── alertas/
│   ├── notificador.py        # Engine de alertas
│   ├── whatsapp.py           # Evolution API
│   └── email_smtp.py         # Gmail SMTP
├── static/
│   ├── manifest.json         # PWA
│   └── sw.js                 # Service Worker
├── requirements.txt
└── .streamlit/
    └── config.toml           # Tema e configurações


## Segurança

- No primeiro login do usuário `admin`, o sistema exige a troca da senha padrão antes de liberar acesso às páginas.
- Em produção, configure `DATABASE_URL` apontando para o banco PostgreSQL do Supabase com SSL habilitado.

## Deploy no Streamlit Cloud

1. Suba este projeto para um repositório Git.
2. No Streamlit Cloud, configure o app apontando para `app.py`.
3. Em **Secrets**, informe:

```toml
DATABASE_URL = "postgresql://postgres:SUA-SENHA@db.PROJETO.supabase.co:5432/postgres"
DB_SSLMODE = "require"
```

4. O arquivo `requirements.txt` já está revisado para deploy no Streamlit Cloud.
