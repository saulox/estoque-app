"""
Envio de alertas por e-mail via Gmail SMTP.
Requer: senha de app Google (não a senha normal da conta).
Como gerar: myaccount.google.com → Segurança → Senhas de app
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def enviar_email(remetente: str, senha_app: str,
                 destinatarios: List[str], assunto: str,
                 corpo_html: str) -> dict:
    """
    Envia e-mail via Gmail SMTP.

    Returns:
        dict com 'ok': bool e 'detalhe': str
    """
    if not destinatarios:
        return {"ok": False, "detalhe": "Nenhum destinatário configurado."}
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = f"EstoqueApp <{remetente}>"
        msg["To"]      = ", ".join(destinatarios)
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(remetente, senha_app)
            server.sendmail(remetente, destinatarios, msg.as_string())

        return {"ok": True, "detalhe": f"E-mail enviado para {len(destinatarios)} destinatário(s)."}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "detalhe": "Erro de autenticação. Verifique o e-mail e a senha de app."}
    except smtplib.SMTPConnectError:
        return {"ok": False, "detalhe": "Não foi possível conectar ao servidor SMTP do Gmail."}
    except Exception as e:
        return {"ok": False, "detalhe": str(e)}


def testar_conexao(remetente: str, senha_app: str,
                   destinatarios: List[str]) -> dict:
    """Envia e-mail de teste."""
    html = _template_base(
        titulo="✅ Teste de conexão",
        cor_titulo="#7ab87a",
        corpo="<p>Seu EstoqueApp está configurado corretamente para enviar alertas por e-mail.</p>",
    )
    return enviar_email(remetente, senha_app, destinatarios,
                        "EstoqueApp — Teste de conexão", html)


# ─── Templates HTML ───────────────────────────────────────────────────────────

def _template_base(titulo: str, cor_titulo: str, corpo: str) -> str:
    hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body{{margin:0;padding:0;background:#f0e8dc;font-family:Arial,sans-serif;}}
  .wrap{{max-width:560px;margin:32px auto;background:#fff;border-radius:12px;
         overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);}}
  .header{{background:#2e2010;padding:24px 28px;}}
  .header h1{{margin:0;font-size:20px;color:#e8b48a;font-weight:700;}}
  .header p{{margin:4px 0 0;font-size:12px;color:#9a7d65;}}
  .body{{padding:24px 28px;}}
  .alert-box{{background:#fdf6ef;border:1px solid #d4894a44;border-left:4px solid {cor_titulo};
              border-radius:8px;padding:14px 18px;margin:14px 0;}}
  .alert-title{{font-size:16px;font-weight:700;color:{cor_titulo};margin:0 0 6px;}}
  p{{font-size:14px;color:#4a3420;line-height:1.6;margin:8px 0;}}
  table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;}}
  th{{background:#f5e6d3;color:#6b4c2a;font-weight:700;padding:8px 10px;text-align:left;}}
  td{{padding:8px 10px;border-bottom:1px solid #f0e0cc;color:#2e2010;}}
  .footer{{background:#2e2010;padding:14px 28px;font-size:11px;color:#6b4c2a;text-align:center;}}
</style></head><body>
<div class="wrap">
  <div class="header">
    <h1>📦 EstoqueApp</h1>
    <p>Sistema de Controle de Almoxarifado · {hora}</p>
  </div>
  <div class="body">
    <div class="alert-box">
      <div class="alert-title">{titulo}</div>
    </div>
    {corpo}
  </div>
  <div class="footer">Este é um alerta automático do EstoqueApp. Não responda este e-mail.</div>
</div></body></html>"""


def template_estoque_baixo(produtos: list) -> str:
    linhas = "".join(
        f"<tr><td><strong>{p['nome']}</strong></td>"
        f"<td>{p['codigo']}</td>"
        f"<td style='color:#c0635a;font-weight:700;'>{p['quantidade']:g} {p['unidade']}</td>"
        f"<td>{p['minimo']:g} {p['unidade']}</td></tr>"
        for p in produtos
    )
    corpo = f"""
    <p>{len(produtos)} produto(s) estão com estoque abaixo do mínimo no almoxarifado.</p>
    <table>
      <tr><th>Produto</th><th>Código</th><th>Qtd. Atual</th><th>Mínimo</th></tr>
      {linhas}
    </table>
    <p>Acesse o sistema para verificar e solicitar reposição.</p>"""
    return _template_base("⚠️ Estoque abaixo do mínimo", "#d4a843", corpo)


def template_estoque_zerado(produtos: list) -> str:
    linhas = "".join(
        f"<tr><td><strong>{p['nome']}</strong></td>"
        f"<td>{p['codigo']}</td>"
        f"<td>{p['categoria']}</td></tr>"
        for p in produtos
    )
    corpo = f"""
    <p style='color:#c0635a;font-weight:700;'>{len(produtos)} produto(s) estão com estoque ZERADO.</p>
    <table>
      <tr><th>Produto</th><th>Código</th><th>Categoria</th></tr>
      {linhas}
    </table>
    <p>Ação imediata necessária para evitar paralisação.</p>"""
    return _template_base("🚨 Estoque zerado — reposição urgente", "#c0635a", corpo)


def template_movimentacao(produto: str, codigo: str, tipo: str,
                           quantidade: float, unidade: str,
                           motivo: str, usuario: str = "Sistema") -> str:
    emoji = "📥" if tipo == "entrada" else "📤"
    cor   = "#7ab87a" if tipo == "entrada" else "#c0635a"
    corpo = f"""
    <p>Uma nova movimentação foi registrada no almoxarifado.</p>
    <table>
      <tr><th>Campo</th><th>Valor</th></tr>
      <tr><td>Produto</td><td><strong>{produto}</strong> ({codigo})</td></tr>
      <tr><td>Tipo</td><td style='color:{cor};font-weight:700;'>{emoji} {tipo.capitalize()}</td></tr>
      <tr><td>Quantidade</td><td>{quantidade:g} {unidade}</td></tr>
      <tr><td>Motivo</td><td>{motivo or '—'}</td></tr>
      <tr><td>Registrado por</td><td>{usuario}</td></tr>
    </table>"""
    return _template_base(f"{emoji} Nova movimentação: {produto}", cor, corpo)


def template_inventario(total: int, ajustes: int, sobras: float, faltas: float) -> str:
    corpo = f"""
    <p>Um inventário físico foi concluído no almoxarifado.</p>
    <table>
      <tr><th>Resumo</th><th>Valor</th></tr>
      <tr><td>Produtos contados</td><td>{total}</td></tr>
      <tr><td>Produtos com ajuste</td><td><strong>{ajustes}</strong></td></tr>
      <tr><td>Total de sobras</td><td style='color:#7ab87a;font-weight:700;'>+{sobras:g}</td></tr>
      <tr><td>Total de faltas</td><td style='color:#c0635a;font-weight:700;'>-{faltas:g}</td></tr>
    </table>
    <p>Todos os ajustes foram registrados como movimentações de inventário.</p>"""
    return _template_base("📋 Inventário concluído", "#c4956a", corpo)
