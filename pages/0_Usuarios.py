import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db, init_db
from database.crud_usuarios import (listar_usuarios, criar_usuario,
                                     atualizar_usuario, deletar_usuario)
from database.models import PerfilUsuario
from auth import requer_login, sidebar_nav
from theme import GLOBAL_CSS

st.set_page_config(page_title="Usuários — EstoqueApp", page_icon="👥", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin"])
sidebar_nav()
init_db()
db = get_db()

st.markdown('<div class="page-header">👥 Usuários</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Gerencie o acesso ao sistema por perfil.</div>', unsafe_allow_html=True)

PERFIS = {"admin":"Admin — acesso total",
          "operador":"Operador — movimentações e consultas",
          "visualizador":"Visualizador — somente leitura"}

tab_lista, tab_novo = st.tabs(["👤 Usuários cadastrados", "➕ Novo usuário"])

with tab_lista:
    usuarios = listar_usuarios(db)
    if not usuarios:
        st.info("Nenhum usuário cadastrado.")
    else:
        for k, _ in [("edit_uid", None), ("del_uid", None)]:
            if k not in st.session_state: st.session_state[k] = None

        for u in usuarios:
            cor_perfil = {"admin":"#d4894a","operador":"#c4956a","visualizador":"#7ab87a"}.get(u.perfil.value,"#9a7d65")
            col_info, col_edit, col_del = st.columns([10, 0.7, 0.7])
            with col_info:
                st.markdown(f"""
                <div style="background:linear-gradient(145deg,#2e2010,#3a2814);
                            border:1px solid #4a3420;border-radius:10px;
                            padding:11px 16px;display:flex;align-items:center;gap:14px;">
                    <div style="width:36px;height:36px;border-radius:50%;
                                background:linear-gradient(135deg,#4a3420,#6b4c2a);
                                display:flex;align-items:center;justify-content:center;font-size:18px;">👤</div>
                    <div style="flex:1;">
                        <div style="font-weight:600;font-size:13.5px;color:#e8b48a;">{u.nome}</div>
                        <div style="font-size:11px;color:#9a7d65;">
                            @{u.login} &nbsp;·&nbsp;
                            <span style="color:{cor_perfil};font-weight:600;">{u.perfil.value.upper()}</span>
                            &nbsp;·&nbsp; {"✅ Ativo" if u.ativo else "🚫 Inativo"}
                        </div>
                    </div>
                    <div style="font-size:11px;color:#6b4c2a;text-align:right;">
                        Último acesso<br>{u.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if u.ultimo_acesso else "Nunca"}
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_edit:
                if st.button("✏️", key=f"uedit_{u.id}", use_container_width=True):
                    st.session_state.edit_uid = u.id if st.session_state.edit_uid != u.id else None
                    st.session_state.del_uid  = None
            with col_del:
                if st.button("🗑️", key=f"udel_{u.id}", use_container_width=True):
                    st.session_state.del_uid  = u.id if st.session_state.del_uid != u.id else None
                    st.session_state.edit_uid = None

            if st.session_state.edit_uid == u.id:
                with st.form(f"fedit_{u.id}"):
                    st.markdown(f"**✏️ Editando: {u.nome}**")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        enome  = st.text_input("Nome",    value=u.nome)
                        elogin = st.text_input("Login",   value=u.login)
                        esenha = st.text_input("Nova senha (deixe em branco p/ manter)",
                                               type="password", placeholder="••••")
                    with ec2:
                        eperfil = st.selectbox("Perfil",
                                   list(PERFIS.keys()),
                                   index=list(PERFIS.keys()).index(u.perfil.value),
                                   format_func=lambda x: PERFIS[x])
                        eativo = st.toggle("Usuário ativo", value=bool(u.ativo))
                    es1, es2 = st.columns(2)
                    with es1: salvar_u = st.form_submit_button("💾 Salvar", use_container_width=True)
                    with es2: fechar_u = st.form_submit_button("✖ Fechar",  use_container_width=True)
                    if salvar_u:
                        try:
                            dados = {"nome":enome,"login":elogin.strip().lower(),
                                     "perfil":eperfil,"ativo":1 if eativo else 0}
                            if esenha: dados["senha"] = esenha
                            atualizar_usuario(db, u.id, dados)
                            st.success("✅ Usuário atualizado!")
                            st.session_state.edit_uid = None
                            st.rerun()
                        except ValueError as e: st.error(f"❌ {e}")
                    if fechar_u:
                        st.session_state.edit_uid = None; st.rerun()

            if st.session_state.del_uid == u.id:
                st.markdown(f"""<div style="background:rgba(192,99,90,.1);border:1px solid rgba(192,99,90,.3);
                    border-left:3px solid #c0635a;border-radius:8px;padding:11px 16px;margin:2px 0 6px;">
                    <strong style="color:#e89a94;">Excluir usuário "{u.nome}"?</strong>
                    <span style="font-size:12px;color:#c4956a;margin-left:8px;">Esta ação não pode ser desfeita.</span>
                </div>""", unsafe_allow_html=True)
                dc1, dc2, _ = st.columns([1.4, 1.4, 7])
                with dc1:
                    if st.button("✅ Confirmar", key=f"udconf_{u.id}", use_container_width=True):
                        try:
                            deletar_usuario(db, u.id)
                            st.session_state.del_uid = None
                            st.success("🗑️ Usuário excluído.")
                            st.rerun()
                        except ValueError as e: st.error(f"❌ {e}")
                with dc2:
                    if st.button("✖ Cancelar", key=f"udcanc_{u.id}", use_container_width=True):
                        st.session_state.del_uid = None; st.rerun()

with tab_novo:
    with st.form("form_novo_user"):
        nc1, nc2 = st.columns(2)
        with nc1:
            unome  = st.text_input("Nome completo *")
            ulogin = st.text_input("Login *", placeholder="sem espaços")
        with nc2:
            usenha  = st.text_input("Senha *", type="password")
            uperfil = st.selectbox("Perfil", list(PERFIS.keys()), format_func=lambda x: PERFIS[x])
        if st.form_submit_button("➕ Criar usuário", use_container_width=True):
            try:
                criar_usuario(db, unome, ulogin, usenha, uperfil)
                st.success(f"✅ Usuário **{unome}** criado com perfil **{uperfil}**!")
                st.rerun()
            except ValueError as e: st.error(f"❌ {e}")

db.close()
