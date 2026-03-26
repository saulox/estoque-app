import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db, init_db
from database import crud_notas
from database.models import ConfigAlertas
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import requer_login, sidebar_nav, usuario_atual, eh_admin, eh_operador_ou_admin
from theme import GLOBAL_CSS

st.set_page_config(page_title="Configurações — EstoqueApp", page_icon="⚙️", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.cfg-section {
    background:linear-gradient(145deg,#2e2010,#3a2814);
    border:1px solid #4a3420; border-radius:12px;
    padding:20px 24px; margin-bottom:16px;
}
.cfg-section-title {
    font-family:'Lora',serif; font-size:15px; font-weight:600;
    color:#e8b48a; margin-bottom:14px; display:flex;
    align-items:center; gap:8px;
}
.status-ok  { background:rgba(122,184,122,.15); border:1px solid rgba(122,184,122,.3);
              color:#7ab87a; border-radius:6px; padding:8px 14px; font-size:13px; }
.status-err { background:rgba(192,99,90,.15); border:1px solid rgba(192,99,90,.3);
              color:#e89a94; border-radius:6px; padding:8px 14px; font-size:13px; }
.info-box   { background:rgba(212,137,74,.1); border:1px solid rgba(212,137,74,.25);
              border-left:3px solid #d4894a; border-radius:8px;
              padding:12px 16px; font-size:13px; color:#c4956a; margin-bottom:14px; }
.step-box   { background:#251a0e; border:1px solid #4a3420; border-radius:8px;
              padding:12px 16px; margin-bottom:8px; }
.step-num   { display:inline-block; width:22px; height:22px; background:#d4894a;
              border-radius:50%; color:#1a1208; font-weight:700; font-size:12px;
              text-align:center; line-height:22px; margin-right:8px; flex-shrink:0; }
</style>
""", unsafe_allow_html=True)

init_db()

requer_login(["admin"])
sidebar_nav()

db  = get_db()

# Carrega / cria configs
cfg_emp = crud_notas.get_config_empresa(db)
cfg_alr = db.query(ConfigAlertas).filter(ConfigAlertas.id == 1).first()
if not cfg_alr:
    cfg_alr = ConfigAlertas(id=1)
    db.add(cfg_alr)
    db.commit()
    db.refresh(cfg_alr)

st.markdown('<div class="page-header">⚙️ Configurações</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Dados da empresa, alertas automáticos e notificações.</div>', unsafe_allow_html=True)

tab_empresa, tab_wpp, tab_email, tab_gatilhos = st.tabs([
    "🏢 Empresa", "📱 WhatsApp", "📧 E-mail", "🔔 Gatilhos"
])

# ══════════════════════════════════════════════════════
# ABA: EMPRESA
# ══════════════════════════════════════════════════════
with tab_empresa:
    with st.form("form_cfg_empresa"):
        st.markdown('<div class="section-title">🏢 Dados da Empresa Emitente</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            razao    = st.text_input("Razão Social *",       value=cfg_emp.razao_social)
            fantasia = st.text_input("Nome Fantasia",         value=cfg_emp.nome_fantasia)
            cnpj     = st.text_input("CNPJ",                 value=cfg_emp.cnpj)
            insc_mun = st.text_input("Inscrição Municipal",  value=cfg_emp.inscricao_mun)
        with c2:
            endereco = st.text_area("Endereço completo",     value=cfg_emp.endereco, height=80)
            telefone = st.text_input("Telefone",             value=cfg_emp.telefone)
            email    = st.text_input("E-mail da empresa",    value=cfg_emp.email)
        st.markdown('<div class="section-title">🧾 Fiscal</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            regime = st.selectbox("Regime Tributário",
                       ["Simples Nacional","Lucro Presumido","Lucro Real","MEI"],
                       index=["Simples Nacional","Lucro Presumido","Lucro Real","MEI"].index(
                           cfg_emp.regime_tributario)
                       if cfg_emp.regime_tributario in ["Simples Nacional","Lucro Presumido","Lucro Real","MEI"] else 0)
            iss = st.number_input("Alíquota ISS padrão (%)", min_value=0.0, max_value=20.0,
                                  value=float(cfg_emp.aliquota_iss), step=0.5, format="%.1f")
        with c4:
            obs_pad = st.text_area("Observação padrão nas notas", value=cfg_emp.observacao_padrao or "", height=100)
        if st.form_submit_button("💾 Salvar dados da empresa", use_container_width=True):
            if not razao.strip():
                st.error("❌ Razão Social é obrigatória.")
            else:
                crud_notas.salvar_config_empresa(db, {
                    "razao_social":razao.strip(),"nome_fantasia":fantasia.strip(),
                    "cnpj":cnpj.strip(),"inscricao_mun":insc_mun.strip(),
                    "endereco":endereco.strip(),"telefone":telefone.strip(),
                    "email":email.strip(),"regime_tributario":regime,
                    "aliquota_iss":iss,"observacao_padrao":obs_pad.strip(),
                })
                st.success("✅ Dados da empresa salvos!")

# ══════════════════════════════════════════════════════
# ABA: WHATSAPP
# ══════════════════════════════════════════════════════
with tab_wpp:
    # ── Guia de instalação ────────────────────────────
    with st.expander("📖 Como instalar a Evolution API (clique para ver o guia)", expanded=not cfg_alr.wpp_url):
        st.markdown("""
<div class="info-box">
A <strong>Evolution API</strong> é um servidor local (ou em nuvem) que conecta ao WhatsApp Web
e permite enviar mensagens via requisição HTTP. É gratuita e open source.
</div>

<div class="step-box">
<span class="step-num">1</span>
<strong>Instale o Docker Desktop</strong> — <a href="https://www.docker.com/products/docker-desktop" target="_blank">docker.com/products/docker-desktop</a>
</div>

<div class="step-box">
<span class="step-num">2</span>
<strong>Execute no terminal:</strong>
<pre style="background:#1a1208;color:#e8b48a;padding:10px;border-radius:6px;font-size:12px;margin-top:8px;overflow-x:auto;">docker run -d \\
  --name evolution-api \\
  -p 8080:8080 \\
  -e AUTHENTICATION_API_KEY=minha-chave-secreta \\
  atendai/evolution-api:latest</pre>
</div>

<div class="step-box">
<span class="step-num">3</span>
<strong>Acesse</strong> <code>http://localhost:8080</code> e crie uma instância.
</div>

<div class="step-box">
<span class="step-num">4</span>
<strong>Escaneie o QR Code</strong> com o WhatsApp no celular (igual ao WhatsApp Web).
</div>

<div class="step-box">
<span class="step-num">5</span>
<strong>Preencha abaixo:</strong> URL = <code>http://localhost:8080</code>,
Instância = nome que você criou, Token = a chave usada no passo 2.
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:8px;">📱 Configuração Evolution API</div>', unsafe_allow_html=True)

    with st.form("form_cfg_wpp"):
        wpp_ativo = st.toggle("Ativar alertas por WhatsApp", value=bool(cfg_alr.wpp_ativo))
        c1, c2 = st.columns(2)
        with c1:
            wpp_url      = st.text_input("URL da Evolution API", value=cfg_alr.wpp_url,
                                          placeholder="http://localhost:8080")
            wpp_instancia = st.text_input("Nome da Instância",  value=cfg_alr.wpp_instancia,
                                           placeholder="almoxarifado")
        with c2:
            wpp_token    = st.text_input("API Key / Token",     value=cfg_alr.wpp_token,
                                          type="password", placeholder="minha-chave-secreta")
            wpp_numeros  = st.text_area("Números para alertas",value=cfg_alr.wpp_numeros,
                                         placeholder="5598999999999\n5598888888888",
                                         help="Um número por linha ou separados por vírgula. Incluir DDI+DDD.")
        c_salvar, c_testar = st.columns(2)
        with c_salvar:
            salvo_wpp = st.form_submit_button("💾 Salvar configuração WhatsApp", use_container_width=True)
        with c_testar:
            testar_wpp = st.form_submit_button("🔌 Testar conexão", use_container_width=True)

        if salvo_wpp:
            cfg_alr.wpp_ativo     = 1 if wpp_ativo else 0
            cfg_alr.wpp_url       = wpp_url.strip()
            cfg_alr.wpp_instancia = wpp_instancia.strip()
            cfg_alr.wpp_token     = wpp_token.strip()
            cfg_alr.wpp_numeros   = wpp_numeros.strip()
            db.commit()
            st.success("✅ Configuração WhatsApp salva!")

        if testar_wpp:
            if not wpp_url or not wpp_instancia or not wpp_token:
                st.error("❌ Preencha URL, instância e token antes de testar.")
            else:
                from alertas.whatsapp import testar_conexao, enviar_whatsapp
                res = testar_conexao(wpp_url.strip(), wpp_instancia.strip(), wpp_token.strip())
                if res["ok"]:
                    st.markdown(f'<div class="status-ok">✅ {res["detalhe"]}</div>', unsafe_allow_html=True)
                    # Envia mensagem de teste para o primeiro número
                    nums = [n.strip() for n in wpp_numeros.replace("\n",",").split(",") if n.strip()]
                    if nums:
                        r2 = enviar_whatsapp(wpp_url.strip(), wpp_instancia.strip(),
                                             wpp_token.strip(), nums[0],
                                             "✅ *Teste EstoqueApp*\n\nSeu WhatsApp está configurado corretamente para receber alertas do almoxarifado!")
                        if r2["ok"]:
                            st.success(f"📲 Mensagem de teste enviada para {nums[0]}!")
                        else:
                            st.warning(f"Conexão OK mas falha no envio: {r2['detalhe']}")
                else:
                    st.markdown(f'<div class="status-err">❌ {res["detalhe"]}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# ABA: E-MAIL
# ══════════════════════════════════════════════════════
with tab_email:
    with st.expander("📖 Como configurar o Gmail para envio de alertas", expanded=not cfg_alr.email_remetente):
        st.markdown("""
<div class="info-box">
O Gmail requer uma <strong>Senha de App</strong> — não é a sua senha normal.
É uma senha especial gerada para aplicativos de terceiros.
</div>

<div class="step-box">
<span class="step-num">1</span>
Acesse <a href="https://myaccount.google.com/security" target="_blank">myaccount.google.com/security</a>
</div>

<div class="step-box">
<span class="step-num">2</span>
Ative a <strong>Verificação em duas etapas</strong> (obrigatório para senhas de app).
</div>

<div class="step-box">
<span class="step-num">3</span>
Na mesma página, procure <strong>"Senhas de app"</strong> → Selecione "Outro" → digite "EstoqueApp" → Gerar.
</div>

<div class="step-box">
<span class="step-num">4</span>
Copie a senha de 16 caracteres gerada e cole no campo abaixo.
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:8px;">📧 Configuração Gmail SMTP</div>', unsafe_allow_html=True)

    with st.form("form_cfg_email"):
        email_ativo = st.toggle("Ativar alertas por e-mail", value=bool(cfg_alr.email_ativo))
        c1, c2 = st.columns(2)
        with c1:
            email_rem  = st.text_input("Gmail remetente",     value=cfg_alr.email_remetente,
                                        placeholder="seuemail@gmail.com")
            email_senha = st.text_input("Senha de app (16 dígitos)", value=cfg_alr.email_senha_app,
                                         type="password", placeholder="xxxx xxxx xxxx xxxx")
        with c2:
            email_dest = st.text_area("Destinatários dos alertas", value=cfg_alr.email_destinatarios,
                                       placeholder="gestor@empresa.com\nalmox@empresa.com",
                                       help="Um e-mail por linha ou separados por vírgula.")

        c_salvar2, c_testar2 = st.columns(2)
        with c_salvar2:
            salvo_email = st.form_submit_button("💾 Salvar configuração e-mail", use_container_width=True)
        with c_testar2:
            testar_email = st.form_submit_button("📨 Enviar e-mail de teste", use_container_width=True)

        if salvo_email:
            cfg_alr.email_ativo         = 1 if email_ativo else 0
            cfg_alr.email_remetente     = email_rem.strip()
            cfg_alr.email_senha_app     = email_senha.strip()
            cfg_alr.email_destinatarios = email_dest.strip()
            db.commit()
            st.success("✅ Configuração e-mail salva!")

        if testar_email:
            if not email_rem or not email_senha:
                st.error("❌ Preencha e-mail e senha de app antes de testar.")
            else:
                from alertas.email_smtp import testar_conexao as tc_email
                dests = [e.strip() for e in email_dest.replace("\n",",").split(",") if e.strip()]
                if not dests:
                    st.error("❌ Adicione pelo menos um destinatário.")
                else:
                    res = tc_email(email_rem.strip(), email_senha.strip(), dests)
                    if res["ok"]:
                        st.markdown(f'<div class="status-ok">✅ {res["detalhe"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-err">❌ {res["detalhe"]}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# ABA: GATILHOS
# ══════════════════════════════════════════════════════
with tab_gatilhos:
    st.markdown('<div class="section-title">🔔 Quando disparar alertas</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        Configure quais eventos disparam notificações. Os canais ativos (WhatsApp e/ou e-mail)
        serão usados sempre que o gatilho for acionado.
    </div>""", unsafe_allow_html=True)

    with st.form("form_gatilhos"):
        g1 = st.toggle("🚨 Estoque zerado",
                        value=bool(cfg_alr.alerta_estoque_zerado),
                        help="Dispara quando qualquer produto atingir quantidade 0.")
        g2 = st.toggle("⚠️ Estoque abaixo do mínimo",
                        value=bool(cfg_alr.alerta_estoque_minimo),
                        help="Dispara quando um produto ficar abaixo do estoque mínimo configurado.")
        g3 = st.toggle("🔄 Nova movimentação registrada",
                        value=bool(cfg_alr.alerta_movimentacao),
                        help="Dispara a cada entrada ou saída registrada. Use com cuidado — pode gerar muitos alertas.")
        g4 = st.toggle("📋 Inventário concluído",
                        value=bool(cfg_alr.alerta_inventario),
                        help="Dispara quando um inventário físico é confirmado com ajustes.")

        st.markdown("---")
        st.markdown('<div class="section-title">🧪 Teste manual de alertas</div>', unsafe_allow_html=True)
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            testar_estoque = st.form_submit_button("🔍 Verificar e alertar estoque agora", use_container_width=True)
        with col_t2:
            salvar_gat = st.form_submit_button("💾 Salvar gatilhos", use_container_width=True)

        if salvar_gat:
            cfg_alr.alerta_estoque_zerado  = 1 if g1 else 0
            cfg_alr.alerta_estoque_minimo  = 1 if g2 else 0
            cfg_alr.alerta_movimentacao    = 1 if g3 else 0
            cfg_alr.alerta_inventario      = 1 if g4 else 0
            db.commit()
            st.success("✅ Gatilhos salvos!")

        if testar_estoque:
            from alertas.notificador import Notificador
            with st.spinner("Verificando estoque e disparando alertas..."):
                resultados = Notificador(db).checar_e_alertar_estoque()
            if not resultados:
                st.info("ℹ️ Nenhum alerta foi disparado (sem produtos abaixo do mínimo, ou canais desativados).")
            else:
                for r in resultados:
                    if r["ok"]:
                        st.markdown(f'<div class="status-ok">✅ {r["canal"]}: {r["detalhe"]}</div>',
                                    unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-err">❌ {r["canal"]}: {r["detalhe"]}</div>',
                                    unsafe_allow_html=True)

db.close()
