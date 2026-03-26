"""
Integração com Evolution API para envio de mensagens WhatsApp.
Docs: https://doc.evolution-api.com
"""
import requests
import json
from typing import Optional


def enviar_whatsapp(url: str, instancia: str, token: str,
                    numero: str, mensagem: str) -> dict:
    """
    Envia mensagem WhatsApp via Evolution API.

    Args:
        url: URL base da Evolution API (ex: http://localhost:8080)
        instancia: nome da instância criada na Evolution API
        token: API Key da instância
        numero: número destino com DDI+DDD (ex: 5598999999999)
        mensagem: texto da mensagem

    Returns:
        dict com 'ok': bool e 'detalhe': str
    """
    numero = _normalizar_numero(numero)
    endpoint = f"{url.rstrip('/')}/message/sendText/{instancia}"
    headers  = {"apikey": token, "Content-Type": "application/json"}
    payload  = {
        "number": numero,
        "text": mensagem,
        "delay": 1000,
    }
    try:
        resp = requests.post(endpoint, headers=headers,
                             data=json.dumps(payload), timeout=10)
        if resp.status_code in (200, 201):
            return {"ok": True, "detalhe": "Mensagem enviada com sucesso."}
        return {"ok": False, "detalhe": f"Erro {resp.status_code}: {resp.text[:200]}"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "detalhe": "Não foi possível conectar à Evolution API. Verifique a URL e se o serviço está rodando."}
    except requests.exceptions.Timeout:
        return {"ok": False, "detalhe": "Timeout ao conectar à Evolution API."}
    except Exception as e:
        return {"ok": False, "detalhe": str(e)}


def _normalizar_numero(numero: str) -> str:
    """Remove caracteres não numéricos e garante DDI 55 (Brasil)."""
    n = "".join(c for c in numero if c.isdigit())
    if not n.startswith("55") and len(n) in (10, 11):
        n = "55" + n
    return n


def testar_conexao(url: str, instancia: str, token: str) -> dict:
    """Verifica se a instância está conectada."""
    endpoint = f"{url.rstrip('/')}/instance/connectionState/{instancia}"
    headers  = {"apikey": token}
    try:
        resp = requests.get(endpoint, headers=headers, timeout=8)
        if resp.status_code == 200:
            data   = resp.json()
            estado = data.get("instance", {}).get("state", "unknown")
            if estado == "open":
                return {"ok": True, "detalhe": "✅ WhatsApp conectado e pronto."}
            return {"ok": False, "detalhe": f"Instância no estado: '{estado}'. Escaneie o QR Code."}
        return {"ok": False, "detalhe": f"Erro {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"ok": False, "detalhe": str(e)}
