import streamlit as st
import plotly.express as px
import pandas as pd
from database.connection import init_db, get_db
from database import crud
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual
from theme import GLOBAL_CSS, plot_layout

st.set_page_config(
    page_title="EstoqueApp",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown(
    """
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#d4894a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="EstoqueApp">
<meta name="mobile-web-app-capable" content="yes">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .catch(e => console.log('SW:', e));
  });
}
let deferredPrompt;
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredPrompt = e;
  const btn = document.getElementById('pwa-install-btn');
  if (btn) { btn.style.display = 'block'; }
});
function installPWA() {
  if (deferredPrompt) { deferredPrompt.prompt(); }
}
</script>
""",
    unsafe_allow_html=True,
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

requer_login()
sidebar_nav()

st.title("📦 Dashboard")

u = usuario_atual()
st.caption(f"Bem-vindo, {u.get('nome', 'Usuário')}")

db = get_db()
try:
    resumo = crud.resumo_dashboard(db)
    movimentacoes = crud.listar_movimentacoes(db, dias=30)[:10]
    produtos = crud.listar_produtos(db)
finally:
    db.close()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Produtos cadastrados", resumo["total_produtos"])

with c2:
    st.metric("Alertas de estoque", resumo["alertas_estoque"])

with c3:
    st.metric(
        "Valor total em estoque",
        f'R$ {resumo["valor_total_estoque"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."),
    )

with c4:
    st.metric("Movimentações hoje", resumo["movimentacoes_hoje"])

st.markdown("---")

col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("Produtos com estoque baixo")

    produtos_alertas = resumo.get("produtos_alertas", [])
    if produtos_alertas:
        df_alertas = pd.DataFrame({
            "Produto": [p.nome for p in produtos_alertas[:10]],
            "Quantidade": [float(p.quantidade or 0) for p in produtos_alertas[:10]],
            "Estoque mínimo": [float(p.estoque_minimo or 0) for p in produtos_alertas[:10]],
        })

        fig = px.bar(
            df_alertas,
            x="Produto",
            y=["Quantidade", "Estoque mínimo"],
            barmode="group",
            title="Produtos em alerta",
        )
        fig.update_layout(**plot_layout(360))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum produto em alerta no momento.")

with col2:
    st.subheader("Últimas movimentações")

    if movimentacoes:
        df_mov = pd.DataFrame([
            {
                "Produto": m.produto.nome if m.produto else "Produto",
                "Tipo": m.tipo.value if hasattr(m.tipo, "value") else str(m.tipo),
                "Quantidade": float(m.quantidade or 0),
                "Data": m.criado_em.strftime("%d/%m %H:%M") if m.criado_em else "",
            }
            for m in movimentacoes
        ])
        st.dataframe(df_mov, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma movimentação registrada.")

st.markdown("---")
st.subheader("Acesso rápido")

a1, a2, a3, a4 = st.columns(4)

with a1:
    st.page_link("pages/1_Produtos.py", label="📦 Produtos")

with a2:
    st.page_link("pages/2_Movimentacoes.py", label="🔄 Movimentações")

with a3:
    st.page_link("pages/3_Relatorios.py", label="📊 Relatórios")

with a4:
    st.page_link("pages/9_Fornecedores.py", label="🚚 Fornecedores")
