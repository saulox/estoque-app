import streamlit as st
import pandas as pd
from io import BytesIO
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db, init_db
from database.crud_fornecedores import (
    listar_fornecedores, criar_fornecedor, atualizar_fornecedor, deletar_fornecedor,
    listar_pedidos, criar_pedido, atualizar_status_pedido, deletar_pedido, buscar_pedido
)
from database.models import StatusPedido
from database import crud
from auth import requer_login, sidebar_nav
from theme import GLOBAL_CSS
from gerar_pdf_pedido import gerar_pdf_pedido

st.set_page_config(page_title="Fornecedores — EstoqueApp", page_icon="🏭", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin","operador"])
sidebar_nav()
init_db()
db = get_db()

for k in ["forn_edit","forn_del","ped_edit","ped_del"]:
    if k not in st.session_state: st.session_state[k] = None
if "itens_pedido" not in st.session_state: st.session_state.itens_pedido = []

st.markdown('<div class="page-header">🏭 Fornecedores & Pedidos de Compra</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Gerencie fornecedores e emita pedidos de compra com entrada automática no estoque.</div>', unsafe_allow_html=True)

tab_forn, tab_pedidos, tab_novo_ped = st.tabs(["🏭 Fornecedores", "📋 Pedidos de Compra", "➕ Novo Pedido"])

STATUS_COR = {
    "pendente":  ("#d4a843","#3d2a10"),
    "enviado":   ("#3498db","#0a2030"),
    "recebido":  ("#7ab87a","#1a2e1a"),
    "cancelado": ("#c0635a","#2d0f0f"),
}

def badge_status(s):
    cor, bg = STATUS_COR.get(s,("#9a7d65","#2e2010"))
    return f'<span style="background:{bg};color:{cor};border:1px solid {cor}55;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;">{s.upper()}</span>'

# ══ Fornecedores ══════════════════════════════════════════════════════════════
with tab_forn:
    fornecedores = listar_fornecedores(db)
    busca_f = st.text_input("Busca", placeholder="🔍  Buscar fornecedor...", label_visibility="collapsed", key="bf")
    if busca_f.strip():
        fornecedores = [f for f in fornecedores if busca_f.lower() in f.nome.lower()]

    if not fornecedores:
        st.info("Nenhum fornecedor cadastrado.")
    else:
        for f in fornecedores:
            col_c, col_e, col_d = st.columns([11,0.6,0.6])
            with col_c:
                st.markdown(f"""
                <div style="background:linear-gradient(145deg,#2e2010,#3a2814);
                            border:1px solid #4a3420;border-radius:10px;
                            padding:11px 16px;display:flex;align-items:center;gap:12px;">
                    <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#4a3420,#6b4c2a);
                                display:flex;align-items:center;justify-content:center;font-size:18px;">🏭</div>
                    <div style="flex:1;">
                        <div style="font-weight:600;font-size:13.5px;color:#e8b48a;">{f.nome}</div>
                        <div style="font-size:11px;color:#9a7d65;">
                            {f"CNPJ: {f.cnpj} &nbsp;·&nbsp;" if f.cnpj else ""}
                            {f.telefone or ""} &nbsp;·&nbsp; {f.email or "—"}
                        </div>
                    </div>
                    <div style="font-size:11px;color:#6b4c2a;">{len(f.pedidos)} pedido(s)</div>
                </div>""", unsafe_allow_html=True)
            with col_e:
                if st.button("✏️", key=f"fe_{f.id}", use_container_width=True):
                    st.session_state.forn_edit = f.id if st.session_state.forn_edit != f.id else None
                    st.session_state.forn_del  = None
            with col_d:
                if st.button("🗑️", key=f"fd_{f.id}", use_container_width=True):
                    st.session_state.forn_del  = f.id if st.session_state.forn_del != f.id else None
                    st.session_state.forn_edit = None

            if st.session_state.forn_edit == f.id:
                with st.form(f"ffed_{f.id}"):
                    st.markdown(f"**✏️ Editando: {f.nome}**")
                    fe1, fe2 = st.columns(2)
                    with fe1:
                        enome  = st.text_input("Nome *",    value=f.nome)
                        ecnpj  = st.text_input("CNPJ",      value=f.cnpj or "")
                        econ   = st.text_input("Contato",   value=f.contato or "")
                    with fe2:
                        etel   = st.text_input("Telefone",  value=f.telefone or "")
                        eemail = st.text_input("E-mail",    value=f.email or "")
                        eend   = st.text_input("Endereço",  value=f.endereco or "")
                    eobs = st.text_area("Observação", value=f.observacao or "")
                    fs1, fs2 = st.columns(2)
                    with fs1: sv = st.form_submit_button("💾 Salvar",  use_container_width=True)
                    with fs2: fc = st.form_submit_button("✖ Fechar",   use_container_width=True)
                    if sv:
                        try:
                            atualizar_fornecedor(db, f.id, {"nome":enome,"cnpj":ecnpj,"contato":econ,
                                                             "telefone":etel,"email":eemail,"endereco":eend,"observacao":eobs})
                            st.success("✅ Fornecedor atualizado!"); st.session_state.forn_edit=None; st.rerun()
                        except ValueError as e: st.error(f"❌ {e}")
                    if fc: st.session_state.forn_edit=None; st.rerun()

            if st.session_state.forn_del == f.id:
                st.markdown(f"""<div style="background:rgba(192,99,90,.1);border:1px solid rgba(192,99,90,.3);
                    border-left:3px solid #c0635a;border-radius:8px;padding:11px 16px;margin:2px 0 6px;">
                    <strong style="color:#e89a94;">Excluir "{f.nome}"?</strong>
                </div>""", unsafe_allow_html=True)
                xc1, xc2, _ = st.columns([1.2,1.2,8])
                with xc1:
                    if st.button("✅ Sim", key=f"fdconf_{f.id}", use_container_width=True):
                        try: deletar_fornecedor(db, f.id); st.session_state.forn_del=None; st.rerun()
                        except ValueError as e: st.error(f"❌ {e}")
                with xc2:
                    if st.button("✖ Não", key=f"fdcanc_{f.id}", use_container_width=True):
                        st.session_state.forn_del=None; st.rerun()

    st.markdown('<div class="section-title">➕ Cadastrar Fornecedor</div>', unsafe_allow_html=True)
    with st.form("form_novo_forn"):
        nf1, nf2 = st.columns(2)
        with nf1:
            fnome  = st.text_input("Nome *")
            fcnpj  = st.text_input("CNPJ")
            fcon   = st.text_input("Contato")
        with nf2:
            ftel   = st.text_input("Telefone")
            femail = st.text_input("E-mail")
            fend   = st.text_input("Endereço")
        fobs = st.text_area("Observação")
        if st.form_submit_button("➕ Cadastrar", use_container_width=True):
            try:
                criar_fornecedor(db, {"nome":fnome,"cnpj":fcnpj,"contato":fcon,
                                       "telefone":ftel,"email":femail,"endereco":fend,"observacao":fobs})
                st.success(f"✅ Fornecedor **{fnome}** cadastrado!"); st.rerun()
            except ValueError as e: st.error(f"❌ {e}")

# ══ Pedidos de Compra ══════════════════════════════════════════════════════════
with tab_pedidos:
    pf1, pf2 = st.columns(2)
    with pf1:
        f_status = st.selectbox("Status", ["Todos","pendente","enviado","recebido","cancelado"],
                                 format_func=lambda x: x.capitalize(), key="ps")
    with pf2:
        forns = listar_fornecedores(db)
        fmap  = {"Todos os fornecedores": None}
        fmap.update({f.nome: f.id for f in forns})
        f_forn = st.selectbox("Fornecedor", list(fmap.keys()), key="pf")

    pedidos = listar_pedidos(db,
                              status=f_status if f_status != "Todos" else None,
                              fornecedor_id=fmap[f_forn])

    if not pedidos:
        st.info("Nenhum pedido encontrado.")
    else:
        for p in pedidos:
            pc1, pc2, pc3 = st.columns([10, 0.7, 0.7])
            with pc1:
                st.markdown(f"""
                <div style="background:linear-gradient(145deg,#2e2010,#3a2814);
                            border:1px solid #4a3420;border-radius:10px;
                            padding:11px 16px;display:flex;align-items:center;gap:12px;">
                    <div style="flex:1;">
                        <div style="font-weight:600;font-size:13px;color:#e8b48a;">
                            {p.numero_formatado} &nbsp;·&nbsp; {p.fornecedor.nome}
                        </div>
                        <div style="font-size:11px;color:#9a7d65;">
                            {p.criado_em.strftime('%d/%m/%Y')} &nbsp;·&nbsp;
                            {len(p.itens)} item(ns) &nbsp;·&nbsp;
                            Total: R$ {p.total:,.2f}
                        </div>
                    </div>
                    {badge_status(p.status.value)}
                </div>""", unsafe_allow_html=True)
            with pc2:
                try:
                    from gerar_pdf_pedido import gerar_pdf_pedido as gpdf
                    pdf = gpdf(p)
                    st.download_button("📄", data=pdf,
                                       file_name=f"{p.numero_formatado}.pdf",
                                       mime="application/pdf",
                                       key=f"ppdf_{p.id}", use_container_width=True,
                                       help="Baixar PDF")
                except Exception:
                    st.markdown("📄", unsafe_allow_html=True)
            with pc3:
                if st.button("✏️", key=f"ped_{p.id}", use_container_width=True):
                    st.session_state.ped_edit = p.id if st.session_state.ped_edit != p.id else None

            if st.session_state.ped_edit == p.id:
                st.markdown(f"**Pedido {p.numero_formatado} — alterar status**")
                opcoes = ["pendente","enviado","recebido","cancelado"]
                novo_s = st.selectbox("Novo status", opcoes,
                                       index=opcoes.index(p.status.value),
                                       key=f"ps_{p.id}",
                                       format_func=lambda x: x.capitalize())
                if novo_s == "recebido":
                    st.warning("⚠️ Ao marcar como **Recebido**, os itens vinculados a produtos darão entrada automática no estoque.")
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("✅ Confirmar status", key=f"psc_{p.id}", use_container_width=True):
                        try:
                            atualizar_status_pedido(db, p.id, novo_s)
                            st.session_state.ped_edit = None
                            st.success(f"✅ Pedido {p.numero_formatado} → {novo_s.upper()}")
                            st.rerun()
                        except ValueError as e: st.error(f"❌ {e}")
                with ec2:
                    if st.button("✖ Fechar", key=f"psf_{p.id}", use_container_width=True):
                        st.session_state.ped_edit = None; st.rerun()

# ══ Novo Pedido ════════════════════════════════════════════════════════════════
with tab_novo_ped:
    forns2 = listar_fornecedores(db)
    if not forns2:
        st.warning("⚠️ Cadastre um fornecedor primeiro.")
    else:
        fmap2 = {f.nome: f.id for f in forns2}
        produtos_all = crud.listar_produtos(db)

        col_np1, col_np2 = st.columns(2)
        with col_np1:
            forn_sel = st.selectbox("Fornecedor *", list(fmap2.keys()), key="nps")
        with col_np2:
            obs_ped  = st.text_input("Observação do pedido", key="npobs")

        st.markdown('<div class="section-title">➕ Adicionar itens</div>', unsafe_allow_html=True)
        with st.form("form_item_ped", clear_on_submit=True):
            pi1, pi2 = st.columns([3, 2])
            with pi1:
                desc_it = st.text_input("Descrição / produto *",
                                         placeholder="Ex: Tecido branco, Parafuso M6...")
            with pi2:
                prod_map = {"(sem vínculo)": None}
                prod_map.update({p.nome: p.id for p in produtos_all})
                prod_sel = st.selectbox("Vincular ao produto do estoque", list(prod_map.keys()), key="pip")

            pi3, pi4, pi5 = st.columns([1.2, 1, 1.5])
            with pi3:
                qtd_it  = st.number_input("Quantidade", min_value=0.01, value=1.0, step=1.0)
            with pi4:
                un_it   = st.text_input("Unidade", value="un",
                                         help="un · kg · g · L · ml · cx · pç · m")
            with pi5:
                preco_it = st.number_input("Preço unit.", min_value=0.0, value=0.0, format="%.2f")
            add_it = st.form_submit_button("➕ Adicionar item", use_container_width=True)
            if add_it and desc_it.strip():
                st.session_state.itens_pedido.append({
                    "descricao": desc_it.strip(),
                    "produto_id": prod_map[prod_sel],
                    "quantidade": qtd_it,
                    "unidade": un_it,
                    "preco_unit": preco_it,
                })
                st.rerun()

        if st.session_state.itens_pedido:
            dados_it = [{"#":i+1,"Descrição":it["descricao"],
                          "Produto vinculado": next((p.nome for p in produtos_all if p.id==it["produto_id"]),"—"),
                          "Qtd":f"{it['quantidade']:g}","Un":it["unidade"],
                          "Preço Unit.":f"R$ {it['preco_unit']:.2f}",
                          "Total":f"R$ {it['quantidade']*it['preco_unit']:.2f}"}
                         for i,it in enumerate(st.session_state.itens_pedido)]
            st.dataframe(pd.DataFrame(dados_it), use_container_width=True, hide_index=True)
            total_ped = sum(it["quantidade"]*it["preco_unit"] for it in st.session_state.itens_pedido)
            st.markdown(f"**Total do pedido: R$ {total_ped:,.2f}**")

            c_salvar, c_limpar = st.columns(2)
            with c_salvar:
                if st.button("✅ Criar Pedido de Compra", use_container_width=True, type="primary"):
                    try:
                        p = criar_pedido(db, fmap2[forn_sel],
                                         st.session_state.itens_pedido, obs_ped)
                        st.session_state.itens_pedido = []
                        st.success(f"✅ Pedido **{p.numero_formatado}** criado!")
                        st.rerun()
                    except ValueError as e: st.error(f"❌ {e}")
            with c_limpar:
                if st.button("🗑️ Limpar itens", use_container_width=True):
                    st.session_state.itens_pedido = []; st.rerun()

db.close()
