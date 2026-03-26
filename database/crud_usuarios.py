import hashlib, secrets, re
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime
from database.models import Usuario, PerfilUsuario


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def _rollback(db):
    try: db.rollback()
    except: pass


def criar_usuario(db: Session, nome: str, login: str,
                  senha: str, perfil: str = "operador",
                  deve_trocar_senha: bool = False) -> Usuario:
    nome  = nome.strip()
    login = login.strip().lower()
    if not nome:  raise ValueError("Nome é obrigatório.")
    if not login: raise ValueError("Login é obrigatório.")
    if len(senha) < 4: raise ValueError("Senha deve ter pelo menos 4 caracteres.")
    dup = db.query(Usuario).filter(func.lower(Usuario.login) == login).first()
    if dup: raise ValueError(f"Login '{login}' já está em uso.")
    try:
        u = Usuario(
            nome=nome,
            login=login,
            senha_hash=_hash(senha),
            perfil=perfil,
            deve_trocar_senha=1 if deve_trocar_senha else 0,
        )
        db.add(u); db.commit(); db.refresh(u)
        return u
    except IntegrityError:
        _rollback(db)
        raise ValueError("Login já existe.")


def autenticar(db: Session, login: str, senha: str) -> dict | None:
    """Autentica e retorna dict com os dados do usuário (sem objeto SQLAlchemy)."""
    login = login.strip().lower()
    u = db.query(Usuario).filter(
        func.lower(Usuario.login) == login,
        Usuario.ativo == 1
    ).first()
    if u and u.senha_hash == _hash(senha):
        u.ultimo_acesso = datetime.utcnow()
        db.commit()
        # Retorna dict para evitar DetachedInstanceError após fechar a sessão
        return {
            "id":     u.id,
            "nome":   u.nome,
            "login":  u.login,
            "perfil": u.perfil.value,
            "deve_trocar_senha": bool(u.deve_trocar_senha),
        }
    return None



def alterar_senha_usuario(db: Session, uid: int, nova_senha: str, obrigar_troca: bool = False) -> Usuario:
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise ValueError("Usuário não encontrado.")
    if len(nova_senha) < 8:
        raise ValueError("A nova senha deve ter pelo menos 8 caracteres.")
    u.senha_hash = _hash(nova_senha)
    u.deve_trocar_senha = 1 if obrigar_troca else 0
    db.commit()
    db.refresh(u)
    return u


def marcar_troca_senha_obrigatoria(db: Session, uid: int, obrigatoria: bool = True) -> Usuario:
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise ValueError("Usuário não encontrado.")
    u.deve_trocar_senha = 1 if obrigatoria else 0
    db.commit()
    db.refresh(u)
    return u

def listar_usuarios(db: Session):
    return db.query(Usuario).order_by(Usuario.nome).all()


def atualizar_usuario(db: Session, uid: int, dados: dict) -> Usuario:
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u: raise ValueError("Usuário não encontrado.")
    if "senha" in dados and dados["senha"]:
        if len(dados["senha"]) < 4:
            raise ValueError("Senha deve ter pelo menos 4 caracteres.")
        u.senha_hash = _hash(dados.pop("senha"))
    for k, v in dados.items():
        setattr(u, k, v)
    db.commit(); db.refresh(u)
    return u


def deletar_usuario(db: Session, uid: int):
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u: raise ValueError("Usuário não encontrado.")
    db.delete(u); db.commit()


def garantir_admin_padrao(db: Session):
    """Cria admin padrão se não houver nenhum usuário."""
    if db.query(Usuario).count() == 0:
        criar_usuario(
            db,
            "Administrador",
            "admin",
            "admin123",
            "admin",
            deve_trocar_senha=True,
        )
        return True
    return False
