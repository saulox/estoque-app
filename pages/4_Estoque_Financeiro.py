import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db
from database import crud
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS, COLORS, plot_layout

st.set_page_config(page_title="Estoque Financeiro — EstoqueApp", page_icon="💰", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador", "visualizador"])
sidebar_nav()


db = get_db()
produtos = crud.listar_produtos(db)

st.markdown('<div class="page-header">💰 Estoque Financeiro</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Valor financeiro imobilizado, margens e lucro potencial do seu estoque.</div>', unsafe_allow_html=True)

if not produtos:
    st.info("Nenhum produto cadastrado.")
    db.close()
    st.stop()

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

valor_custo  = sum(p.valor_em_estoque for p in produtos)
valor_venda  = sum(p.quantidade * p.preco_venda for p in produtos)
lucro_pot    = valor_venda - valor_custo
margem_media = (lucro_pot / valor_custo * 100) if valor_custo > 0 else 0

col1, col2, col3, col4 = st.columns(4)
def fin_card(label, value, cor_borda):
    return f"""<div style="background:linear-gradient(145deg,#2e2010,#3a2814);
               border:1px solid #4a3420;border-top:2px solid {cor_borda};
               border-radius:12px;padding:20px 22px;margin-bottom:12px;">
        <div style="font-size:11px;color:#9a7d65;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">{label}</div>
        <div style="font-family:'Inconsolata',monospace;font-size:24px;font-weight:700;color:#e8b48a;">{value}</div>
    </div>"""

with col1: st.markdown(fin_card("💰 Valor de Custo", fmt_brl(valor_custo), COLORS["brown_main"]), unsafe_allow_html=True)
with col2: st.markdown(fin_card("🏷️ Valor de Venda", fmt_brl(valor_venda), COLORS["brown_light"]), unsafe_allow_html=True)
with col3: st.markdown(fin_card("📈 Lucro Potencial", fmt_brl(lucro_pot),  COLORS["accent"]), unsafe_allow_html=True)
with col4: st.markdown(fin_card("📊 Margem Média",    f"{margem_media:.1f}%", COLORS["yellow"]), unsafe_allow_html=True)

st.markdown('<div class="section-title">📋 Detalhe por Produto</div>', unsafe_allow_html=True)
dados = []
for p in produtos:
    margem = ((p.preco_venda - p.preco_custo) / p.preco_custo * 100) if p.preco_custo > 0 else 0
    dados.append({
        "Código": p.codigo or "—",
        "Produto": p.nome,
        "Categoria": p.categoria.nome if p.categoria else "—",
        "Qtd": f"{p.quantidade} {p.unidade}",
        "Custo Unit.": f"R$ {p.preco_custo:.2f}",
        "Venda Unit.": f"R$ {p.preco_venda:.2f}",
        "Margem": f"{margem:.1f}%",
        "Val. Custo": f"R$ {p.valor_em_estoque:.2f}",
        "Val. Venda": f"R$ {p.quantidade * p.preco_venda:.2f}",
        "Lucro Pot.": f"R$ {(p.preco_venda - p.preco_custo) * p.quantidade:.2f}",
    })
st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown('<div class="section-title">💰 Maior Valor em Estoque (Top 10)</div>', unsafe_allow_html=True)
    top10 = sorted(produtos, key=lambda p: p.valor_em_estoque, reverse=True)[:10]
    df_top = pd.DataFrame({"Produto": [p.nome for p in top10], "Valor (R$)": [p.valor_em_estoque for p in top10]})
    fig = px.bar(df_top, x="Valor (R$)", y="Produto", orientation="h", color="Valor (R$)",
                 color_continuous_scale=[COLORS["bg_card2"], COLORS["brown_main"]])
    fig.update_layout(**plot_layout(300), coloraxis_showscale=False)
    fig.update_layout(yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True)

with col_g2:
    st.markdown('<div class="section-title">🏷️ Custo vs Venda por Categoria</div>', unsafe_allow_html=True)
    cat_data = {}
    for p in produtos:
        cat = p.categoria.nome if p.categoria else "Sem categoria"
        if cat not in cat_data:
            cat_data[cat] = {"custo": 0, "venda": 0}
        cat_data[cat]["custo"] += p.valor_em_estoque
        cat_data[cat]["venda"] += p.quantidade * p.preco_venda
    if cat_data:
        cats = list(cat_data.keys())
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Custo", x=cats, y=[cat_data[c]["custo"] for c in cats], marker_color=COLORS["brown_main"]))
        fig2.add_trace(go.Bar(name="Venda", x=cats, y=[cat_data[c]["venda"] for c in cats], marker_color=COLORS["accent"]))
        fig2.update_layout(**plot_layout(300), barmode="group")
        st.plotly_chart(fig2, use_container_width=True)

db.close()
