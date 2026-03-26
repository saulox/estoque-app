"""
Sistema de autenticação simples via session_state do Streamlit.
Sem dependências externas — usa apenas SHA-256 e session_state.
"""
import streamlit as st
from database.connection import get_db, init_db
from database.crud_usuarios import autenticar, garantir_admin_padrao, alterar_senha_usuario
from theme import GLOBAL_CSS


def _sidebar_nav():
    with st.sidebar:
        u = st.session_state.get("usuario")
        st.markdown(f"""
        <div style="padding:12px 0 16px;">
            <div style="font-family:'Lora',serif;font-size:22px;font-weight:700;color:#e8b48a;">📦 EstoqueApp</div>
            <div style="font-size:11px;color:#9a7d65;margin-top:2px;">Almoxarifado</div>
        </div>
        <div style="background:#251a0e;border:1px solid #4a3420;border-radius:8px;
                    padding:8px 12px;margin-bottom:12px;">
            <div style="font-size:11px;color:#9a7d65;">Logado como</div>
            <div style="font-size:13px;font-weight:600;color:#e8b48a;">{u['nome'] if u else '—'}</div>
            <div style="font-size:10px;color:#6b4c2a;text-transform:uppercase;
                        letter-spacing:.08em;">{u['perfil'] if u else ''}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<div style='font-size:11px;color:#6b4c2a;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>Navegação</div>",
                    unsafe_allow_html=True)
        st.page_link("app.py",                       label="🏠  Tela Inicial")
        st.page_link("pages/1_Produtos.py",           label="📦  Produtos")
        st.page_link("pages/2_Movimentacoes.py",      label="🔄  Movimentações")
        st.page_link("pages/3_Relatorios.py",         label="📊  Relatórios")
        st.page_link("pages/4_Estoque_Financeiro.py", label="💰  Estoque Financeiro")
        st.page_link("pages/5_Alertas.py",            label="🔔  Alertas")
        st.page_link("pages/6_Notas_Servico.py",      label="🧾  Notas de Serviço")
        st.page_link("pages/9_Fornecedores.py",       label="🏭  Fornecedores")
        if u and u["perfil"] == "admin":
            st.page_link("pages/7_Configuracoes.py",  label="⚙️  Configurações")
            st.page_link("pages/0_Usuarios.py",       label="👥  Usuários")
        st.page_link("pages/8_Inventario.py",         label="📋  Inventário")
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.caption("v1.0.0 — EstoqueApp")


def requer_login(perfis_permitidos: list = None):
    """
    Decorator de proteção de página.
    Uso: chamar no topo de cada page, passa a execução adiante se autenticado.
    Retorna True se autenticado e autorizado, False caso contrário.
    """
    init_db()
    db = get_db()
    garantir_admin_padrao(db)
    db.close()

    if "usuario" not in st.session_state or not st.session_state["usuario"]:
        _tela_login()
        st.stop()

    u = st.session_state["usuario"]
    if u.get("deve_trocar_senha"):
        _tela_troca_senha_obrigatoria()
        st.stop()

    if perfis_permitidos and u["perfil"] not in perfis_permitidos:
        st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
        _sidebar_nav()
        st.error("🔒 Você não tem permissão para acessar esta página.")
        st.stop()

    return True


def _tela_login():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <style>
    .login-wrap { max-width:400px; margin:60px auto 0; }
    .login-hero { text-align:center; margin-bottom:28px; }
    .login-hero h1 { font-family:'Lora',serif; font-size:32px;
                     font-weight:700; color:#e8b48a; margin:0; }
    .login-hero p  { font-size:14px; color:#9a7d65; margin-top:6px; }
    </style>
    <div class="login-wrap">
      <div class="login-hero">
        <div style="font-size:56px;margin-bottom:8px;">📦</div>
        <h1>EstoqueApp</h1>
        <p>Sistema de Controle de Almoxarifado</p>
      </div>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("form_login"):
            login = st.text_input("Login", placeholder="seu.login")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("🔑 Entrar", use_container_width=True)
            if entrar:
                if not login or not senha:
                    st.error("Preencha login e senha.")
                else:
                    db = get_db()
                    dados_usuario = autenticar(db, login, senha)
                    db.close()
                    if dados_usuario:
                        st.session_state["usuario"] = dados_usuario
                        if dados_usuario.get("deve_trocar_senha"):
                            st.warning("Para continuar, defina uma nova senha para este usuário.")
                        st.rerun()
                    else:
                        st.error("Login ou senha incorretos.")
        st.info("Primeiro acesso: use o usuário administrador padrão e altere a senha imediatamente após entrar.")



def _tela_troca_senha_obrigatoria():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    u = st.session_state.get("usuario") or {}
    nome_usuario = u.get("nome", "Usuário")
    usuario_id = u.get("id")

    st.markdown("""
    <style>
    .login-wrap { max-width:420px; margin:60px auto 0; }
    .login-hero { text-align:center; margin-bottom:28px; }
    .login-hero h1 { font-family:'Lora',serif; font-size:30px;
                     font-weight:700; color:#e8b48a; margin:0; }
    .login-hero p  { font-size:14px; color:#9a7d65; margin-top:6px; }
    </style>
    <div class="login-wrap">
      <div class="login-hero">
        <div style="font-size:56px;margin-bottom:8px;">🔐</div>
        <h1>Troca obrigatória de senha</h1>
        <p>Olá, defina uma nova senha para continuar.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.info(f"Usuário: {nome_usuario}")

        with st.form("form_troca_senha_obrigatoria"):
            nova_senha = st.text_input("Nova senha", type="password", placeholder="Mínimo de 8 caracteres")
            confirmar_senha = st.text_input("Confirmar nova senha", type="password", placeholder="Repita a nova senha")
            salvar = st.form_submit_button("Salvar nova senha", use_container_width=True)

            if salvar:
                if not usuario_id:
                    st.error("Usuário inválido na sessão. Faça login novamente.")
                    st.session_state.clear()
                    st.stop()

                if not nova_senha or not confirmar_senha:
                    st.error("Preencha os dois campos de senha.")
                elif len(nova_senha) < 8:
                    st.error("A nova senha deve ter pelo menos 8 caracteres.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem.")
                else:
                    db = get_db()
                    try:
                        alterar_senha_usuario(db, usuario_id, nova_senha, obrigar_troca=False)
                        st.session_state["usuario"]["deve_trocar_senha"] = False
                        st.success("Senha alterada com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao alterar senha: {e}")
                    finally:
                        db.close()

        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()

def sidebar_nav():
    """Renderiza sidebar — usar em todas as pages."""
    _sidebar_nav()


def usuario_atual():
    return st.session_state.get("usuario")


def eh_admin():
    u = usuario_atual()
    return u and u["perfil"] == "admin"


def eh_operador_ou_admin():
    u = usuario_atual()
    return u and u["perfil"] in ("admin", "operador")
