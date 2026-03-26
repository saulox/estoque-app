import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db, init_db
from database import crud
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS, COLORS

st.set_page_config(page_title="Inventário — EstoqueApp", page_icon="📋", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador"])
sidebar_nav()
st.markdown("""
<style>
.inv-row {
    background:linear-gradient(145deg,#2e2010,#3a2814);
    border:1px solid #4a3420; border-radius:10px;
    padding:12px 16px; margin-bottom:4px;
    display:flex; align-items:center; gap:12px;
    transition:border-color .18s;
}
.inv-row:hover { border-color:#8b5e3c; }
.inv-icon { width:36px;height:36px;border-radius:8px;flex-shrink:0;
            background:linear-gradient(135deg,#4a3420,#6b4c2a);
            display:flex;align-items:center;justify-content:center;font-size:16px; }
.inv-name { font-weight:600;font-size:13.5px;color:#e8b48a;line-height:1.2; }
.inv-meta { font-size:11px;color:#9a7d65;margin-top:1px; }
.inv-sys  { font-family:'Inconsolata',monospace;font-size:13px;color:#c4956a;
            flex-shrink:0;min-width:90px;text-align:right; }
.diff-pos { color:#7ab87a;font-weight:700; }
.diff-neg { color:#c0635a;font-weight:700; }
.diff-zer { color:#9a7d65; }
.inv-status-bar {
    background:#2e2010; border:1px solid #4a3420; border-radius:10px;
    padding:14px 18px; margin-bottom:16px;
    display:flex; gap:24px; align-items:center; flex-wrap:wrap;
}
</style>
""", unsafe_allow_html=True)

init_db()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

db = get_db()

# ─── Session state ─────────────────────────────────────────────────────────────
if "inv_contagens" not in st.session_state:
    st.session_state.inv_contagens = {}   # {produto_id: qtd_contada}
if "inv_iniciado" not in st.session_state:
    st.session_state.inv_iniciado = False
if "inv_confirmado" not in st.session_state:
    st.session_state.inv_confirmado = False

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-header">📋 Inventário</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Contagem física de estoque com ajuste automático das quantidades.</div>', unsafe_allow_html=True)

st.markdown("""
<div style="background:rgba(212,137,74,0.1);border:1px solid rgba(212,137,74,0.3);
            border-left:3px solid #d4894a;border-radius:8px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#c4956a;">
    <strong>Como funciona:</strong> Preencha a quantidade física contada para cada produto. 
    O sistema calcula a diferença em relação ao estoque atual e, ao confirmar, 
    registra um ajuste de inventário como movimentação automática.
</div>
""", unsafe_allow_html=True)

# ─── Filtros ───────────────────────────────────────────────────────────────────
categorias  = crud.listar_categorias(db)
opcoes_cat  = {"📂 Todas": None}
opcoes_cat.update({c.nome: c.id for c in categorias})

fc1, fc2, fc3 = st.columns([3, 2, 1.5])
with fc1:
    busca_inv = st.text_input("Busca", placeholder="🔍  Buscar produto...",
                               label_visibility="collapsed", key="inv_busca")
with fc2:
    cat_inv = st.selectbox("Filtro", list(opcoes_cat.keys()),
                            label_visibility="collapsed", key="inv_cat")
with fc3:
    mostrar = st.selectbox("Filtro", ["Todos", "Com diferença", "Só alertas"],
                            label_visibility="collapsed", key="inv_show")

produtos = crud.listar_produtos(db, categoria_id=opcoes_cat[cat_inv], incluir_inativos=False)
if busca_inv.strip():
    produtos = [p for p in produtos if busca_inv.strip().lower() in p.nome.lower()]

EMOJI_CAT = {"Alimentos":"🍎","Bebidas":"🥤","Limpeza":"🧹","Eletrônicos":"💻",
             "Roupas":"👕","Calçados":"👟","Ferramentas":"🔧","Papelaria":"📝",
             "Acessórios":"💍","Cosméticos":"💄","Médico":"💊","Outros":"📦"}

# inicializa contagens novas (preserva as já preenchidas)
for p in produtos:
    if p.id not in st.session_state.inv_contagens:
        st.session_state.inv_contagens[p.id] = float(p.quantidade)

# aplica filtro "com diferença"
if mostrar == "Com diferença":
    produtos = [p for p in produtos
                if st.session_state.inv_contagens.get(p.id, p.quantidade) != p.quantidade]
elif mostrar == "Só alertas":
    produtos = [p for p in produtos if p.abaixo_do_minimo]

# ─── Resumo ───────────────────────────────────────────────────────────────────
if produtos:
    contagens = st.session_state.inv_contagens
    total_dif_pos = sum(max(0, contagens.get(p.id, p.quantidade) - p.quantidade) for p in produtos)
    total_dif_neg = sum(max(0, p.quantidade - contagens.get(p.id, p.quantidade)) for p in produtos)
    com_diff      = sum(1 for p in produtos if contagens.get(p.id, p.quantidade) != p.quantidade)

    st.markdown(f"""
    <div class="inv-status-bar">
        <span style="color:#9a7d65;font-size:13px;">
            <strong style="color:#c4956a;font-family:Inconsolata,monospace;font-size:18px;">{len(produtos)}</strong>
            &nbsp;produto(s)
        </span>
        <span style="color:#9a7d65;font-size:13px;">
            Diferenças: <strong style="color:#{'d4a843' if com_diff else '7ab87a'};">{com_diff}</strong>
        </span>
        <span style="color:#9a7d65;font-size:13px;">
            Sobras: <strong style="color:#7ab87a;">+{total_dif_pos:g}</strong>
        </span>
        <span style="color:#9a7d65;font-size:13px;">
            Faltas: <strong style="color:#c0635a;">-{total_dif_neg:g}</strong>
        </span>
        <span style="font-size:12px;color:#6b4c2a;margin-left:auto;">
            Última atualização: {datetime.now().strftime('%H:%M:%S')}
        </span>
    </div>
    """, unsafe_allow_html=True)

# ─── Lista de produtos para contagem ──────────────────────────────────────────
if not produtos:
    st.markdown("""<div style="background:#2e2010;border:1px solid #4a3420;border-radius:10px;
        padding:28px;text-align:center;color:#9a7d65;margin-top:14px;">
        Nenhum produto encontrado.</div>""", unsafe_allow_html=True)
else:
    st.markdown('<div class="section-title">📦 Contagem por Produto</div>', unsafe_allow_html=True)

    for p in produtos:
        contado   = st.session_state.inv_contagens.get(p.id, float(p.quantidade))
        diff      = contado - p.quantidade
        diff_cls  = "diff-pos" if diff > 0 else ("diff-neg" if diff < 0 else "diff-zer")
        diff_str  = (f"+{diff:g}" if diff > 0 else f"{diff:g}") if diff != 0 else "—"
        cat_label = p.categoria.nome if p.categoria else "Sem categoria"
        icon      = EMOJI_CAT.get(cat_label, "📦")

        col_card, col_input, col_diff = st.columns([5, 2, 1.2])

        with col_card:
            st.markdown(f"""
            <div class="inv-row">
                <div class="inv-icon">{icon}</div>
                <div style="flex:1;min-width:0;">
                    <div class="inv-name">{p.nome}</div>
                    <div class="inv-meta">{p.codigo} &nbsp;·&nbsp; {cat_label}</div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:10px;color:#9a7d65;text-transform:uppercase;letter-spacing:.08em;">Sistema</div>
                    <div class="inv-sys">{p.quantidade:g}&nbsp;{p.unidade}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col_input:
            novo_val = st.number_input(
                f"Contado ({p.unidade})",
                min_value=0.0,
                value=float(contado),
                step=1.0,
                key=f"inv_{p.id}",
                label_visibility="visible",
            )
            # atualiza contagem na sessão
            if novo_val != contado:
                st.session_state.inv_contagens[p.id] = novo_val

        with col_diff:
            st.markdown(f"""
            <div style="height:100%;display:flex;flex-direction:column;
                        align-items:center;justify-content:center;padding-top:28px;">
                <div style="font-size:10px;color:#9a7d65;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;">Dif.</div>
                <div class="{diff_cls}" style="font-family:Inconsolata,monospace;font-size:17px;font-weight:700;">{diff_str}</div>
            </div>""", unsafe_allow_html=True)

    # ─── Botões de ação ────────────────────────────────────────────────────────
    st.markdown("---")

    # Lista de ajustes a fazer
    ajustes = [(p, st.session_state.inv_contagens.get(p.id, p.quantidade))
               for p in crud.listar_produtos(db, incluir_inativos=False)
               if st.session_state.inv_contagens.get(p.id, p.quantidade) != p.quantidade]

    if ajustes:
        st.markdown(f'<div class="section-title">⚙️ Ajustes a aplicar ({len(ajustes)} produto(s))</div>',
                    unsafe_allow_html=True)
        for p_aj, qtd_aj in ajustes:
            diff_aj = qtd_aj - p_aj.quantidade
            sinal   = "📈 Entrada" if diff_aj > 0 else "📉 Saída"
            cor     = "#7ab87a" if diff_aj > 0 else "#c0635a"
            st.markdown(f"""
            <div style="background:#2e2010;border:1px solid #4a3420;border-radius:8px;
                        padding:8px 14px;margin-bottom:4px;display:flex;gap:12px;align-items:center;">
                <span style="font-size:13px;color:#c4956a;flex:1;">{p_aj.nome}</span>
                <span style="font-size:12px;color:#9a7d65;">
                    Sistema: {p_aj.quantidade:g} {p_aj.unidade}
                </span>
                <span style="font-size:12px;color:#9a7d65;">→</span>
                <span style="font-size:13px;font-weight:700;color:{cor};">
                    {sinal}: {abs(diff_aj):g} {p_aj.unidade}
                    (novo: {qtd_aj:g})
                </span>
            </div>""", unsafe_allow_html=True)

        col_confirm, col_reset = st.columns([2, 1])
        with col_confirm:
            if st.button("✅ Confirmar e Aplicar Ajustes de Inventário",
                         use_container_width=True, type="primary"):
                erros = []
                ok    = 0
                for p_aj, qtd_aj in ajustes:
                    try:
                        crud.ajustar_estoque_inventario(db, p_aj.id, qtd_aj,
                                                        "Ajuste de inventário físico")
                        ok += 1
                    except Exception as e:
                        erros.append(f"{p_aj.nome}: {e}")

                # Disparar alerta de inventário
                total_sobras = sum(max(0, qtd_aj - p_aj.quantidade) for p_aj, qtd_aj in ajustes)
                total_faltas = sum(max(0, p_aj.quantidade - qtd_aj) for p_aj, qtd_aj in ajustes)
                try:
                    from alertas.notificador import Notificador
                    Notificador(db).alertar_inventario(
                        total=len(crud.listar_produtos(db, incluir_inativos=False)),
                        ajustes=ok, sobras=total_sobras, faltas=total_faltas
                    )
                except Exception:
                    pass

                st.session_state.inv_contagens = {}
                if erros:
                    for e in erros: st.error(f"❌ {e}")
                st.success(f"✅ {ok} produto(s) ajustado(s) com sucesso! Estoque atualizado.")
                st.rerun()

        with col_reset:
            if st.button("🔄 Resetar contagens", use_container_width=True):
                st.session_state.inv_contagens = {}
                st.rerun()
    else:
        st.markdown("""
        <div style="background:rgba(122,184,122,0.1);border:1px solid rgba(122,184,122,0.25);
                    border-radius:8px;padding:12px 16px;text-align:center;color:#7ab87a;font-size:14px;">
            ✅ Nenhuma diferença encontrada — estoque físico confere com o sistema.
        </div>""", unsafe_allow_html=True)

    # ─── Exportar planilha ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">⬇️ Exportar</div>', unsafe_allow_html=True)
    todos_prods = crud.listar_produtos(db, incluir_inativos=False)
    if st.button("📥 Exportar planilha de inventário (.xlsx)", use_container_width=False):
        import openpyxl
        from io import BytesIO
        dados_exp = []
        for p in todos_prods:
            contado_exp = st.session_state.inv_contagens.get(p.id, p.quantidade)
            diff_exp    = contado_exp - p.quantidade
            dados_exp.append({
                "Código":       p.codigo or "—",
                "Nome":         p.nome,
                "Categoria":    p.categoria.nome if p.categoria else "—",
                "Unidade":      p.unidade,
                "Qtd Sistema":  p.quantidade,
                "Qtd Contada":  contado_exp,
                "Diferença":    diff_exp,
                "Status":       "OK" if diff_exp == 0 else ("Sobra" if diff_exp > 0 else "Falta"),
            })
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            pd.DataFrame(dados_exp).to_excel(w, index=False, sheet_name="Inventário")
        st.download_button("⬇️ Baixar inventario.xlsx", buf.getvalue(), "inventario.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

db.close()
