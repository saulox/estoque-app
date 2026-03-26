from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database.connection import Base


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produtos = relationship("Produto", back_populates="categoria")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    codigo = Column(String(50), unique=True, nullable=True)
    descricao = Column(Text, nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    unidade = Column(String(20), default="un")          # ex: un, kg, L, cx
    quantidade = Column(Float, default=0)
    estoque_minimo = Column(Float, default=0)
    preco_custo = Column(Float, default=0)              # preço de compra
    preco_venda = Column(Float, default=0)              # preço de venda
    ativo = Column(Integer, default=1)                  # 1 = ativo, 0 = inativo
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categoria = relationship("Categoria", back_populates="produtos")
    movimentacoes = relationship("Movimentacao", back_populates="produto")

    @property
    def valor_em_estoque(self):
        return self.quantidade * self.preco_custo

    @property
    def abaixo_do_minimo(self):
        return self.quantidade <= self.estoque_minimo

    @property
    def esta_ativo(self):
        return bool(self.ativo)


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(Float, nullable=False)
    preco_unitario = Column(Float, nullable=True)       # preço na hora da mov.
    motivo = Column(String(200), nullable=True)
    observacao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produto = relationship("Produto", back_populates="movimentacoes")

    @property
    def valor_total(self):
        if self.preco_unitario:
            return self.quantidade * self.preco_unitario
        return 0


# ─────────────────────────────────────────────
# NOTAS DE SERVIÇO
# ─────────────────────────────────────────────

class StatusNota(str, enum.Enum):
    RASCUNHO  = "rascunho"
    EMITIDA   = "emitida"
    CANCELADA = "cancelada"


class ConfigEmpresa(Base):
    """Configurações da empresa emitente (1 registro apenas)."""
    __tablename__ = "config_empresa"

    id             = Column(Integer, primary_key=True, default=1)
    razao_social   = Column(String(200), default="")
    nome_fantasia  = Column(String(200), default="")
    cnpj           = Column(String(20),  default="")
    inscricao_mun  = Column(String(30),  default="")
    endereco       = Column(String(300), default="")
    telefone       = Column(String(30),  default="")
    email          = Column(String(100), default="")
    regime_tributario = Column(String(50), default="Simples Nacional")
    aliquota_iss   = Column(Float, default=5.0)   # % padrão de ISS
    observacao_padrao = Column(Text, default="")
    atualizado_em  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Cliente(Base):
    __tablename__ = "clientes"

    id          = Column(Integer, primary_key=True, index=True)
    nome        = Column(String(200), nullable=False)
    cpf_cnpj    = Column(String(20),  nullable=True)
    email       = Column(String(100), nullable=True)
    telefone    = Column(String(30),  nullable=True)
    endereco    = Column(String(300), nullable=True)
    criado_em   = Column(DateTime, default=datetime.utcnow)

    notas = relationship("NotaServico", back_populates="cliente")


class NotaServico(Base):
    __tablename__ = "notas_servico"

    id              = Column(Integer, primary_key=True, index=True)
    numero          = Column(Integer, unique=True, nullable=False)  # sequencial
    cliente_id      = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    status          = Column(Enum(StatusNota), default=StatusNota.RASCUNHO)
    data_emissao    = Column(DateTime, default=datetime.utcnow)
    descricao_geral = Column(Text, nullable=True)
    condicao_pagamento = Column(String(200), default="À vista")
    aliquota_iss    = Column(Float, default=5.0)
    observacoes     = Column(Text, nullable=True)
    criado_em       = Column(DateTime, default=datetime.utcnow)
    atualizado_em   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="notas")
    itens   = relationship("ItemNota", back_populates="nota", cascade="all, delete-orphan")

    @property
    def subtotal(self):
        return sum(i.valor_total for i in self.itens)

    @property
    def valor_iss(self):
        return self.subtotal * (self.aliquota_iss / 100)

    @property
    def valor_total(self):
        return max(self.subtotal - self.valor_iss, 0)  # ISS retido deduz do total

    @property
    def numero_formatado(self):
        return f"{self.numero:06d}"


class ItemNota(Base):
    __tablename__ = "itens_nota"

    id          = Column(Integer, primary_key=True, index=True)
    nota_id     = Column(Integer, ForeignKey("notas_servico.id"), nullable=False)
    descricao   = Column(String(300), nullable=False)
    quantidade  = Column(Float, default=1)
    unidade     = Column(String(20), default="un")
    valor_unit  = Column(Float, default=0)

    nota = relationship("NotaServico", back_populates="itens")

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unit


# ─────────────────────────────────────────────
# CONFIGURAÇÕES DE ALERTAS / NOTIFICAÇÕES
# ─────────────────────────────────────────────

class ConfigAlertas(Base):
    """Configurações de notificações (1 registro apenas)."""
    __tablename__ = "config_alertas"

    id = Column(Integer, primary_key=True, default=1)

    # ── WhatsApp (Evolution API) ──────────────────
    wpp_ativo        = Column(Integer, default=0)   # 0=off 1=on
    wpp_url          = Column(String(300), default="")   # ex: http://localhost:8080
    wpp_instancia    = Column(String(100), default="")
    wpp_token        = Column(String(300), default="")
    wpp_numeros      = Column(Text, default="")     # lista separada por vírgula

    # ── E-mail (Gmail SMTP) ───────────────────────
    email_ativo      = Column(Integer, default=0)
    email_remetente  = Column(String(200), default="")
    email_senha_app  = Column(String(200), default="")  # senha de app Google
    email_destinatarios = Column(Text, default="")      # lista separada por vírgula

    # ── Gatilhos ──────────────────────────────────
    alerta_estoque_minimo  = Column(Integer, default=1)
    alerta_estoque_zerado  = Column(Integer, default=1)
    alerta_movimentacao    = Column(Integer, default=0)
    alerta_inventario      = Column(Integer, default=1)

    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────
# USUÁRIOS E CONTROLE DE ACESSO
# ─────────────────────────────────────────────

class PerfilUsuario(str, enum.Enum):
    ADMIN      = "admin"       # acesso total
    OPERADOR   = "operador"    # movimentações e consultas
    VISUALIZADOR = "visualizador"  # somente leitura


class Usuario(Base):
    __tablename__ = "usuarios"

    id         = Column(Integer, primary_key=True, index=True)
    nome       = Column(String(150), nullable=False)
    login      = Column(String(80),  unique=True, nullable=False)
    senha_hash = Column(String(200), nullable=False)
    perfil     = Column(Enum(PerfilUsuario), default=PerfilUsuario.OPERADOR)
    ativo      = Column(Integer, default=1)
    deve_trocar_senha = Column(Integer, default=0)
    criado_em  = Column(DateTime, default=datetime.utcnow)
    ultimo_acesso = Column(DateTime, nullable=True)


# ─────────────────────────────────────────────
# FORNECEDORES E PEDIDOS DE COMPRA
# ─────────────────────────────────────────────

class StatusPedido(str, enum.Enum):
    PENDENTE  = "pendente"
    ENVIADO   = "enviado"
    RECEBIDO  = "recebido"
    CANCELADO = "cancelado"


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id         = Column(Integer, primary_key=True, index=True)
    nome       = Column(String(200), nullable=False)
    cnpj       = Column(String(20),  nullable=True)
    contato    = Column(String(100), nullable=True)
    telefone   = Column(String(30),  nullable=True)
    email      = Column(String(100), nullable=True)
    endereco   = Column(String(300), nullable=True)
    observacao = Column(Text, nullable=True)
    ativo      = Column(Integer, default=1)
    criado_em  = Column(DateTime, default=datetime.utcnow)

    pedidos    = relationship("PedidoCompra", back_populates="fornecedor")


class PedidoCompra(Base):
    __tablename__ = "pedidos_compra"

    id           = Column(Integer, primary_key=True, index=True)
    numero       = Column(Integer, unique=True, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"), nullable=False)
    status       = Column(Enum(StatusPedido), default=StatusPedido.PENDENTE)
    observacao   = Column(Text, nullable=True)
    criado_em    = Column(DateTime, default=datetime.utcnow)
    recebido_em  = Column(DateTime, nullable=True)

    fornecedor = relationship("Fornecedor", back_populates="pedidos")
    itens      = relationship("ItemPedido", back_populates="pedido",
                              cascade="all, delete-orphan")

    @property
    def numero_formatado(self): return f"PC-{self.numero:05d}"

    @property
    def total(self): return sum(i.total for i in self.itens)


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id          = Column(Integer, primary_key=True, index=True)
    pedido_id   = Column(Integer, ForeignKey("pedidos_compra.id"), nullable=False)
    produto_id  = Column(Integer, ForeignKey("produtos.id"), nullable=True)
    descricao   = Column(String(300), nullable=False)
    quantidade  = Column(Float, default=1)
    unidade     = Column(String(20), default="un")
    preco_unit  = Column(Float, default=0)

    pedido  = relationship("PedidoCompra", back_populates="itens")
    produto = relationship("Produto")

    @property
    def total(self): return self.quantidade * self.preco_unit
