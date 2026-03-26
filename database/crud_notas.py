from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from database.models import ConfigEmpresa, Cliente, NotaServico, ItemNota, StatusNota


def _rollback(db):
    try: db.rollback()
    except: pass


# ─── CONFIG EMPRESA ───────────────────────────────────────────────────────────

def get_config_empresa(db: Session) -> ConfigEmpresa:
    cfg = db.query(ConfigEmpresa).filter(ConfigEmpresa.id == 1).first()
    if not cfg:
        cfg = ConfigEmpresa(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def salvar_config_empresa(db: Session, dados: dict) -> ConfigEmpresa:
    cfg = get_config_empresa(db)
    for k, v in dados.items():
        setattr(cfg, k, v)
    cfg.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(cfg)
    return cfg


# ─── CLIENTES ─────────────────────────────────────────────────────────────────

def listar_clientes(db: Session):
    return db.query(Cliente).order_by(Cliente.nome).all()


def buscar_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def criar_cliente(db: Session, dados: dict) -> Cliente:
    nome = dados.get("nome", "").strip()
    if not nome:
        raise ValueError("O nome do cliente é obrigatório.")
    dup = db.query(Cliente).filter(func.lower(Cliente.nome) == nome.lower()).first()
    if dup:
        raise ValueError(f"Já existe um cliente com o nome '{nome}'.")
    try:
        c = Cliente(**{**dados, "nome": nome})
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    except IntegrityError:
        _rollback(db)
        raise ValueError("Erro ao cadastrar cliente.")


def atualizar_cliente(db: Session, cliente_id: int, dados: dict) -> Cliente:
    c = buscar_cliente(db, cliente_id)
    if not c:
        raise ValueError("Cliente não encontrado.")
    nome = dados.get("nome", "").strip()
    if nome:
        dup = db.query(Cliente).filter(
            func.lower(Cliente.nome) == nome.lower(), Cliente.id != cliente_id
        ).first()
        if dup:
            raise ValueError(f"Já existe outro cliente com o nome '{nome}'.")
        dados["nome"] = nome
    for k, v in dados.items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


def deletar_cliente(db: Session, cliente_id: int):
    c = buscar_cliente(db, cliente_id)
    if not c:
        raise ValueError("Cliente não encontrado.")
    if c.notas:
        raise ValueError("Não é possível excluir: cliente possui notas emitidas.")
    db.delete(c)
    db.commit()


# ─── NOTAS DE SERVIÇO ─────────────────────────────────────────────────────────

def _proximo_numero(db: Session) -> int:
    max_num = db.query(func.max(NotaServico.numero)).scalar()
    return (max_num or 0) + 1


def listar_notas(db: Session, status: str = None, cliente_id: int = None):
    q = db.query(NotaServico)
    if status:
        q = q.filter(NotaServico.status == status)
    if cliente_id:
        q = q.filter(NotaServico.cliente_id == cliente_id)
    return q.order_by(NotaServico.numero.desc()).all()


def buscar_nota(db: Session, nota_id: int) -> NotaServico:
    return db.query(NotaServico).filter(NotaServico.id == nota_id).first()


def criar_nota(db: Session, cliente_id: int, itens: list[dict],
               descricao_geral: str = "", condicao_pagamento: str = "À vista",
               aliquota_iss: float = 5.0, observacoes: str = "") -> NotaServico:
    if not itens:
        raise ValueError("A nota precisa ter pelo menos um item.")

    for item in itens:
        if item["quantidade"] <= 0:
            raise ValueError("A quantidade do item deve ser maior que zero.")
        if item["valor_unit"] < 0:
            raise ValueError("O valor unitário do item não pode ser negativo.")

    try:
        nota = NotaServico(
            numero=_proximo_numero(db),
            cliente_id=cliente_id,
            descricao_geral=descricao_geral,
            condicao_pagamento=condicao_pagamento,
            aliquota_iss=aliquota_iss,
            observacoes=observacoes,
            status=StatusNota.RASCUNHO,
        )
        db.add(nota)
        db.flush()
        for item in itens:
            db.add(ItemNota(
                nota_id=nota.id,
                descricao=item["descricao"],
                quantidade=item["quantidade"],
                unidade=item.get("unidade", "un"),
                valor_unit=item["valor_unit"],
            ))
        db.commit()
        db.refresh(nota)
        return nota
    except Exception:
        _rollback(db)
        raise


def emitir_nota(db: Session, nota_id: int) -> NotaServico:
    nota = buscar_nota(db, nota_id)
    if not nota:
        raise ValueError("Nota não encontrada.")
    if nota.status == StatusNota.CANCELADA:
        raise ValueError("Nota cancelada não pode ser emitida.")
    nota.status = StatusNota.EMITIDA
    nota.data_emissao = datetime.utcnow()
    db.commit()
    db.refresh(nota)
    return nota


def cancelar_nota(db: Session, nota_id: int) -> NotaServico:
    nota = buscar_nota(db, nota_id)
    if not nota:
        raise ValueError("Nota não encontrada.")
    nota.status = StatusNota.CANCELADA
    db.commit()
    db.refresh(nota)
    return nota


def deletar_nota(db: Session, nota_id: int):
    nota = buscar_nota(db, nota_id)
    if not nota:
        raise ValueError("Nota não encontrada.")
    if nota.status == StatusNota.EMITIDA:
        raise ValueError("Nota emitida não pode ser excluída. Cancele primeiro.")
    db.delete(nota)
    db.commit()
