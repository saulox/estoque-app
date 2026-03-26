import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db, init_db
from database import crud_notas
from database.models import StatusNota
# Importação lazy do reportlab — instale com: pip install reportlab
try:
    from gerar_pdf_nota import gerar_pdf_nota
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS, COLORS

st.set_page_config(page_title="Notas de Serviço — EstoqueApp", page_icon="🧾", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
requer_login(["admin", "operador"])
sidebar_nav()
init_db()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

db = get_db()

st.markdown('<div class="page-header">🧾 Notas de Serviço</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Emita, gerencie e baixe notas de serviço em PDF.</div>', unsafe_allow_html=True)

tab_notas, tab_nova, tab_clientes = st.tabs(["📋 Notas Emitidas", "➕ Nova Nota", "👥 Clientes"])


# ─── Aba: Lista de Notas ──────────────────────────────────────────────────────
with tab_notas:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos", "Rascunho", "Emitida", "Cancelada"])
    with col_f2:
        clientes = crud_notas.listar_clientes(db)
        cli_map = {"Todos os clientes": None}
        cli_map.update({c.nome: c.id for c in clientes})
        cli_filtro = st.selectbox("Cliente", list(cli_map.keys()))

    status_enum = None
    if filtro_status == "Rascunho":  status_enum = StatusNota.RASCUNHO
    elif filtro_status == "Emitida": status_enum = StatusNota.EMITIDA
    elif filtro_status == "Cancelada": status_enum = StatusNota.CANCELADA

    notas = crud_notas.listar_notas(db, status=status_enum, cliente_id=cli_map[cli_filtro])

    if notas:
        def badge_status(s):
            cores = {"rascunho": ("#d4a843","#3d2a10"), "emitida": ("#7ab87a","#1a2e1a"), "cancelada": ("#c0635a","#2d0f0f")}
            cor, bg = cores.get(s.value, ("#9a7d65","#2e2010"))
            return f'<span style="background:{bg};color:{cor};border:1px solid {cor}44;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;">{s.value.upper()}</span>'

        dados = [{
            "Nº":        n.numero_formatado,
            "Data":      n.data_emissao.strftime("%d/%m/%Y"),
            "Cliente":   n.cliente.nome,
            "Itens":     len(n.itens),
            "Subtotal":  f"R$ {n.subtotal:,.2f}".replace(",","X").replace(".",",").replace("X","."),
            "ISS":       f"R$ {n.valor_iss:,.2f}".replace(",","X").replace(".",",").replace("X","."),
            "Total":     f"R$ {n.valor_total:,.2f}".replace(",","X").replace(".",",").replace("X","."),
            "Status":    n.status.value.upper(),
        } for n in notas]
        st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
        st.caption(f"{len(notas)} nota(s) encontrada(s).")

        st.markdown('<div class="section-title">📄 Visualizar / Ações</div>', unsafe_allow_html=True)
        nota_map = {f"Nº {n.numero_formatado} — {n.cliente.nome} — {n.status.value.upper()}": n.id for n in notas}
        nota_sel_key = st.selectbox("Selecione a nota", list(nota_map.keys()))
        nota_sel = crud_notas.buscar_nota(db, nota_map[nota_sel_key])

        if nota_sel:
            empresa = crud_notas.get_config_empresa(db)

            # Info rápida
            status_v = nota_sel.status.value
            cor_status = {"emitida":"#7ab87a","cancelada":"#c0635a","rascunho":"#d4a843"}.get(status_v, "#9a7d65")
            st.markdown(f"""
            <div style="background:#2e2010;border:1px solid #4a3420;border-radius:8px;
                        padding:12px 16px;margin-bottom:12px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;">
                <span class="id-badge">Nº {nota_sel.numero_formatado}</span>
                <span style="color:{cor_status};font-weight:700;font-size:13px;">{status_v.upper()}</span>
                <span style="color:#9a7d65;font-size:13px;">Cliente: <strong style="color:#c4956a;">{nota_sel.cliente.nome}</strong></span>
                <span style="color:#9a7d65;font-size:13px;">Total: <strong style="color:#e8b48a;">R$ {nota_sel.valor_total:,.2f}</strong></span>
            </div>""", unsafe_allow_html=True)

            col_pdf, col_emit, col_cancel, col_del = st.columns(4)

            with col_pdf:
                if not REPORTLAB_OK:
                    st.warning("⚠️ Para gerar PDF instale: pip install reportlab")
                else:
                    try:
                        pdf_bytes = gerar_pdf_nota(nota_sel, empresa)
                        st.download_button(
                            "⬇️ Baixar PDF",
                            data=pdf_bytes,
                            file_name=f"nota_{nota_sel.numero_formatado}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {e}")

            with col_emit:
                if nota_sel.status == StatusNota.RASCUNHO:
                    if st.button("✅ Emitir nota", use_container_width=True):
                        try:
                            crud_notas.emitir_nota(db, nota_sel.id)
                            st.success("✅ Nota emitida com sucesso!")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")

            with col_cancel:
                if nota_sel.status != StatusNota.CANCELADA:
                    if st.button("🚫 Cancelar", use_container_width=True):
                        try:
                            crud_notas.cancelar_nota(db, nota_sel.id)
                            st.warning("🚫 Nota cancelada.")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")

            with col_del:
                if nota_sel.status != StatusNota.EMITIDA:
                    if st.button("🗑️ Excluir", use_container_width=True):
                        try:
                            crud_notas.deletar_nota(db, nota_sel.id)
                            st.success("🗑️ Nota excluída.")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")

            # Itens da nota selecionada
            if nota_sel.itens:
                st.markdown('<div class="section-title">📦 Itens da Nota</div>', unsafe_allow_html=True)
                itens_data = [{
                    "Descrição": i.descricao,
                    "Qtd": f"{i.quantidade:g}",
                    "Un": i.unidade,
                    "Valor Unit.": f"R$ {i.valor_unit:.2f}",
                    "Total": f"R$ {i.valor_total:.2f}",
                } for i in nota_sel.itens]
                st.dataframe(pd.DataFrame(itens_data), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma nota encontrada. Use a aba ➕ Nova Nota para criar.")


# ─── Aba: Nova Nota ───────────────────────────────────────────────────────────
with tab_nova:
    clientes = crud_notas.listar_clientes(db)
    empresa  = crud_notas.get_config_empresa(db)

    if not clientes:
        st.warning("⚠️ Cadastre um cliente primeiro na aba 👥 Clientes.")
    else:
        cli_map2 = {c.nome: c.id for c in clientes}

        st.markdown('<div class="section-title">📋 Dados da Nota</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente_sel = st.selectbox("Cliente *", list(cli_map2.keys()))
        with col2:
            condicao_pag = st.selectbox("Condição de Pagamento",
                ["À vista", "30 dias", "30/60 dias", "30/60/90 dias", "Parcelado", "A combinar"])
        with col3:
            iss_aliq = st.number_input("Alíquota ISS (%)", min_value=0.0, max_value=20.0,
                                       value=float(empresa.aliquota_iss), step=0.5, format="%.1f")

        descricao_geral = st.text_area("Descrição geral dos serviços (opcional)",
                                        placeholder="Ex: Serviços de consultoria em TI referente ao mês de março/2026")

        st.markdown('<div class="section-title">📦 Itens / Serviços</div>', unsafe_allow_html=True)

        # Gerenciamento de itens via session_state
        if "itens_nota" not in st.session_state:
            st.session_state.itens_nota = []

        with st.form("form_add_item", clear_on_submit=True):
            ci1, ci2, ci3, ci4 = st.columns([4, 1.2, 1.2, 1.5])
            with ci1: desc_item  = st.text_input("Descrição do serviço *")
            with ci2: qtd_item   = st.number_input("Qtd", min_value=0.01, value=1.0, step=0.5)
            with ci3: un_item    = st.selectbox("Un", ["un", "h", "dia", "mês", "serv", "m²", "m"])
            with ci4: vunit_item = st.number_input("Valor unit. (R$)", min_value=0.0, value=0.0, format="%.2f")
            add_item = st.form_submit_button("➕ Adicionar item", use_container_width=True)
            if add_item:
                if not desc_item.strip():
                    st.error("❌ Informe a descrição do item.")
                elif vunit_item <= 0:
                    st.error("❌ Informe o valor unitário.")
                else:
                    st.session_state.itens_nota.append({
                        "descricao": desc_item.strip(), "quantidade": qtd_item,
                        "unidade": un_item, "valor_unit": vunit_item,
                    })
                    st.rerun()

        if st.session_state.itens_nota:
            dados_itens = [{
                "#": i+1, "Descrição": it["descricao"],
                "Qtd": f"{it['quantidade']:g}", "Un": it["unidade"],
                "Valor Unit.": f"R$ {it['valor_unit']:.2f}",
                "Total": f"R$ {it['quantidade']*it['valor_unit']:.2f}",
            } for i, it in enumerate(st.session_state.itens_nota)]
            st.dataframe(pd.DataFrame(dados_itens), use_container_width=True, hide_index=True)

            subtotal = sum(it["quantidade"] * it["valor_unit"] for it in st.session_state.itens_nota)
            iss_val  = subtotal * (iss_aliq / 100)
            total    = subtotal - iss_val

            def fmt(v): return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            st.markdown(f"""
            <div style="background:#2e2010;border:1px solid #4a3420;border-radius:8px;
                        padding:12px 20px;margin:10px 0;display:flex;gap:30px;flex-wrap:wrap;">
                <span style="color:#9a7d65;font-size:13px;">Subtotal: <strong style="color:#c4956a;">{fmt(subtotal)}</strong></span>
                <span style="color:#9a7d65;font-size:13px;">ISS ({iss_aliq:.1f}%): <strong style="color:#c0635a;">- {fmt(iss_val)}</strong></span>
                <span style="color:#9a7d65;font-size:13px;">Total líquido: <strong style="color:#e8b48a;font-size:16px;">{fmt(total)}</strong></span>
            </div>""", unsafe_allow_html=True)

            if st.button("🗑️ Limpar todos os itens"):
                st.session_state.itens_nota = []
                st.rerun()

        observacoes = st.text_area("Observações (aparece no rodapé da nota)",
                                    value=empresa.observacao_padrao or "",
                                    placeholder="Ex: Obrigado pela preferência! Pagamento via PIX: 00.000.000/0001-00")

        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.button("💾 Salvar como Rascunho", use_container_width=True):
                if not st.session_state.itens_nota:
                    st.error("❌ Adicione pelo menos um item.")
                else:
                    try:
                        nota = crud_notas.criar_nota(
                            db, cliente_id=cli_map2[cliente_sel],
                            itens=st.session_state.itens_nota,
                            descricao_geral=descricao_geral,
                            condicao_pagamento=condicao_pag,
                            aliquota_iss=iss_aliq,
                            observacoes=observacoes,
                        )
                        st.session_state.itens_nota = []
                        st.success(f"💾 Rascunho Nº {nota.numero_formatado} salvo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

        with col_save2:
            if st.button("✅ Salvar e Emitir", use_container_width=True, type="primary"):
                if not st.session_state.itens_nota:
                    st.error("❌ Adicione pelo menos um item.")
                else:
                    try:
                        nota = crud_notas.criar_nota(
                            db, cliente_id=cli_map2[cliente_sel],
                            itens=st.session_state.itens_nota,
                            descricao_geral=descricao_geral,
                            condicao_pagamento=condicao_pag,
                            aliquota_iss=iss_aliq,
                            observacoes=observacoes,
                        )
                        crud_notas.emitir_nota(db, nota.id)
                        st.session_state.itens_nota = []
                        st.success(f"✅ Nota Nº {nota.numero_formatado} emitida!")
                        if REPORTLAB_OK:
                            empresa_cfg = crud_notas.get_config_empresa(db)
                            nota_final  = crud_notas.buscar_nota(db, nota.id)
                            pdf_bytes   = gerar_pdf_nota(nota_final, empresa_cfg)
                            st.download_button("⬇️ Baixar PDF agora", data=pdf_bytes,
                                               file_name=f"nota_{nota.numero_formatado}.pdf",
                                               mime="application/pdf", use_container_width=True)
                        else:
                            st.warning("⚠️ Instale reportlab para gerar PDF: pip install reportlab")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")


# ─── Aba: Clientes ────────────────────────────────────────────────────────────
with tab_clientes:
    clientes = crud_notas.listar_clientes(db)
    col_lista, col_form = st.columns([2, 1])

    with col_lista:
        st.markdown('<div class="section-title">Clientes cadastrados</div>', unsafe_allow_html=True)
        if clientes:
            dados = [{
                "Nome": c.nome, "CPF/CNPJ": c.cpf_cnpj or "—",
                "E-mail": c.email or "—", "Telefone": c.telefone or "—",
                "Notas": len(c.notas),
            } for c in clientes]
            st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)

            st.markdown('<div class="section-title">✏️ Editar / Excluir Cliente</div>', unsafe_allow_html=True)
            cli_edit_map = {c.nome: c.id for c in clientes}
            cli_sel_nome = st.selectbox("Selecione o cliente", list(cli_edit_map.keys()), key="cli_edit")
            c_sel = crud_notas.buscar_cliente(db, cli_edit_map[cli_sel_nome])

            if c_sel:
                with st.form("form_edit_cli"):
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        e_nome  = st.text_input("Nome *",       value=c_sel.nome)
                        e_cpf   = st.text_input("CPF / CNPJ",   value=c_sel.cpf_cnpj or "")
                        e_email = st.text_input("E-mail",       value=c_sel.email or "")
                    with ce2:
                        e_tel   = st.text_input("Telefone",     value=c_sel.telefone or "")
                        e_end   = st.text_area("Endereço",      value=c_sel.endereco or "")
                    cs1, cs2 = st.columns(2)
                    with cs1:
                        salvar_cli = st.form_submit_button("💾 Salvar", use_container_width=True)
                    with cs2:
                        del_cli = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                    if salvar_cli:
                        try:
                            crud_notas.atualizar_cliente(db, c_sel.id, {
                                "nome": e_nome, "cpf_cnpj": e_cpf, "email": e_email,
                                "telefone": e_tel, "endereco": e_end,
                            })
                            st.success("✅ Cliente atualizado!")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")
                    if del_cli:
                        try:
                            crud_notas.deletar_cliente(db, c_sel.id)
                            st.success("🗑️ Cliente removido.")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")
        else:
            st.info("Nenhum cliente cadastrado ainda.")

    with col_form:
        with st.form("form_novo_cli"):
            st.markdown("**Novo cliente**")
            nome_c   = st.text_input("Nome *")
            cpf_c    = st.text_input("CPF / CNPJ")
            email_c  = st.text_input("E-mail")
            tel_c    = st.text_input("Telefone")
            end_c    = st.text_area("Endereço")
            add_cli  = st.form_submit_button("➕ Cadastrar", use_container_width=True)
            if add_cli:
                try:
                    crud_notas.criar_cliente(db, {
                        "nome": nome_c, "cpf_cnpj": cpf_c, "email": email_c,
                        "telefone": tel_c, "endereco": end_c,
                    })
                    st.success("✅ Cliente cadastrado!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {e}")

db.close()
