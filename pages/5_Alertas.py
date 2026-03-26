import streamlit as st
import pandas as pd
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db
from database import crud
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS, COLORS

st.set_page_config(page_title="Alertas — EstoqueApp", page_icon="🔔", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador", "visualizador"])
sidebar_nav()


db = get_db()
produtos_alerta = crud.listar_produtos(db, apenas_alertas=True)

st.markdown('<div class="page-header">🔔 Alertas de Estoque</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Produtos que precisam de reposição ou estão zerados.</div>', unsafe_allow_html=True)

if not produtos_alerta:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a2e1a,#1e3520);border:1px solid #27ae6044;
                border-radius:12px;padding:30px;text-align:center;color:#7ab87a;font-size:18px;margin-top:20px;">
        ✅ Todos os produtos estão com estoque acima do mínimo!
    </div>""", unsafe_allow_html=True)
else:
    criticos = [p for p in produtos_alerta if p.quantidade <= 0]
    atencao  = [p for p in produtos_alerta if p.quantidade > 0]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div style="background:rgba(192,99,90,0.15);border:1px solid {COLORS['red']}44;
                        border-left:3px solid {COLORS['red']};border-radius:8px;padding:14px 18px;">
            <div style="font-size:11px;color:{COLORS['red']};text-transform:uppercase;letter-spacing:0.1em;">Críticos (sem estoque)</div>
            <div style="font-family:'Inconsolata',monospace;font-size:30px;color:{COLORS['red']};font-weight:700;">{len(criticos)}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div style="background:rgba(212,168,67,0.15);border:1px solid {COLORS['yellow']}44;
                        border-left:3px solid {COLORS['yellow']};border-radius:8px;padding:14px 18px;">
            <div style="font-size:11px;color:{COLORS['yellow']};text-transform:uppercase;letter-spacing:0.1em;">Atenção (abaixo do mínimo)</div>
            <div style="font-family:'Inconsolata',monospace;font-size:30px;color:{COLORS['yellow']};font-weight:700;">{len(atencao)}</div>
        </div>""", unsafe_allow_html=True)

    if criticos:
        st.markdown('<div class="section-title">🚨 Estoque Zerado — Reposição Urgente</div>', unsafe_allow_html=True)
        for p in criticos:
            cat = p.categoria.nome if p.categoria else "Sem categoria"
            st.markdown(f"""
            <div style="background:rgba(192,99,90,0.12);border:1px solid rgba(192,99,90,0.3);
                        border-left:4px solid {COLORS['red']};border-radius:10px;
                        padding:14px 18px;margin-bottom:8px;">
                <span class="id-badge">{p.codigo}</span>
                <strong style="color:{COLORS['red']};">{p.nome}</strong>
                <div style="font-size:13px;color:#e8a09a;margin-top:4px;">
                    Categoria: {cat} &nbsp;|&nbsp;
                    Estoque: <strong>0 {p.unidade}</strong> &nbsp;|&nbsp;
                    Mínimo necessário: {p.estoque_minimo} {p.unidade}
                </div>
            </div>""", unsafe_allow_html=True)

    if atencao:
        st.markdown('<div class="section-title">⚠️ Abaixo do Mínimo — Repor em Breve</div>', unsafe_allow_html=True)
        for p in atencao:
            cat = p.categoria.nome if p.categoria else "Sem categoria"
            falta = p.estoque_minimo - p.quantidade
            pct   = (p.quantidade / p.estoque_minimo * 100) if p.estoque_minimo > 0 else 0
            st.markdown(f"""
            <div style="background:rgba(212,168,67,0.1);border:1px solid rgba(212,168,67,0.25);
                        border-left:4px solid {COLORS['yellow']};border-radius:10px;
                        padding:14px 18px;margin-bottom:8px;">
                <span class="id-badge">{p.codigo}</span>
                <strong style="color:{COLORS['yellow']};">{p.nome}</strong>
                <div style="font-size:13px;color:#f0d080;margin-top:4px;">
                    Categoria: {cat} &nbsp;|&nbsp;
                    Atual: <strong>{p.quantidade} {p.unidade}</strong> &nbsp;|&nbsp;
                    Mínimo: {p.estoque_minimo} {p.unidade} &nbsp;|&nbsp;
                    Faltam: <strong>{falta:.1f} {p.unidade}</strong> ({pct:.0f}% do mínimo)
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">📋 Tabela Resumo</div>', unsafe_allow_html=True)
    dados = [{"Código": p.codigo or "—", "Produto": p.nome,
              "Categoria": p.categoria.nome if p.categoria else "—",
              "Qtd Atual": f"{p.quantidade} {p.unidade}",
              "Mínimo": f"{p.estoque_minimo} {p.unidade}",
              "Falta": f"{max(0, p.estoque_minimo - p.quantidade):.1f} {p.unidade}",
              "Status": "🚨 Zerado" if p.quantidade <= 0 else "⚠️ Baixo"} for p in produtos_alerta]
    st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)

db.close()
