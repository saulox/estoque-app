import streamlit as st
import pandas as pd
from database.connection import get_db
from database import crud
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS

st.set_page_config(page_title="Produtos — EstoqueApp", page_icon="📦", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador"])
sidebar_nav()

st.markdown("""
<style>
.prod-grid { display:flex; flex-direction:column; gap:6px; margin-top:4px; }
.prod-row {
    background:linear-gradient(145deg,#2e2010,#3a2814);
    border:1px solid #4a3420; border-radius:10px;
    padding:11px 14px;
    display:flex; align-items:center; gap:12px;
    transition:border-color .18s, box-shadow .18s;
}
.prod-row:hover { border-color:#8b5e3c; box-shadow:0 2px 10px rgba(139,94,60,.2); }
.prod-row-icon {
    width:36px; height:36px; border-radius:8px; flex-shrink:0;
    background:linear-gradient(135deg,#4a3420,#6b4c2a);
    display:flex; align-items:center; justify-content:center; font-size:16px;
}
.prod-row-name { font-weight:600; font-size:13.5px; color:#e8b48a; line-height:1.2; }
.prod-row-meta { font-size:11px; color:#9a7d65; margin-top:1px; }
.prod-row-qty  { font-family:'Inconsolata',monospace; font-size:13px; color:#c4956a;
                 flex-shrink:0; min-width:80px; text-align:right; margin-left:auto; }
.badge-ok  { background:rgba(122,184,122,.12); color:#7ab87a;
             border:1px solid rgba(122,184,122,.28); border-radius:4px;
             font-size:10px; font-weight:700; padding:2px 7px; flex-shrink:0; }
.badge-low { background:rgba(212,168,67,.12); color:#d4a843;
             border:1px solid rgba(212,168,67,.28); border-radius:4px;
             font-size:10px; font-weight:700; padding:2px 7px; flex-shrink:0; }
.edit-panel {
    background:linear-gradient(135deg,#251a0e,#2e2010);
    border:1px solid #6b4c2a; border-left:3px solid #d4894a;
    border-radius:10px; padding:20px; margin:4px 0 8px 0;
}
/* botões caneta/lixeira compactos */
button[kind="secondary"] { min-height:36px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

db = get_db()
UNIDADES = ["un", "kg", "g", "L", "ml", "cx", "pç", "m", "m²"]
EMOJI_CAT = {"Alimentos":"🍎","Bebidas":"🥤","Limpeza":"🧹","Eletrônicos":"💻",
             "Roupas":"👕","Calçados":"👟","Ferramentas":"🔧","Papelaria":"📝",
             "Acessórios":"💍","Cosméticos":"💄","Médico":"💊","Outros":"📦"}

# ─── Session state ────────────────────────────────────────────────────────────
for k in ["prod_edit_id","prod_del_id"]:
    if k not in st.session_state: st.session_state[k] = None

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-header">📦 Produtos</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Gerencie o cadastro de produtos e categorias do seu estoque.</div>', unsafe_allow_html=True)

tab_lista, tab_inativos, tab_cadastro, tab_categorias = st.tabs([
    "📋 Ativos", "🚫 Inativos", "➕ Cadastrar", "🏷️ Categorias"
])

# ══════════════════════════════════════════════════════════════
# ABA: PRODUTOS ATIVOS
# ══════════════════════════════════════════════════════════════
with tab_lista:
    categorias = crud.listar_categorias(db)
    opcoes_cat = {c.nome: c.id for c in categorias}

    # ── Barra de pesquisa + filtro lado a lado ────────────────
    sc1, sc2 = st.columns([3, 2])
    with sc1:
        busca = st.text_input("Busca", placeholder="🔍  Buscar por nome do produto...",
                              label_visibility="collapsed", key="busca_prod")
    with sc2:
        filtro_cat = st.selectbox("Categoria", ["📂  Todas as categorias"] + list(opcoes_cat.keys()),
                                  label_visibility="collapsed", key="fc_ativo")

    cat_id   = opcoes_cat.get(filtro_cat) if not filtro_cat.startswith("📂") else None
    produtos = crud.listar_produtos(db, categoria_id=cat_id, incluir_inativos=False)
    if busca.strip():
        produtos = [p for p in produtos if busca.strip().lower() in p.nome.lower()]

    if not produtos:
        st.markdown("""<div style="background:#2e2010;border:1px solid #4a3420;border-radius:10px;
            padding:28px;text-align:center;color:#9a7d65;margin-top:14px;">
            Nenhum produto encontrado.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:12px;color:#6b4c2a;margin:6px 0 2px;'>{len(produtos)} produto(s)</div>",
                    unsafe_allow_html=True)

        for p in produtos:
            cat_label = p.categoria.nome if p.categoria else "Sem categoria"
            icon      = EMOJI_CAT.get(cat_label, "📦")
            badge_cls = "badge-low" if p.abaixo_do_minimo else "badge-ok"
            badge_txt = "⚠️ Baixo" if p.abaixo_do_minimo else "✅ OK"
            preco_str = f"R$ {p.preco_venda:.2f}"

            col_card, col_pen, col_bin = st.columns([11, 0.6, 0.6])

            with col_card:
                st.markdown(f"""
                <div class="prod-row">
                    <div class="prod-row-icon">{icon}</div>
                    <div style="flex:1;min-width:0;">
                        <div class="prod-row-name">{p.nome}</div>
                        <div class="prod-row-meta">{p.codigo} &nbsp;·&nbsp; {cat_label} &nbsp;·&nbsp; {preco_str}</div>
                    </div>
                    <div class="prod-row-qty">{p.quantidade:g}&nbsp;{p.unidade}</div>
                    <span class="{badge_cls}">{badge_txt}</span>
                </div>""", unsafe_allow_html=True)

            with col_pen:
                if st.button("✏️", key=f"pen_{p.id}", help="Editar produto", use_container_width=True):
                    st.session_state.prod_edit_id = p.id if st.session_state.prod_edit_id != p.id else None
                    st.session_state.prod_del_id  = None

            with col_bin:
                if st.button("🗑️", key=f"bin_{p.id}", help="Remover produto", use_container_width=True):
                    st.session_state.prod_del_id  = p.id if st.session_state.prod_del_id != p.id else None
                    st.session_state.prod_edit_id = None

            # ── Painel de edição inline ───────────────────────
            if st.session_state.prod_edit_id == p.id:
                categorias2 = crud.listar_categorias(db)
                ocat2 = {c.nome: c.id for c in categorias2}
                with st.container():
                    st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                    st.markdown(f"**✏️ Editando: {p.nome}**")
                    with st.form(f"fedit_{p.id}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            e_nome   = st.text_input("Nome",    value=p.nome)
                            e_cod    = st.text_input("Código",  value=p.codigo or "")
                            e_un     = st.selectbox("Unidade",  UNIDADES,
                                       index=UNIDADES.index(p.unidade) if p.unidade in UNIDADES else 0)
                            cats_lst = ["(sem categoria)"] + list(ocat2.keys())
                            cat_idx  = cats_lst.index(p.categoria.nome) if p.categoria and p.categoria.nome in cats_lst else 0
                            e_cat    = st.selectbox("Categoria", cats_lst, index=cat_idx)
                        with e2:
                            e_min    = st.number_input("Estoque mínimo",    value=float(p.estoque_minimo), min_value=0.0)
                            e_custo  = st.number_input("Preço custo (R$)",  value=float(p.preco_custo),    min_value=0.0, format="%.2f")
                            e_venda  = st.number_input("Preço venda (R$)",  value=float(p.preco_venda),    min_value=0.0, format="%.2f")
                            e_desc   = st.text_area("Descrição", value=p.descricao or "", height=68)
                        es1, es2 = st.columns(2)
                        with es1: salvar  = st.form_submit_button("💾 Salvar", use_container_width=True)
                        with es2: fechar  = st.form_submit_button("✖ Fechar", use_container_width=True)
                        if salvar:
                            try:
                                crud.atualizar_produto(db, p.id, {
                                    "nome":e_nome,"codigo":e_cod or None,"unidade":e_un,
                                    "estoque_minimo":e_min,"preco_custo":e_custo,
                                    "preco_venda":e_venda,"descricao":e_desc,
                                    "categoria_id":ocat2.get(e_cat),
                                })
                                st.session_state.prod_edit_id = None
                                st.success("✅ Produto atualizado!")
                                st.rerun()
                            except ValueError as err:
                                st.error(f"❌ {err}")
                        if fechar:
                            st.session_state.prod_edit_id = None
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # ── Painel de confirmação de exclusão ─────────────
            if st.session_state.prod_del_id == p.id:
                tem_movs = len(p.movimentacoes) > 0
                aviso = "possui movimentações — será <strong>inativado</strong>" if tem_movs else "sem movimentações — será <strong>excluído definitivamente</strong>"
                st.markdown(f"""<div style="background:rgba(192,99,90,.1);border:1px solid rgba(192,99,90,.3);
                    border-left:3px solid #c0635a;border-radius:8px;padding:11px 16px;margin:2px 0 6px;">
                    <strong style="color:#e89a94;">Remover "{p.nome}"?</strong>
                    <span style="font-size:12px;color:#c4956a;margin-left:8px;">Este produto {aviso}.</span>
                </div>""", unsafe_allow_html=True)
                dc1, dc2, _ = st.columns([1.4, 1.4, 7])
                with dc1:
                    if st.button("✅ Confirmar", key=f"dconf_{p.id}", use_container_width=True):
                        try:
                            res = crud.inativar_produto(db, p.id)
                            st.session_state.prod_del_id = None
                            st.warning("🚫 Inativado.") if res == "inativado" else st.success("🗑️ Excluído.")
                            st.rerun()
                        except ValueError as err:
                            st.error(f"❌ {err}")
                with dc2:
                    if st.button("✖ Cancelar", key=f"dcanc_{p.id}", use_container_width=True):
                        st.session_state.prod_del_id = None
                        st.rerun()

# ══════════════════════════════════════════════════════════════
# ABA: INATIVOS
# ══════════════════════════════════════════════════════════════
with tab_inativos:
    todos    = crud.listar_produtos(db, incluir_inativos=True)
    inativos = [p for p in todos if not p.esta_ativo]
    if not inativos:
        st.markdown("""<div style="background:#2e2010;border:1px solid #4a3420;border-radius:10px;
            padding:24px;text-align:center;color:#9a7d65;margin-top:12px;">Nenhum produto inativo ✅</div>""",
            unsafe_allow_html=True)
    else:
        st.info(f"ℹ️ {len(inativos)} produto(s) inativo(s) — não aparecem nas listas normais.")
        for p in inativos:
            ic1, ic2, ic3 = st.columns([10, 1.4, 1.4])
            with ic1:
                st.markdown(f"""<div class="prod-row" style="opacity:.65;">
                    <div class="prod-row-icon" style="opacity:.5;">📦</div>
                    <div style="flex:1;min-width:0;">
                        <div class="prod-row-name" style="color:#9a7d65;">{p.nome}</div>
                        <div class="prod-row-meta">{p.codigo} · {p.categoria.nome if p.categoria else '—'} · {len(p.movimentacoes)} mov.</div>
                    </div>
                    <div class="prod-row-qty" style="color:#6b4c2a;">{p.quantidade:g} {p.unidade}</div>
                    <span style="background:rgba(80,60,40,.3);color:#6b4c2a;border:1px solid #4a3420;
                                 border-radius:4px;font-size:10px;font-weight:700;padding:2px 7px;">INATIVO</span>
                </div>""", unsafe_allow_html=True)
            with ic2:
                if st.button("✅ Reativar", key=f"reativ_{p.id}", use_container_width=True):
                    crud.reativar_produto(db, p.id)
                    st.success(f"✅ {p.nome} reativado!")
                    st.rerun()
            with ic3:
                if not p.movimentacoes:
                    if st.button("🗑️ Excluir", key=f"exdel_{p.id}", use_container_width=True):
                        crud.inativar_produto(db, p.id)
                        st.success("🗑️ Excluído.")
                        st.rerun()
                else:
                    st.markdown("<div style='font-size:11px;color:#4a3420;padding:8px 4px;text-align:center;'>🔒 Movs.</div>",
                                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ABA: CADASTRAR PRODUTO
# ══════════════════════════════════════════════════════════════
with tab_cadastro:
    categorias = crud.listar_categorias(db)
    opcoes_cat = {c.nome: c.id for c in categorias}
    st.markdown("""<div style="background:#2e2010;border:1px solid #4a3420;border-left:3px solid #d4894a;
                border-radius:8px;padding:9px 14px;margin-bottom:14px;font-size:13px;color:#c4956a;">
        💡 O código é gerado automaticamente (ex: <code style="color:#e8b48a">PRD-3F7A2C</code>).
        Você também pode informar um código personalizado.
    </div>""", unsafe_allow_html=True)
    with st.form("form_novo_prod"):
        c1, c2 = st.columns(2)
        with c1:
            nome    = st.text_input("Nome do produto *")
            codigo  = st.text_input("Código / SKU", placeholder="Deixar em branco = automático")
            unidade = st.selectbox("Unidade", UNIDADES)
            catsel  = st.selectbox("Categoria", ["(sem categoria)"] + list(opcoes_cat.keys()))
        with c2:
            qtd     = st.number_input("Quantidade inicial", min_value=0.0, value=0.0)
            emin    = st.number_input("Estoque mínimo",     min_value=0.0, value=0.0)
            custo   = st.number_input("Preço custo (R$)",   min_value=0.0, value=0.0, format="%.2f")
            venda   = st.number_input("Preço venda (R$)",   min_value=0.0, value=0.0, format="%.2f")
        desc = st.text_area("Descrição (opcional)")
        if st.form_submit_button("➕ Cadastrar Produto", use_container_width=True):
            if not nome.strip():
                st.error("❌ Nome é obrigatório.")
            else:
                try:
                    p = crud.criar_produto(db, {
                        "nome":nome,"codigo":codigo.strip() or None,"unidade":unidade,
                        "quantidade":qtd,"estoque_minimo":emin,"preco_custo":custo,
                        "preco_venda":venda,"descricao":desc,"categoria_id":opcoes_cat.get(catsel),
                    })
                    st.success(f"✅ **{p.nome}** cadastrado! Código: **{p.codigo}**")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {e}")

# ══════════════════════════════════════════════════════════════
# ABA: CATEGORIAS
# ══════════════════════════════════════════════════════════════
with tab_categorias:
    categorias = crud.listar_categorias(db)
    cc1, cc2 = st.columns([2, 1])
    with cc1:
        st.markdown('<div class="section-title">Categorias cadastradas</div>', unsafe_allow_html=True)
        if categorias:
            dados = [{"Nome": c.nome, "Descrição": c.descricao or "—",
                      "Produtos ativos": len([p for p in c.produtos if p.esta_ativo])} for c in categorias]
            st.dataframe(pd.DataFrame(dados), hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma categoria cadastrada.")
    with cc2:
        with st.form("form_cat"):
            st.markdown("**Nova categoria**")
            nc = st.text_input("Nome *")
            dc = st.text_input("Descrição")
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if not nc.strip(): st.error("❌ Informe o nome.")
                else:
                    try:
                        crud.criar_categoria(db, nc, dc)
                        st.success("✅ Criada!")
                        st.rerun()
                    except ValueError as e: st.error(f"❌ {e}")
        if categorias:
            st.markdown("---")
            cd = st.selectbox("Excluir categoria", [c.nome for c in categorias])
            if st.button("🗑️ Excluir", use_container_width=True):
                try:
                    crud.deletar_categoria(db, next(c.id for c in categorias if c.nome == cd))
                    st.success("✅ Removida.")
                    st.rerun()
                except ValueError as e: st.error(f"❌ {e}")

db.close()
