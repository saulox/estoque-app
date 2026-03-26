"""
Notificador central — orquestra envios de WhatsApp e e-mail.
Importar e usar em qualquer parte do sistema:

    from alertas.notificador import Notificador
    n = Notificador(db)
    n.checar_e_alertar_estoque()
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from datetime import datetime


class Notificador:
    def __init__(self, db: "Session"):
        self.db  = db
        self.cfg = self._carregar_config()

    def _carregar_config(self):
        from database.models import ConfigAlertas
        cfg = self.db.query(ConfigAlertas).filter(ConfigAlertas.id == 1).first()
        if not cfg:
            cfg = ConfigAlertas(id=1)
            self.db.add(cfg)
            self.db.commit()
            self.db.refresh(cfg)
        return cfg

    def _numeros_wpp(self) -> list[str]:
        if not self.cfg.wpp_numeros:
            return []
        return [n.strip() for n in self.cfg.wpp_numeros.split(",") if n.strip()]

    def _destinatarios_email(self) -> list[str]:
        if not self.cfg.email_destinatarios:
            return []
        return [e.strip() for e in self.cfg.email_destinatarios.split(",") if e.strip()]

    # ─── Dispatcher central ───────────────────────────────────────────────────

    def _enviar_wpp(self, mensagem: str) -> list[dict]:
        if not self.cfg.wpp_ativo:
            return []
        from alertas.whatsapp import enviar_whatsapp
        resultados = []
        for num in self._numeros_wpp():
            r = enviar_whatsapp(
                self.cfg.wpp_url, self.cfg.wpp_instancia,
                self.cfg.wpp_token, num, mensagem
            )
            resultados.append({"canal": f"WhatsApp {num}", **r})
        return resultados

    def _enviar_email(self, assunto: str, html: str) -> list[dict]:
        if not self.cfg.email_ativo:
            return []
        from alertas.email_smtp import enviar_email
        r = enviar_email(
            self.cfg.email_remetente,
            self.cfg.email_senha_app,
            self._destinatarios_email(),
            assunto, html,
        )
        return [{"canal": "E-mail", **r}]

    def _disparar(self, assunto: str, html: str, wpp_texto: str) -> list[dict]:
        """Envia por todos os canais ativos e retorna lista de resultados."""
        resultados = []
        resultados += self._enviar_email(assunto, html)
        resultados += self._enviar_wpp(wpp_texto)
        return resultados

    # ─── Alertas de estoque ───────────────────────────────────────────────────

    def checar_e_alertar_estoque(self) -> list[dict]:
        """
        Verifica todos os produtos e dispara alertas conforme configuração.
        Chamar após qualquer movimentação de saída.
        """
        from database.models import Produto
        from alertas.email_smtp import template_estoque_zerado, template_estoque_baixo

        produtos = self.db.query(Produto).filter(Produto.ativo == 1).all()
        zerados  = [p for p in produtos if p.quantidade <= 0]
        baixos   = [p for p in produtos if 0 < p.quantidade <= p.estoque_minimo]

        resultados = []

        if zerados and self.cfg.alerta_estoque_zerado:
            lista = [{"nome": p.nome, "codigo": p.codigo or "—",
                      "categoria": p.categoria.nome if p.categoria else "—"}
                     for p in zerados]
            nomes = ", ".join(p["nome"] for p in lista[:3])
            mais  = f" e mais {len(lista)-3}" if len(lista) > 3 else ""
            wpp   = (f"🚨 *ESTOQUE ZERADO — ALMOXARIFADO*\n\n"
                     f"{len(lista)} produto(s) estão com estoque zerado:\n"
                     f"• {nomes}{mais}\n\n"
                     f"Acesse o sistema para verificar.")
            html  = template_estoque_zerado(lista)
            resultados += self._disparar("🚨 Estoque zerado — ação urgente", html, wpp)

        if baixos and self.cfg.alerta_estoque_minimo:
            lista = [{"nome": p.nome, "codigo": p.codigo or "—",
                      "quantidade": p.quantidade, "unidade": p.unidade,
                      "minimo": p.estoque_minimo}
                     for p in baixos]
            nomes = ", ".join(p["nome"] for p in lista[:3])
            mais  = f" e mais {len(lista)-3}" if len(lista) > 3 else ""
            wpp   = (f"⚠️ *Estoque abaixo do mínimo — Almoxarifado*\n\n"
                     f"{len(lista)} produto(s) precisam de reposição:\n"
                     f"• {nomes}{mais}\n\n"
                     f"Acesse o sistema para mais detalhes.")
            html  = template_estoque_baixo(lista)
            resultados += self._disparar("⚠️ Estoque abaixo do mínimo", html, wpp)

        return resultados

    def alertar_movimentacao(self, produto_nome: str, produto_codigo: str,
                              tipo: str, quantidade: float, unidade: str,
                              motivo: str = "") -> list[dict]:
        """Alerta sobre nova movimentação registrada."""
        if not self.cfg.alerta_movimentacao:
            return []
        from alertas.email_smtp import template_movimentacao
        emoji = "📥" if tipo == "entrada" else "📤"
        html  = template_movimentacao(produto_nome, produto_codigo,
                                      tipo, quantidade, unidade, motivo)
        wpp   = (f"{emoji} *Nova movimentação — Almoxarifado*\n\n"
                 f"Produto: *{produto_nome}* ({produto_codigo})\n"
                 f"Tipo: {tipo.capitalize()}\n"
                 f"Quantidade: {quantidade:g} {unidade}\n"
                 f"Motivo: {motivo or '—'}\n"
                 f"Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        return self._disparar(f"{emoji} Movimentação: {produto_nome}", html, wpp)

    def alertar_inventario(self, total: int, ajustes: int,
                            sobras: float, faltas: float) -> list[dict]:
        """Alerta ao concluir um inventário."""
        if not self.cfg.alerta_inventario:
            return []
        from alertas.email_smtp import template_inventario
        html = template_inventario(total, ajustes, sobras, faltas)
        wpp  = (f"📋 *Inventário concluído — Almoxarifado*\n\n"
                f"• Produtos contados: {total}\n"
                f"• Produtos ajustados: {ajustes}\n"
                f"• Sobras: +{sobras:g}\n"
                f"• Faltas: -{faltas:g}\n\n"
                f"Todos os ajustes foram registrados.")
        return self._disparar("📋 Inventário concluído", html, wpp)
