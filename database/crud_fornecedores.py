from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc
from datetime import datetime
from database.models import (Fornecedor, PedidoCompra, ItemPedido,
                              StatusPedido, Produto, TipoMovimentacao,
                              Movimentacao)


def _rollback(db):
    try: db.rollback()
    except: pass


# ── Fornecedores ──────────────────────────────────────────────────────────────

def listar_fornecedores(db: Session, apenas_ativos=True):
    q = db.query(Fornecedor)
    if apenas_ativos: q = q.filter(Fornecedor.ativo == 1)
    return q.order_by(Fornecedor.nome).all()


def criar_fornecedor(db: Session, dados: dict) -> Fornecedor:
    nome = dados.get("nome","").strip()
    if not nome: raise ValueError("Nome do fornecedor é obrigatório.")
    dup = db.query(Fornecedor).filter(
        func.lower(Fornecedor.nome)==nome.lower()).first()
    if dup: raise ValueError(f"Fornecedor '{nome}' já cadastrado.")
    try:
        f = Fornecedor(**{**dados, "nome": nome})
        db.add(f); db.commit(); db.refresh(f); return f
    except IntegrityError:
        _rollback(db); raise ValueError("Erro ao cadastrar fornecedor.")


def atualizar_fornecedor(db: Session, fid: int, dados: dict) -> Fornecedor:
    f = db.query(Fornecedor).filter(Fornecedor.id == fid).first()
    if not f: raise ValueError("Fornecedor não encontrado.")
    nome = dados.get("nome","").strip()
    if nome:
        dup = db.query(Fornecedor).filter(
            func.lower(Fornecedor.nome)==nome.lower(),
            Fornecedor.id != fid).first()
        if dup: raise ValueError(f"Já existe fornecedor com o nome '{nome}'.")
        dados["nome"] = nome
    for k,v in dados.items(): setattr(f, k, v)
    db.commit(); db.refresh(f); return f


def deletar_fornecedor(db: Session, fid: int):
    f = db.query(Fornecedor).filter(Fornecedor.id == fid).first()
    if not f: raise ValueError("Fornecedor não encontrado.")
    if f.pedidos: raise ValueError("Fornecedor possui pedidos — inative-o em vez de excluir.")
    db.delete(f); db.commit()


# ── Pedidos de Compra ─────────────────────────────────────────────────────────

def _proximo_num_pedido(db: Session) -> int:
    m = db.query(func.max(PedidoCompra.numero)).scalar()
    return (m or 0) + 1


def listar_pedidos(db: Session, status=None, fornecedor_id=None):
    q = db.query(PedidoCompra)
    if status:       q = q.filter(PedidoCompra.status == status)
    if fornecedor_id: q = q.filter(PedidoCompra.fornecedor_id == fornecedor_id)
    return q.order_by(desc(PedidoCompra.criado_em)).all()


def buscar_pedido(db: Session, pid: int) -> PedidoCompra:
    return db.query(PedidoCompra).filter(PedidoCompra.id == pid).first()


def criar_pedido(db: Session, fornecedor_id: int, itens: list,
                 observacao: str = "") -> PedidoCompra:
    if not itens:
        raise ValueError("Pedido precisa de ao menos um item.")

    for it in itens:
        if it["quantidade"] <= 0:
            raise ValueError("A quantidade do item deve ser maior que zero.")
        if it["preco_unit"] < 0:
            raise ValueError("O preço unitário não pode ser negativo.")

    try:
        p = PedidoCompra(numero=_proximo_num_pedido(db),
                         fornecedor_id=fornecedor_id, observacao=observacao)
        db.add(p)
        db.flush()
        for it in itens:
            db.add(ItemPedido(pedido_id=p.id, **it))
        db.commit()
        db.refresh(p)
        return p
    except Exception:
        _rollback(db)
        raise


def atualizar_status_pedido(db: Session, pid: int,
                             novo_status: str) -> PedidoCompra:
    p = buscar_pedido(db, pid)
    if not p:
        raise ValueError("Pedido não encontrado.")

    status_anterior = p.status

    if status_anterior == StatusPedido.RECEBIDO and novo_status == StatusPedido.RECEBIDO:
        return p

    if status_anterior == StatusPedido.RECEBIDO and novo_status != StatusPedido.RECEBIDO:
        raise ValueError("Pedido já recebido não pode voltar para outro status.")

    p.status = novo_status

    if novo_status == StatusPedido.RECEBIDO:
        p.recebido_em = datetime.utcnow()
        # Gera entradas automáticas no estoque
        for it in p.itens:
            if it.produto_id:
                prod = db.query(Produto).filter(Produto.id == it.produto_id).first()
                if prod:
                    mov = Movimentacao(
                        produto_id=prod.id,
                        tipo=TipoMovimentacao.ENTRADA,
                        quantidade=it.quantidade,
                        preco_unitario=it.preco_unit or None,
                        motivo=f"Recebimento pedido {p.numero_formatado}",
                        observacao=f"Fornecedor: {p.fornecedor.nome}",
                    )
                    db.add(mov)
                    prod.quantidade += it.quantidade
                    prod.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(p)
    return p


def deletar_pedido(db: Session, pid: int):
    p = buscar_pedido(db, pid)
    if not p: raise ValueError("Pedido não encontrado.")
    if p.status == StatusPedido.RECEBIDO:
        raise ValueError("Pedido já recebido não pode ser excluído.")
    db.delete(p); db.commit()
