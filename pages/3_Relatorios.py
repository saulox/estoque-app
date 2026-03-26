import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db
from database import crud
from database.models import TipoMovimentacao
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS, COLORS, plot_layout

st.set_page_config(page_title="Relatórios — EstoqueApp", page_icon="📊", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador", "visualizador"])
sidebar_nav()


db = get_db()

st.markdown('<div class="page-header">📊 Relatórios</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Análise visual das movimentações e do estoque.</div>', unsafe_allow_html=True)

col1, _ = st.columns([1, 3])
with col1:
    dias = st.selectbox("Período de análise", [7, 15, 30, 60, 90], index=2,
                        format_func=lambda x: f"Últimos {x} dias")

st.markdown('<div class="section-title">📈 Entradas vs Saídas por dia</div>', unsafe_allow_html=True)
movs_dia = crud.movimentacoes_por_dia(db, dias=dias)
if movs_dia:
    df = pd.DataFrame(movs_dia, columns=["data", "tipo", "total"])
    df["data"] = pd.to_datetime(df["data"])
    df_ent = df[df["tipo"] == "entrada"].rename(columns={"total": "Entradas"})
    df_sai = df[df["tipo"] == "saida"].rename(columns={"total": "Saídas"})
    df_m   = df_ent.merge(df_sai, on="data", how="outer").fillna(0)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_m["data"], y=df_m.get("Entradas", 0), name="Entradas", marker_color=COLORS["green"]))
    fig.add_trace(go.Bar(x=df_m["data"], y=df_m.get("Saídas",   0), name="Saídas",   marker_color=COLORS["red"]))
    fig.update_layout(**plot_layout(300), barmode="group")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem dados de movimentação para o período.")

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown('<div class="section-title">🏆 Mais movimentados</div>', unsafe_allow_html=True)
    top = crud.top_produtos_movimentados(db, dias=dias, limite=8)
    if top:
        df_top = pd.DataFrame(top, columns=["Produto", "Total"])
        fig2 = px.bar(df_top, x="Total", y="Produto", orientation="h", color="Total",
                      color_continuous_scale=[COLORS["bg_card2"], COLORS["accent"]])
        fig2.update_layout(**plot_layout(300), coloraxis_showscale=False)
        fig2.update_layout(yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem dados.")

with col_g2:
    st.markdown('<div class="section-title">🏷️ Distribuição por Categoria</div>', unsafe_allow_html=True)
    produtos = crud.listar_produtos(db)
    if produtos:
        cat_counts = {}
        for p in produtos:
            cat = p.categoria.nome if p.categoria else "Sem categoria"
            cat_counts[cat] = cat_counts.get(cat, 0) + p.quantidade
        df_cat = pd.DataFrame(list(cat_counts.items()), columns=["Categoria", "Quantidade"])
        fig3 = px.pie(df_cat, names="Categoria", values="Quantidade",
                      color_discrete_sequence=[COLORS["brown_main"], COLORS["accent"],
                                               COLORS["brown_light"], COLORS["brown_bright"],
                                               COLORS["muted"]])
        fig3.update_layout(**plot_layout(300))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Nenhum produto cadastrado.")

st.markdown('<div class="section-title">⬇️ Exportar Dados</div>', unsafe_allow_html=True)
col_e1, col_e2 = st.columns(2)

with col_e1:
    if st.button("📦 Exportar lista de produtos (.xlsx)", use_container_width=True):
        produtos = crud.listar_produtos(db)
        if produtos:
            dados = [{"Código": p.codigo, "Nome": p.nome,
                      "Categoria": p.categoria.nome if p.categoria else "",
                      "Unidade": p.unidade, "Quantidade": p.quantidade,
                      "Estoque Mínimo": p.estoque_minimo,
                      "Preço Custo": p.preco_custo, "Preço Venda": p.preco_venda,
                      "Valor em Estoque": p.valor_em_estoque} for p in produtos]
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as w:
                pd.DataFrame(dados).to_excel(w, index=False, sheet_name="Produtos")
            st.download_button("⬇️ Baixar produtos.xlsx", buffer.getvalue(), "produtos.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col_e2:
    if st.button("🔄 Exportar movimentações (.xlsx)", use_container_width=True):
        movs = crud.listar_movimentacoes(db, dias=dias)
        if movs:
            dados = [{"Data": m.criado_em.strftime("%d/%m/%Y %H:%M"),
                      "Produto": m.produto.nome, "Código": m.produto.codigo,
                      "Tipo": m.tipo.value, "Quantidade": m.quantidade,
                      "Preço Unit.": m.preco_unitario, "Total": m.valor_total,
                      "Motivo": m.motivo} for m in movs]
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as w:
                pd.DataFrame(dados).to_excel(w, index=False, sheet_name="Movimentações")
            st.download_button("⬇️ Baixar movimentacoes.xlsx", buffer.getvalue(), "movimentacoes.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

db.close()
