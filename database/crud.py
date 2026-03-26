import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from database.models import Categoria, Produto, Movimentacao, TipoMovimentacao


def _rollback(db):
    try:
        db.rollback()
    except Exception:
        pass


# ─────────────────────────────────────────────
# CATEGORIAS
# ─────────────────────────────────────────────

def listar_categorias(db: Session):
    return db.query(Categoria).order_by(Categoria.nome).all()


def criar_categoria(db: Session, nome: str, descricao: str = ""):
    nome = nome.strip()
    existente = db.query(Categoria).filter(
        func.lower(Categoria.nome) == nome.lower()
    ).first()
    if existente:
        raise ValueError(f"Já existe uma categoria com o nome '{nome}'.")
    try:
        cat = Categoria(nome=nome, descricao=descricao.strip())
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat
    except IntegrityError:
        _rollback(db)
        raise ValueError(f"Já existe uma categoria com o nome '{nome}'.")
    except Exception:
        _rollback(db)
        raise


def deletar_categoria(db: Session, categoria_id: int):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if cat:
        try:
            db.delete(cat)
            db.commit()
        except IntegrityError:
            _rollback(db)
            raise ValueError("Não é possível excluir: existem produtos vinculados a esta categoria.")
    return cat


# ─────────────────────────────────────────────
# PRODUTOS
# ─────────────────────────────────────────────

def _gerar_codigo_auto(db: Session) -> str:
    """Gera um código único no formato PRD-XXXXXX."""
    while True:
        codigo = "PRD-" + uuid.uuid4().hex[:6].upper()
        existe = db.query(Produto).filter(Produto.codigo == codigo).first()
        if not existe:
            return codigo


def listar_produtos(db: Session, categoria_id: int = None,
                    apenas_alertas: bool = False, incluir_inativos: bool = False):
    q = db.query(Produto)
    if not incluir_inativos:
        q = q.filter(Produto.ativo == 1)
    if categoria_id:
        q = q.filter(Produto.categoria_id == categoria_id)
    produtos = q.order_by(Produto.nome).all()
    if apenas_alertas:
        produtos = [p for p in produtos if p.abaixo_do_minimo]
    return produtos


def buscar_produto(db: Session, produto_id: int):
    return db.query(Produto).filter(Produto.id == produto_id).first()


def criar_produto(db: Session, dados: dict):
    dados = dict(dados)

    # Gera código automático se não foi informado
    if not dados.get("codigo"):
        dados["codigo"] = _gerar_codigo_auto(db)
    else:
        dados["codigo"] = dados["codigo"].strip()
        # Verifica duplicidade de código manual
        existente = db.query(Produto).filter(
            func.lower(Produto.codigo) == dados["codigo"].lower()
        ).first()
        if existente:
            raise ValueError(f"Já existe um produto com o código '{dados['codigo']}'.")

    # Verifica duplicidade de nome
    nome = dados.get("nome", "").strip()
    existente_nome = db.query(Produto).filter(
        func.lower(Produto.nome) == nome.lower()
    ).first()
    if existente_nome:
        raise ValueError(f"Já existe um produto com o nome '{nome}'.")

    if not nome:
        raise ValueError("Nome do produto é obrigatório.")

    for campo in ["quantidade", "estoque_minimo", "preco_custo", "preco_venda"]:
        valor = dados.get(campo, 0)
        if valor is not None and valor < 0:
            raise ValueError(f"O campo '{campo}' não pode ser negativo.")

    dados["nome"] = nome
    try:
        produto = Produto(**dados)
        db.add(produto)
        db.commit()
        db.refresh(produto)
        return produto
    except IntegrityError:
        _rollback(db)
        raise ValueError("Erro ao cadastrar: código ou nome já existe no sistema.")
    except Exception:
        _rollback(db)
        raise


def atualizar_produto(db: Session, produto_id: int, dados: dict):
    produto = buscar_produto(db, produto_id)
    if not produto:
        raise ValueError("Produto não encontrado.")

    dados = dict(dados)
    nome = dados.get("nome", "").strip()
    codigo = dados.get("codigo", "").strip()

    # Verifica duplicidade de nome (ignorando o próprio produto)
    if nome:
        dup = db.query(Produto).filter(
            func.lower(Produto.nome) == nome.lower(),
            Produto.id != produto_id
        ).first()
        if dup:
            raise ValueError(f"Já existe outro produto com o nome '{nome}'.")
        dados["nome"] = nome

    # Verifica duplicidade de código (ignorando o próprio produto)
    if codigo:
        dup = db.query(Produto).filter(
            func.lower(Produto.codigo) == codigo.lower(),
            Produto.id != produto_id
        ).first()
        if dup:
            raise ValueError(f"Já existe outro produto com o código '{codigo}'.")
        dados["codigo"] = codigo

    for campo in ["quantidade", "estoque_minimo", "preco_custo", "preco_venda"]:
        if campo in dados and dados[campo] is not None and dados[campo] < 0:
            raise ValueError(f"O campo '{campo}' não pode ser negativo.")

    try:
        for k, v in dados.items():
            setattr(produto, k, v)
        produto.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(produto)
        return produto
    except IntegrityError:
        _rollback(db)
        raise ValueError("Erro ao atualizar: código ou nome já existe no sistema.")
    except Exception:
        _rollback(db)
        raise


def inativar_produto(db: Session, produto_id: int):
    """Inativa o produto (nunca deleta se tiver movimentações)."""
    produto = buscar_produto(db, produto_id)
    if not produto:
        raise ValueError("Produto não encontrado.")
    tem_movimentacoes = len(produto.movimentacoes) > 0
    if tem_movimentacoes:
        # Só inativa — preserva histórico
        produto.ativo = 0
        produto.atualizado_em = datetime.utcnow()
        db.commit()
        return "inativado"
    else:
        # Sem movimentações: pode excluir definitivamente
        try:
            db.delete(produto)
            db.commit()
        except IntegrityError:
            _rollback(db)
            produto.ativo = 0
            produto.atualizado_em = datetime.utcnow()
            db.commit()
            return "inativado"
        return "excluido"


def reativar_produto(db: Session, produto_id: int):
    """Reativa um produto inativo."""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise ValueError("Produto não encontrado.")
    produto.ativo = 1
    produto.atualizado_em = datetime.utcnow()
    db.commit()
    return produto


def deletar_produto(db: Session, produto_id: int):
    """Mantido para compatibilidade — redireciona para inativar_produto."""
    return inativar_produto(db, produto_id)


# ─────────────────────────────────────────────
# MOVIMENTAÇÕES
# ─────────────────────────────────────────────

def registrar_movimentacao(db: Session, produto_id: int, tipo: str,
                           quantidade: float, preco_unitario: float = None,
                           motivo: str = "", observacao: str = ""):
    produto = buscar_produto(db, produto_id)
    if not produto:
        raise ValueError("Produto não encontrado.")
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")
    if tipo == TipoMovimentacao.SAIDA and produto.quantidade < quantidade:
        raise ValueError(
            f"Quantidade insuficiente. Estoque atual: {produto.quantidade} {produto.unidade}."
        )
    try:
        mov = Movimentacao(
            produto_id=produto_id, tipo=tipo, quantidade=quantidade,
            preco_unitario=preco_unitario, motivo=motivo, observacao=observacao,
        )
        db.add(mov)
        if tipo == TipoMovimentacao.ENTRADA:
            produto.quantidade += quantidade
        else:
            produto.quantidade -= quantidade
        produto.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(mov)
        # Disparar alertas (silencioso — nunca bloqueia a operação)
        try:
            import sys as _sys, os as _os
            _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
            from alertas.notificador import Notificador as _N
            _n = _N(db)
            _n.alertar_movimentacao(produto.nome, produto.codigo or "—",
                                     tipo.value, quantidade, produto.unidade, motivo)
            if tipo == TipoMovimentacao.SAIDA:
                _n.checar_e_alertar_estoque()
        except Exception:
            pass
        return mov
    except Exception:
        _rollback(db)
        raise


def listar_movimentacoes(db: Session, produto_id: int = None,
                         tipo: str = None, dias: int = 30):
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    q = db.query(Movimentacao).filter(Movimentacao.criado_em >= data_inicio)
    if produto_id:
        q = q.filter(Movimentacao.produto_id == produto_id)
    if tipo:
        q = q.filter(Movimentacao.tipo == tipo)
    return q.order_by(desc(Movimentacao.criado_em)).all()


# ─────────────────────────────────────────────
# RELATÓRIOS / DASHBOARD
# ─────────────────────────────────────────────

def resumo_dashboard(db: Session):
    produtos = db.query(Produto).all()
    alertas  = [p for p in produtos if p.abaixo_do_minimo]
    valor    = sum(p.valor_em_estoque for p in produtos)
    movs_hoje = db.query(Movimentacao).filter(
        Movimentacao.criado_em >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    return {
        "total_produtos":      len(produtos),
        "alertas_estoque":     len(alertas),
        "valor_total_estoque": valor,
        "movimentacoes_hoje":  movs_hoje,
        "produtos_alertas":    alertas,
    }


def movimentacoes_por_dia(db: Session, dias: int = 30):
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    return (
        db.query(
            func.date(Movimentacao.criado_em).label("data"),
            Movimentacao.tipo,
            func.sum(Movimentacao.quantidade).label("total"),
        )
        .filter(Movimentacao.criado_em >= data_inicio)
        .group_by(func.date(Movimentacao.criado_em), Movimentacao.tipo)
        .order_by(func.date(Movimentacao.criado_em))
        .all()
    )


def top_produtos_movimentados(db: Session, dias: int = 30, limite: int = 10):
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    return (
        db.query(
            Produto.nome,
            func.sum(Movimentacao.quantidade).label("total_movimentado"),
        )
        .join(Movimentacao)
        .filter(Movimentacao.criado_em >= data_inicio)
        .group_by(Produto.nome)
        .order_by(desc("total_movimentado"))
        .limit(limite)
        .all()
    )


# ─────────────────────────────────────────────
# EDITAR / EXCLUIR MOVIMENTAÇÃO
# ─────────────────────────────────────────────

def buscar_movimentacao(db: Session, mov_id: int):
    return db.query(Movimentacao).filter(Movimentacao.id == mov_id).first()


def editar_movimentacao(db: Session, mov_id: int, nova_quantidade: float,
                        novo_preco: float = None, novo_motivo: str = "",
                        nova_observacao: str = ""):
    """Edita uma movimentação e recalcula o saldo do produto."""
    mov = buscar_movimentacao(db, mov_id)
    if not mov:
        raise ValueError("Movimentação não encontrada.")

    produto = buscar_produto(db, mov.produto_id)
    if not produto:
        raise ValueError("Produto vinculado não encontrado.")

    diff = nova_quantidade - mov.quantidade  # diferença a aplicar

    # Reverter o efeito da movimentação antiga e aplicar a nova
    if mov.tipo == TipoMovimentacao.ENTRADA:
        novo_saldo = produto.quantidade + diff
    else:
        novo_saldo = produto.quantidade - diff

    if novo_saldo < 0:
        raise ValueError(
            f"Edição resultaria em estoque negativo ({novo_saldo:.2f}). "
            f"Estoque atual: {produto.quantidade} {produto.unidade}."
        )

    try:
        mov.quantidade     = nova_quantidade
        mov.preco_unitario = novo_preco if novo_preco and novo_preco > 0 else None
        mov.motivo         = novo_motivo
        mov.observacao     = nova_observacao
        produto.quantidade = novo_saldo
        produto.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(mov)
        return mov
    except Exception:
        _rollback(db)
        raise


def excluir_movimentacao(db: Session, mov_id: int):
    """Exclui a movimentação e estorna o saldo do produto."""
    mov = buscar_movimentacao(db, mov_id)
    if not mov:
        raise ValueError("Movimentação não encontrada.")

    produto = buscar_produto(db, mov.produto_id)
    if produto:
        if mov.tipo == TipoMovimentacao.ENTRADA:
            novo_saldo = produto.quantidade - mov.quantidade
        else:
            novo_saldo = produto.quantidade + mov.quantidade
        if novo_saldo < 0:
            raise ValueError(
                f"Exclusão resultaria em estoque negativo. "
                f"Estoque atual: {produto.quantidade} {produto.unidade}."
            )
        produto.quantidade = novo_saldo
        produto.atualizado_em = datetime.utcnow()

    try:
        db.delete(mov)
        db.commit()
    except Exception:
        _rollback(db)
        raise


def listar_movimentacoes_por_datas(db: Session, data_inicio, data_fim,
                                   produto_id: int = None, tipo: str = None):
    """Filtra movimentações por intervalo de datas exatas."""
    from datetime import datetime as dt
    if isinstance(data_inicio, str):
        data_inicio = dt.strptime(data_inicio, "%Y-%m-%d")
    if isinstance(data_fim, str):
        data_fim = dt.strptime(data_fim, "%Y-%m-%d")
    # inclui o dia final completo
    from datetime import timedelta
    data_fim = data_fim + timedelta(days=1)

    q = db.query(Movimentacao).filter(
        Movimentacao.criado_em >= data_inicio,
        Movimentacao.criado_em < data_fim,
    )
    if produto_id:
        q = q.filter(Movimentacao.produto_id == produto_id)
    if tipo:
        q = q.filter(Movimentacao.tipo == tipo)
    return q.order_by(desc(Movimentacao.criado_em)).all()


# ─────────────────────────────────────────────
# INVENTÁRIO
# ─────────────────────────────────────────────

def ajustar_estoque_inventario(db: Session, produto_id: int,
                                quantidade_contada: float, observacao: str = ""):
    """
    Registra um ajuste de inventário:
    - Se contado > atual → entrada de ajuste
    - Se contado < atual → saída de ajuste
    - Se igual → nenhuma movimentação
    Retorna (movimentacao_ou_None, diferenca)
    """
    produto = buscar_produto(db, produto_id)
    if not produto:
        raise ValueError("Produto não encontrado.")

    diff = quantidade_contada - produto.quantidade
    if diff == 0:
        return None, 0

    tipo = TipoMovimentacao.ENTRADA if diff > 0 else TipoMovimentacao.SAIDA
    motivo = f"Ajuste de inventário"

    try:
        mov = Movimentacao(
            produto_id=produto_id,
            tipo=tipo,
            quantidade=abs(diff),
            preco_unitario=None,
            motivo=motivo,
            observacao=observacao or "Contagem física de estoque",
        )
        db.add(mov)
        produto.quantidade = quantidade_contada
        produto.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(mov)
        return mov, diff
    except Exception:
        _rollback(db)
        raise


# ─────────────────────────────────────────────
# MOVIMENTAÇÕES — EDIÇÃO E FILTRO POR DATA
# ─────────────────────────────────────────────


def listar_movimentacoes_filtro(db: Session, produto_id: int = None,
                                tipo=None, data_inicio=None, data_fim=None):
    q = db.query(Movimentacao)
    if produto_id:
        q = q.filter(Movimentacao.produto_id == produto_id)
    if tipo:
        q = q.filter(Movimentacao.tipo == tipo)
    if data_inicio:
        q = q.filter(Movimentacao.criado_em >= data_inicio)
    if data_fim:
        from datetime import time
        fim_dia = datetime.combine(data_fim.date() if hasattr(data_fim, "date") else data_fim,
                                   time(23, 59, 59))
        q = q.filter(Movimentacao.criado_em <= fim_dia)
    return q.order_by(desc(Movimentacao.criado_em)).all()


def deletar_movimentacao(db: Session, mov_id: int):
    """Compatibilidade: remove movimentação e estorna o estoque."""
    return excluir_movimentacao(db, mov_id)
