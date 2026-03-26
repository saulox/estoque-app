import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db
from database import crud
from database.models import TipoMovimentacao
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS, COLORS, plot_layout

st.set_page_config(page_title="Movimentações — EstoqueApp", page_icon="🔄", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador"])
sidebar_nav()

st.markdown("""
<style>
.mov-card {
    background: linear-gradient(145deg, #251a0e, #2e2010);
    border: 1px solid #3a2814;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}
.mov-card::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
}
.mov-card.entrada::before { background: #7ab87a; }
.mov-card.saida::before   { background: #c0635a; }
.mov-card:hover {
    border-color: #6b4c2a;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transform: translateX(2px);
}
.mov-avatar {
    width: 42px; height: 42px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.mov-avatar.entrada { background: rgba(122,184,122,.15); border: 1px solid rgba(122,184,122,.3); }
.mov-avatar.saida   { background: rgba(192,99,90,.15);  border: 1px solid rgba(192,99,90,.3); }
.mov-body { flex: 1; min-width: 0; }
.mov-title {
    font-weight: 600; font-size: 13.5px; color: #e8b48a;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.mov-sub {
    font-size: 11.5px; color: #9a7d65; margin-top: 3px;
    display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
}
.mov-sub .tag {
    background: rgba(74,52,32,.6); border: 1px solid #4a3420;
    border-radius: 4px; padding: 1px 7px; font-size: 10.5px; color: #c4956a;
}
.mov-qty {
    font-family: "Inconsolata", monospace;
    font-size: 15px; font-weight: 700;
    min-width: 100px; text-align: right; flex-shrink: 0;
}
.mov-qty.entrada { color: #7ab87a; }
.mov-qty.saida   { color: #c0635a; }
.mov-value {
    font-size: 12px; color: #c4956a;
    min-width: 90px; text-align: right; flex-shrink: 0;
}
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }
.kpi-card {
    background: linear-gradient(145deg, #251a0e, #2e2010);
    border: 1px solid #3a2814;
    border-radius: 14px;
    padding: 18px 20px;
    position: relative; overflow: hidden;
    transition: all 0.2s;
}
.kpi-card:hover { border-color: #6b4c2a; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.35); }
.kpi-card .kpi-icon {
    font-size: 22px; margin-bottom: 10px;
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
}
.kpi-card .kpi-label { font-size: 10.5px; color: #9a7d65; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 6px; }
.kpi-card .kpi-value { font-family: "Inconsolata", monospace; font-size: 24px; font-weight: 700; color: #e8b48a; }
.kpi-card .kpi-delta { font-size: 11px; color: #6b4c2a; margin-top: 4px; }
.kpi-card .kpi-bg {
    position: absolute; right: -10px; bottom: -10px;
    font-size: 64px; opacity: .06; pointer-events: none;
}
.filter-panel {
    background: linear-gradient(145deg, #1f1508, #251a0e);
    border: 1px solid #3a2814;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 18px;
}
.edit-panel {
    background: linear-gradient(135deg, #1f1508, #251a0e);
    border: 1px solid #6b4c2a;
    border-left: 3px solid #d4894a;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 2px 0 10px;
}
.del-panel {
    background: rgba(192,99,90,.08);
    border: 1px solid rgba(192,99,90,.25);
    border-left: 3px solid #c0635a;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 2px 0 10px;
}
.prod-found {
    background: rgba(122,184,122,.1);
    border: 1px solid rgba(122,184,122,.3);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 12px;
}
.timeline-date {
    font-size: 11px; color: #6b4c2a;
    text-transform: uppercase; letter-spacing: .1em;
    padding: 10px 0 6px; font-weight: 700;
    display: flex; align-items: center; gap: 8px;
}
.timeline-date::after {
    content: ""; flex: 1; height: 1px; background: #2e2010;
}
</style>
""", unsafe_allow_html=True)

db = get_db()

for k in ["mov_edit_id", "mov_del_id"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ── HEADER ──
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="page-header">🔄 Movimentações</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Registre entradas, saídas e acompanhe o histórico completo do estoque.</div>', unsafe_allow_html=True)
with col_h2:
    movs_hoje = crud.listar_movimentacoes(db, dias=1)
    st.markdown(f"""
    <div style="background:#2e2010;border:1px solid #4a3420;border-radius:10px;
                padding:12px 16px;text-align:center;margin-top:8px;">
        <div style="font-size:10px;color:#9a7d65;text-transform:uppercase;letter-spacing:.1em;">Mov. hoje</div>
        <div style="font-family:'Inconsolata',monospace;font-size:26px;font-weight:700;color:#d4894a;">{len(movs_hoje)}</div>
    </div>
    """, unsafe_allow_html=True)

tab_nova, tab_historico, tab_graficos, tab_rapida = st.tabs([
    "➕  Nova Movimentação",
    "📋  Histórico & Edição",
    "📊  Análise Visual",
    "⚡  Movimentação em Lote",
])

# ══════════════════════════════════════════════════════════════
# ABA 1: NOVA MOVIMENTAÇÃO
# ══════════════════════════════════════════════════════════════
with tab_nova:
    col_form, col_preview = st.columns([3, 2])

    with col_form:
        st.markdown("""
        <div style="background:#1a1208;border:1px dashed #4a3420;border-radius:12px;
                    padding:14px 18px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:10px;font-size:12.5px;color:#9a7d65;">
                <span style="font-size:20px;">📷</span>
                Use um <strong style="color:#c4956a;">leitor USB</strong> ou câmera para escanear,
                ou busque pelo nome do produto abaixo.
            </div>
        </div>
        """, unsafe_allow_html=True)

        sc1, sc2 = st.columns([3, 1])
        with sc1:
            codigo_lido = st.text_input("Buscar produto", placeholder="🔍  Código de barras, SKU ou nome...",
                                        label_visibility="collapsed", key="barcode_input")
        with sc2:
            usar_camera = st.toggle("📷 Câmera", key="barcode_camera")

        if usar_camera:
            st.markdown("""
            <div id="barcode-scanner" style="background:#1a1208;border:1px solid #4a3420;border-radius:10px;padding:14px;text-align:center;">
                <video id="bc-video" style="width:100%;max-width:340px;border-radius:8px;" autoplay playsinline></video>
                <div id="bc-result" style="margin-top:10px;font-size:13px;color:#c4956a;"></div>
            </div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>
            <script>
            (function(){
                const video=document.getElementById("bc-video"),result=document.getElementById("bc-result");
                let scanned=false;
                navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}})
                    .then(s=>{video.srcObject=s;}).catch(()=>{result.textContent="Câmera não disponível.";});
                Quagga.init({inputStream:{name:"Live",type:"LiveStream",target:video},
                    decoder:{readers:["code_128_reader","ean_reader","ean_8_reader","code_39_reader"]}
                },err=>{if(err){result.textContent="Erro: "+err;return;}Quagga.start();});
                Quagga.onDetected(data=>{
                    if(scanned)return;scanned=true;
                    const code=data.codeResult.code;
                    result.innerHTML="✅ Código: <strong>"+code+"</strong>";
                    window.parent.document.querySelectorAll("input").forEach(inp=>{
                        if(inp.placeholder&&inp.placeholder.includes("Código")){
                            inp.value=code;inp.dispatchEvent(new Event("input",{bubbles:true}));
                        }
                    });
                    Quagga.stop();setTimeout(()=>{scanned=false;Quagga.start();},2500);
                });
            })();
            </script>""", unsafe_allow_html=True)

        produto_pre_idx = 0
        if codigo_lido.strip():
            _db2 = get_db()
            _prods = crud.listar_produtos(_db2)
            _match = [p for p in _prods if p.codigo and codigo_lido.strip().lower() in p.codigo.lower()]
            if not _match:
                _match = [p for p in _prods if codigo_lido.strip().lower() in p.nome.lower()]
            _db2.close()
            if _match:
                p = _match[0]
                cor_est = "#7ab87a" if not p.abaixo_do_minimo else "#d4a843"
                alerta_html = f'<span style="color:#d4a843;font-size:11px;">⚠️ Estoque baixo (mín: {p.estoque_minimo:g} {p.unidade})</span>' if p.abaixo_do_minimo else ""
                st.markdown(f"""
                <div class="prod-found">
                    <span style="font-size:28px;">📦</span>
                    <div style="flex:1;">
                        <div style="font-weight:700;font-size:14px;color:#e8b48a;">{p.nome}</div>
                        <div style="font-size:12px;color:#9a7d65;margin-top:2px;">
                            SKU: {p.codigo} &nbsp;·&nbsp;
                            {p.categoria.nome if p.categoria else "Sem categoria"} &nbsp;·&nbsp;
                            Venda: R$ {p.preco_venda:.2f}
                            {"&nbsp;·&nbsp;" + alerta_html if alerta_html else ""}
                        </div>
                    </div>
                    <div style="text-align:right;font-family:'Inconsolata',monospace;font-size:20px;font-weight:700;color:{cor_est};">
                        {p.quantidade:g} <span style="font-size:12px;color:#9a7d65;">{p.unidade}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                produto_pre_idx = p.id
            else:
                st.warning(f"⚠️ Nenhum produto encontrado com '{codigo_lido}'.")

        produtos = crud.listar_produtos(db)
        if not produtos:
            st.warning("⚠️ Nenhum produto cadastrado. Cadastre um produto primeiro.")
        else:
            produto_map = {f"[{p.codigo}] {p.nome}  —  Estoque: {p.quantidade} {p.unidade}": p for p in produtos}
            opcoes = list(produto_map.keys())
            idx_default = 0
            if produto_pre_idx:
                for i, p in enumerate(produtos):
                    if p.id == produto_pre_idx:
                        idx_default = i
                        break

            with st.form("form_mov", clear_on_submit=True):
                psel = st.selectbox("Produto *", opcoes, index=idx_default)
                prod_obj = produto_map[psel]

                c1, c2 = st.columns(2)
                with c1:
                    tipo = st.radio("Tipo *", ["📥 Entrada", "📤 Saída"], horizontal=True)
                with c2:
                    data_mov = st.date_input("Data", value=date.today())

                st.markdown("<hr style='border-color:#2e2010;margin:10px 0;'>", unsafe_allow_html=True)

                d1, d2, d3 = st.columns(3)
                with d1:
                    qtd = st.number_input("Quantidade *", min_value=0.01, value=1.0, step=0.5,
                                          help=f"Estoque atual: {prod_obj.quantidade:g} {prod_obj.unidade}")
                with d2:
                    preco_default = float(prod_obj.preco_custo) if "Entrada" in tipo else float(prod_obj.preco_venda)
                    preco = st.number_input("Preço unitário (R$)", min_value=0.0, value=preco_default, format="%.2f")
                with d3:
                    total_calc = qtd * preco
                    st.markdown(f"""
                    <div style="background:#2e2010;border:1px solid #4a3420;border-radius:8px;
                                padding:11px;margin-top:24px;text-align:center;">
                        <div style="font-size:10px;color:#9a7d65;text-transform:uppercase;">Total</div>
                        <div style="font-family:'Inconsolata',monospace;font-size:17px;font-weight:700;
                                    color:{'#7ab87a' if 'Entrada' in tipo else '#c0635a'};">
                            R$ {total_calc:,.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                m1, m2 = st.columns(2)
                with m1:
                    MOTIVOS_E = ["Compra de fornecedor","Devolução de cliente","Ajuste de inventário","Transferência","Outro"]
                    MOTIVOS_S = ["Venda","Uso interno","Devolução a fornecedor","Ajuste de inventário","Perda/Avaria","Transferência","Outro"]
                    mot_sel = st.selectbox("Motivo *", MOTIVOS_E if "Entrada" in tipo else MOTIVOS_S)
                with m2:
                    mot_custom = st.text_input("Motivo personalizado", placeholder="Deixar em branco = usar selecionado")

                obs = st.text_area("Observação", placeholder="Nº de nota fiscal, lote, observações...")

                col_sb1, col_sb2 = st.columns([3, 1])
                with col_sb1:
                    submit = st.form_submit_button(
                        f"{'📥 Registrar Entrada' if 'Entrada' in tipo else '📤 Registrar Saída'}",
                        use_container_width=True)

                if submit:
                    tipo_enum = TipoMovimentacao.ENTRADA if "Entrada" in tipo else TipoMovimentacao.SAIDA
                    motivo_final = mot_custom.strip() if mot_custom.strip() else mot_sel
                    try:
                        crud.registrar_movimentacao(db, produto_id=prod_obj.id, tipo=tipo_enum,
                            quantidade=qtd, preco_unitario=preco if preco > 0 else None,
                            motivo=motivo_final, observacao=obs)
                        icone = "📥" if "Entrada" in tipo else "📤"
                        sinal = "+" if "Entrada" in tipo else "−"
                        st.success(f"{icone} Registrado! **{prod_obj.nome}**: {sinal}{qtd:g} {prod_obj.unidade} — R$ {total_calc:,.2f}")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ {e}")

    with col_preview:
        st.markdown('<div class="section-title">📈 Visão Rápida</div>', unsafe_allow_html=True)
        produtos_lista = crud.listar_produtos(db)
        if produtos_lista:
            prod_map_prev = {f"[{p.codigo}] {p.nome}  —  {p.quantidade:g} {p.unidade}": p for p in produtos_lista}
            sel_prev = st.selectbox("Visualizar produto", list(prod_map_prev.keys()), key="prev_prod", label_visibility="collapsed")
            prod_prev = prod_map_prev[sel_prev]
            pct = min((prod_prev.quantidade / prod_prev.estoque_minimo * 100) if prod_prev.estoque_minimo > 0 else 100, 150)
            cor_pct = "#7ab87a" if pct >= 100 else ("#d4a843" if pct >= 50 else "#c0635a")
            status_txt = "✅ Estoque OK" if pct >= 100 else ("⚠️ Atenção: baixo" if pct >= 50 else "🔴 Crítico")

            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#251a0e,#2e2010);border:1px solid #3a2814;
                        border-radius:12px;padding:18px;margin-bottom:12px;">
                <div style="font-size:11px;color:#9a7d65;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">
                    📦 {prod_prev.categoria.nome if prod_prev.categoria else "Sem categoria"}
                </div>
                <div style="font-size:16px;font-weight:700;color:#e8b48a;margin-bottom:12px;">{prod_prev.nome}</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
                    <div style="background:#1a1208;border-radius:8px;padding:10px;">
                        <div style="font-size:10px;color:#6b4c2a;text-transform:uppercase;">Atual</div>
                        <div style="font-family:'Inconsolata',monospace;font-size:19px;font-weight:700;color:{cor_pct};">
                            {prod_prev.quantidade:g} <span style="font-size:11px;color:#9a7d65;">{prod_prev.unidade}</span>
                        </div>
                    </div>
                    <div style="background:#1a1208;border-radius:8px;padding:10px;">
                        <div style="font-size:10px;color:#6b4c2a;text-transform:uppercase;">Mínimo</div>
                        <div style="font-family:'Inconsolata',monospace;font-size:19px;font-weight:700;color:#9a7d65;">
                            {prod_prev.estoque_minimo:g} <span style="font-size:11px;color:#9a7d65;">{prod_prev.unidade}</span>
                        </div>
                    </div>
                    <div style="background:#1a1208;border-radius:8px;padding:10px;">
                        <div style="font-size:10px;color:#6b4c2a;text-transform:uppercase;">Custo</div>
                        <div style="font-family:'Inconsolata',monospace;font-size:14px;font-weight:700;color:#c4956a;">R$ {prod_prev.preco_custo:.2f}</div>
                    </div>
                    <div style="background:#1a1208;border-radius:8px;padding:10px;">
                        <div style="font-size:10px;color:#6b4c2a;text-transform:uppercase;">Venda</div>
                        <div style="font-family:'Inconsolata',monospace;font-size:14px;font-weight:700;color:#c4956a;">R$ {prod_prev.preco_venda:.2f}</div>
                    </div>
                </div>
                <div style="background:#1a1208;border-radius:6px;height:8px;overflow:hidden;margin-bottom:6px;">
                    <div style="width:{min(pct,100):.0f}%;height:100%;background:{cor_pct};border-radius:6px;"></div>
                </div>
                <div style="font-size:11px;color:{cor_pct};">{status_txt} — {min(pct,150):.0f}% do mínimo</div>
            </div>
            """, unsafe_allow_html=True)

            _db3 = get_db()
            ultimas = crud.listar_movimentacoes(_db3, produto_id=prod_prev.id, dias=90)[:6]
            _db3.close()
            if ultimas:
                st.markdown('<div class="section-title">Últimas 6 movimentações</div>', unsafe_allow_html=True)
                for m in ultimas:
                    is_ent = m.tipo == TipoMovimentacao.ENTRADA
                    cor = "#7ab87a" if is_ent else "#c0635a"
                    sinal = "+" if is_ent else "−"
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
                                background:#1f1508;border:1px solid #2e2010;border-radius:8px;margin-bottom:4px;">
                        <span>{"📥" if is_ent else "📤"}</span>
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:12px;color:#c4956a;">{m.criado_em.strftime("%d/%m/%Y %H:%M")}</div>
                            <div style="font-size:11px;color:#9a7d65;">{m.motivo or "—"}</div>
                        </div>
                        <div style="font-family:'Inconsolata',monospace;font-size:14px;font-weight:700;color:{cor};">
                            {sinal}{m.quantidade:g}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ABA 2: HISTÓRICO
# ══════════════════════════════════════════════════════════════
with tab_historico:
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#6b4c2a;text-transform:uppercase;letter-spacing:.1em;margin-bottom:14px;font-weight:600;">🔍 Filtros</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4, fc5 = st.columns([1.6, 1.6, 1.4, 2.2, 2.4])
    with fc1:
        data_ini = st.date_input("📅 De", value=date.today()-timedelta(days=30), key="mov_di")
    with fc2:
        data_fim = st.date_input("📅 Até", value=date.today(), key="mov_df")
    with fc3:
        f_tipo = st.selectbox("Tipo", ["Todos","Entrada","Saída"], key="mov_tipo")
    with fc4:
        prods_l = crud.listar_produtos(db)
        pmap = {"Todos os produtos": None}
        pmap.update({p.nome: p.id for p in prods_l})
        f_prod = st.selectbox("Produto", list(pmap.keys()), key="mov_prod")
    with fc5:
        f_busca = st.text_input("Busca", placeholder="🔍  Motivo, observação, produto...",
                                label_visibility="collapsed", key="mov_busca")
    st.markdown('</div>', unsafe_allow_html=True)

    tipo_enum = None
    if f_tipo == "Entrada": tipo_enum = TipoMovimentacao.ENTRADA
    elif f_tipo == "Saída":  tipo_enum = TipoMovimentacao.SAIDA

    movs = crud.listar_movimentacoes_filtro(db, produto_id=pmap[f_prod], tipo=tipo_enum,
        data_inicio=datetime.combine(data_ini, datetime.min.time()),
        data_fim=datetime.combine(data_fim, datetime.min.time()))
    if f_busca.strip():
        b = f_busca.strip().lower()
        movs = [m for m in movs if
                (m.motivo and b in m.motivo.lower()) or
                (m.observacao and b in m.observacao.lower()) or
                b in m.produto.nome.lower()]

    if movs:
        te = sum(m.quantidade for m in movs if m.tipo == TipoMovimentacao.ENTRADA)
        ts = sum(m.quantidade for m in movs if m.tipo == TipoMovimentacao.SAIDA)
        ve = sum(m.valor_total for m in movs if m.tipo == TipoMovimentacao.ENTRADA)
        vs = sum(m.valor_total for m in movs if m.tipo == TipoMovimentacao.SAIDA)
        vt = ve + vs

        def fmt_brl(v):
            return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon" style="background:rgba(196,149,106,.1);border:1px solid rgba(196,149,106,.25);">📋</div>
                <div class="kpi-label">Registros</div>
                <div class="kpi-value">{len(movs)}</div>
                <div class="kpi-delta">{(date.today()-data_ini).days} dias</div>
                <div class="kpi-bg">📋</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon" style="background:rgba(122,184,122,.1);border:1px solid rgba(122,184,122,.25);">📥</div>
                <div class="kpi-label">Total entradas</div>
                <div class="kpi-value" style="color:#7ab87a;">+{te:g}</div>
                <div class="kpi-delta">{fmt_brl(ve)} em valor</div>
                <div class="kpi-bg">📥</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon" style="background:rgba(192,99,90,.1);border:1px solid rgba(192,99,90,.25);">📤</div>
                <div class="kpi-label">Total saídas</div>
                <div class="kpi-value" style="color:#c0635a;">−{ts:g}</div>
                <div class="kpi-delta">{fmt_brl(vs)} em valor</div>
                <div class="kpi-bg">📤</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon" style="background:rgba(212,137,74,.1);border:1px solid rgba(212,137,74,.25);">💰</div>
                <div class="kpi-label">Valor total</div>
                <div class="kpi-value" style="color:#d4894a;">{fmt_brl(vt)}</div>
                <div class="kpi-delta">Ent. + Saídas</div>
                <div class="kpi-bg">💰</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_exp, _ = st.columns([1, 4])
        with col_exp:
            df_exp = pd.DataFrame([{
                "ID": m.id, "Data": m.criado_em.strftime("%d/%m/%Y %H:%M"),
                "Produto": m.produto.nome, "Código": m.produto.codigo,
                "Tipo": "Entrada" if m.tipo == TipoMovimentacao.ENTRADA else "Saída",
                "Quantidade": float(m.quantidade), "Unidade": m.produto.unidade,
                "Preço Unit.": float(m.preco_unitario or 0), "Valor Total": float(m.valor_total),
                "Motivo": m.motivo or "", "Observação": m.observacao or "",
            } for m in movs])
            csv = df_exp.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
            st.download_button("⬇️ Exportar CSV", data=csv,
                file_name=f"movimentacoes_{data_ini}_{data_fim}.csv",
                mime="text/csv", use_container_width=True)

        st.markdown(f'<div class="section-title" style="margin-top:8px;">📋 {len(movs)} Registro(s)</div>', unsafe_allow_html=True)

        data_atual = None
        for m in movs:
            data_str = m.criado_em.strftime("%Y-%m-%d")
            if data_str != data_atual:
                data_atual = data_str
                dia_disp = m.criado_em.strftime("%A, %d de %B de %Y").capitalize()
                st.markdown(f'<div class="timeline-date">📅  {dia_disp}</div>', unsafe_allow_html=True)

            is_ent = m.tipo == TipoMovimentacao.ENTRADA
            cls    = "entrada" if is_ent else "saida"
            ico    = "📥" if is_ent else "📤"
            sinal  = "+" if is_ent else "−"
            tot_s  = f"R$ {m.valor_total:.2f}".replace(".",",") if m.preco_unitario else "—"
            hora   = m.criado_em.strftime("%H:%M")
            tags   = ""
            if m.motivo: tags += f'<span class="tag">{m.motivo}</span>'
            if m.observacao: tags += '<span class="tag" title="' + m.observacao + '">📝 Obs.</span>'

            col_c, col_p, col_b = st.columns([11, 0.6, 0.6])
            with col_c:
                st.markdown(f"""
                <div class="mov-card {cls}">
                    <div class="mov-avatar {cls}">{ico}</div>
                    <div class="mov-body">
                        <div class="mov-title">{m.produto.nome}</div>
                        <div class="mov-sub">
                            <span style="color:#6b4c2a;">🕐 {hora}</span>
                            <span>SKU: {m.produto.codigo}</span>
                            {tags}
                        </div>
                    </div>
                    <div class="mov-qty {cls}">{sinal}{m.quantidade:g} <span style="font-size:11px;color:#9a7d65;">{m.produto.unidade}</span></div>
                    <div class="mov-value">{tot_s}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_p:
                if st.button("✏️", key=f"mpen_{m.id}", help="Editar", use_container_width=True):
                    st.session_state.mov_edit_id = m.id if st.session_state.mov_edit_id != m.id else None
                    st.session_state.mov_del_id  = None
            with col_b:
                if st.button("🗑️", key=f"mbin_{m.id}", help="Excluir e estornar", use_container_width=True):
                    st.session_state.mov_del_id  = m.id if st.session_state.mov_del_id != m.id else None
                    st.session_state.mov_edit_id = None

            if st.session_state.mov_edit_id == m.id:
                st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                st.markdown(f"**✏️ Editando #{m.id} — {m.produto.nome}**")
                st.caption(f"Tipo: {'📥 Entrada' if is_ent else '📤 Saída'} · {m.criado_em.strftime('%d/%m/%Y %H:%M')}")
                with st.form(f"fmedit_{m.id}"):
                    me1, me2 = st.columns(2)
                    with me1:
                        nqtd   = st.number_input("Nova quantidade", value=float(m.quantidade), min_value=0.01)
                        npreco = st.number_input("Preço unitário (R$)", value=float(m.preco_unitario or 0), min_value=0.0, format="%.2f")
                    with me2:
                        nmot = st.text_input("Motivo", value=m.motivo or "")
                        nobs = st.text_area("Observação", value=m.observacao or "", height=68)
                    novo_total = nqtd * npreco
                    st.markdown(f"""
                    <div style="background:#1a1208;border-radius:8px;padding:10px 14px;margin:8px 0;
                                border:1px solid #3a2814;display:flex;justify-content:space-between;">
                        <span style="font-size:12px;color:#9a7d65;">Novo valor total:</span>
                        <span style="font-family:'Inconsolata',monospace;font-size:16px;font-weight:700;color:#d4894a;">
                            R$ {novo_total:,.2f}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    ms1, ms2 = st.columns(2)
                    with ms1: salvar_m = st.form_submit_button("💾 Salvar", use_container_width=True)
                    with ms2: fechar_m = st.form_submit_button("✖ Fechar", use_container_width=True)
                    if salvar_m:
                        try:
                            crud.editar_movimentacao(db, m.id, nqtd, npreco if npreco > 0 else None, nmot, nobs)
                            st.session_state.mov_edit_id = None
                            st.success("✅ Atualizado! Estoque recalculado.")
                            st.rerun()
                        except ValueError as err:
                            st.error(f"❌ {err}")
                    if fechar_m:
                        st.session_state.mov_edit_id = None
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.mov_del_id == m.id:
                sinal_e = f"−{m.quantidade:g}" if is_ent else f"+{m.quantidade:g}"
                st.markdown(f"""
                <div class="del-panel">
                    <strong style="color:#e89a94;">⚠️ Excluir movimentação #{m.id}?</strong>
                    <div style="font-size:12px;color:#c4956a;margin-top:5px;">
                        Estoque de <strong>{m.produto.nome}</strong> será estornado:
                        <strong style="color:{"#7ab87a" if not is_ent else "#c0635a"}">{sinal_e} {m.produto.unidade}</strong>
                        · Ação irreversível.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                xd1, xd2, _ = st.columns([1.5, 1.5, 7])
                with xd1:
                    if st.button("🗑️ Confirmar", key=f"mxconf_{m.id}", use_container_width=True):
                        try:
                            crud.deletar_movimentacao(db, m.id)
                            st.session_state.mov_del_id = None
                            st.success("✅ Excluída e estoque estornado.")
                            st.rerun()
                        except ValueError as err:
                            st.error(f"❌ {err}")
                with xd2:
                    if st.button("✖ Cancelar", key=f"mxcanc_{m.id}", use_container_width=True):
                        st.session_state.mov_del_id = None
                        st.rerun()
    else:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1f1508,#251a0e);
                    border:1px solid #3a2814;border-radius:14px;
                    padding:48px 28px;text-align:center;color:#9a7d65;margin-top:14px;">
            <div style="font-size:36px;margin-bottom:12px;opacity:.4;">🔍</div>
            <div style="font-size:15px;color:#6b4c2a;font-weight:600;margin-bottom:6px;">Nenhuma movimentação encontrada</div>
            <div style="font-size:13px;">Ajuste os filtros ou amplie o período de busca.</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ABA 3: ANÁLISE VISUAL
# ══════════════════════════════════════════════════════════════
with tab_graficos:
    st.markdown('<div class="section-title">📊 Análise de Movimentações</div>', unsafe_allow_html=True)
    g_dias = st.slider("Período (dias)", min_value=7, max_value=180, value=30, step=7)
    movs_g = crud.listar_movimentacoes(db, dias=g_dias)

    if not movs_g:
        st.info("📭 Sem movimentações no período.")
    else:
        cg1, cg2 = st.columns(2)
        with cg1:
            dados_dia = crud.movimentacoes_por_dia(db, dias=g_dias)
            if dados_dia:
                df_dia = pd.DataFrame([
                    {"Data": str(d.data), "Tipo": "Entrada" if d.tipo == TipoMovimentacao.ENTRADA else "Saída", "Quantidade": float(d.total)}
                    for d in dados_dia])
                fig1 = px.bar(df_dia, x="Data", y="Quantidade", color="Tipo",
                    color_discrete_map={"Entrada":"#7ab87a","Saída":"#c0635a"},
                    barmode="group", title="📈 Movimentações por Dia")
                fig1.update_layout(**plot_layout(320))
                st.plotly_chart(fig1, use_container_width=True)

        with cg2:
            top_prods = crud.top_produtos_movimentados(db, dias=g_dias, limite=8)
            if top_prods:
                df_top = pd.DataFrame([{"Produto": t.nome, "Total": float(t.total_movimentado)} for t in top_prods])
                fig2 = px.bar(df_top.sort_values("Total"), x="Total", y="Produto",
                    orientation="h", title="🏆 Top Produtos",
                    color="Total", color_continuous_scale=["#4a3420","#d4894a","#e8b48a"])
                fig2.update_layout(**plot_layout(320))
                fig2.update_coloraxes(showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

        cg3, cg4 = st.columns(2)
        with cg3:
            n_ent = sum(1 for m in movs_g if m.tipo == TipoMovimentacao.ENTRADA)
            n_sai = sum(1 for m in movs_g if m.tipo == TipoMovimentacao.SAIDA)
            fig3 = go.Figure(data=[go.Pie(
                labels=["Entradas","Saídas"], values=[n_ent, n_sai],
                hole=.55, marker_colors=["#7ab87a","#c0635a"])])
            fig3.update_traces(textfont_size=13, textfont_color="#f5e6d3")
            fig3.update_layout(title="🥧 Entradas vs Saídas", **plot_layout(280),
                annotations=[dict(text=f"{len(movs_g)}<br>total", x=0.5, y=0.5,
                    font_size=15, showarrow=False, font_color="#e8b48a")])
            st.plotly_chart(fig3, use_container_width=True)

        with cg4:
            df_val = pd.DataFrame([{
                "Data": m.criado_em.strftime("%Y-%m-%d"),
                "Tipo": "Entrada" if m.tipo == TipoMovimentacao.ENTRADA else "Saída",
                "Valor": float(m.valor_total)
            } for m in movs_g if m.preco_unitario])
            if not df_val.empty:
                df_vg = df_val.groupby(["Data","Tipo"])["Valor"].sum().reset_index()
                fig4 = px.area(df_vg, x="Data", y="Valor", color="Tipo",
                    color_discrete_map={"Entrada":"#7ab87a","Saída":"#c0635a"},
                    title="💰 Valor Movimentado por Dia (R$)")
                fig4.update_layout(**plot_layout(280))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("💡 Informe o preço nas movimentações para ver este gráfico.")

# ══════════════════════════════════════════════════════════════
# ABA 4: MOVIMENTAÇÃO EM LOTE
# ══════════════════════════════════════════════════════════════
with tab_rapida:
    st.markdown("""
    <div style="background:linear-gradient(145deg,#1f1508,#251a0e);border:1px solid #3a2814;
                border-left:3px solid #d4894a;border-radius:12px;padding:14px 18px;margin-bottom:18px;">
        <strong style="color:#c4956a;">⚡ Movimentação em Lote</strong>
        <p style="font-size:13px;color:#9a7d65;margin:6px 0 0;">
        Registre entradas ou saídas para vários produtos de uma vez. Ideal para recebimentos de NF ou fechamento de vendas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    rl1, rl2 = st.columns(2)
    with rl1:
        tipo_lote = st.radio("Operação", ["📥 Entrada em Lote","📤 Saída em Lote"], horizontal=True)
    with rl2:
        motivo_lote = st.text_input("Motivo do lote", placeholder="Ex: Recebimento NF #1234")

    produtos_lote = crud.listar_produtos(db)
    if produtos_lote:
        st.markdown('<div class="section-title">Selecione produtos e quantidades</div>', unsafe_allow_html=True)
        lc1, lc2, lc3 = st.columns([4, 2, 2])
        with lc1: st.markdown("<small style='color:#6b4c2a;'>PRODUTO</small>", unsafe_allow_html=True)
        with lc2: st.markdown("<small style='color:#6b4c2a;'>ESTOQUE ATUAL</small>", unsafe_allow_html=True)
        with lc3: st.markdown("<small style='color:#6b4c2a;'>QTD. A MOVER</small>", unsafe_allow_html=True)

        selecionados = []
        for p in produtos_lote[:20]:
            lpc1, lpc2, lpc3 = st.columns([4, 2, 2])
            with lpc1:
                sel = st.checkbox(f"**{p.nome}** `{p.codigo}`", key=f"lote_sel_{p.id}")
            with lpc2:
                cor_e = "#7ab87a" if not p.abaixo_do_minimo else "#d4a843"
                st.markdown(f"<div style='padding:8px 0;font-family:Inconsolata,monospace;font-size:14px;font-weight:700;color:{cor_e};'>{p.quantidade:g} {p.unidade}</div>", unsafe_allow_html=True)
            with lpc3:
                if sel:
                    q = st.number_input("Qtd", min_value=0.01, value=1.0, step=1.0,
                                        key=f"lote_qtd_{p.id}", label_visibility="collapsed")
                    selecionados.append((p, q))
                else:
                    st.markdown("<div style='color:#4a3420;padding:8px 0;'>—</div>", unsafe_allow_html=True)

        if selecionados:
            itens_html = "".join([
                f'<div style="font-size:13px;color:#c4956a;padding:2px 0;">{"+" if "Entrada" in tipo_lote else "−"}{q:g} {p.unidade} — {p.nome}</div>'
                for p, q in selecionados
            ])
            st.markdown(f"""
            <div style="background:#1a1208;border:1px solid #3a2814;border-radius:10px;padding:14px 18px;margin:12px 0;">
                <div style="font-size:11px;color:#9a7d65;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Resumo do lote</div>
                {itens_html}
                <div style="margin-top:10px;font-size:13px;color:#e8b48a;font-weight:600;">{len(selecionados)} produto(s) selecionado(s)</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"{'📥 Confirmar Entradas' if 'Entrada' in tipo_lote else '📤 Confirmar Saídas'} em Lote",
                         use_container_width=True):
                tipo_e = TipoMovimentacao.ENTRADA if "Entrada" in tipo_lote else TipoMovimentacao.SAIDA
                erros, ok = [], 0
                for prod, qtd_l in selecionados:
                    try:
                        crud.registrar_movimentacao(db, produto_id=prod.id, tipo=tipo_e, quantidade=qtd_l,
                            motivo=motivo_lote or ("Entrada em lote" if "Entrada" in tipo_lote else "Saída em lote"))
                        ok += 1
                    except ValueError as e:
                        erros.append(f"**{prod.nome}**: {e}")
                if ok: st.success(f"✅ {ok} movimentação(ões) registrada(s)!")
                for e in erros: st.error(f"❌ {e}")
                if ok: st.rerun()
        else:
            st.markdown("<div style='color:#6b4c2a;font-size:13px;text-align:center;padding:20px;'>☝️ Selecione ao menos um produto acima</div>", unsafe_allow_html=True)

db.close()
