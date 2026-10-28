
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
# ALTERAÇÃO: usa o get_db do database.py. Antes havia uma cópia aqui, com outro jeito de abrir a sessão.
from app.database import get_db
from app.models import tabelas
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/auth", tags=["Autenticação"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

load_dotenv()

# ALTERAÇÃO (segurança): antes, se a SECRET_KEY faltasse no .env, o sistema subia com uma chave
# padrão escrita no código, e qualquer pessoa conseguiria forjar tokens. Agora ele não sobe sem a chave.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Defina a variável SECRET_KEY no arquivo .env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


# Funções auxiliares de segurança
def verificar_senha(senha_pura, senha_criptografada):
    return pwd_context.verify(senha_pura, senha_criptografada)


def gerar_senha_criptografada(senha):
    return pwd_context.hash(senha)


def criar_token_acesso(data: dict):
    dados_para_criptografar = data.copy()
    tempo_expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_para_criptografar.update({"exp": tempo_expiracao})
    return jwt.encode(dados_para_criptografar, SECRET_KEY, algorithm=ALGORITHM)


# ROTA DE LOGIN (com auditoria de sucesso e falha)
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.email == form_data.username).first()

    # 1. FALHA NO LOGIN (senha errada ou usuário inexistente)
    if not condominio or not verificar_senha(form_data.password, condominio.senha):
        if condominio:
            log_falha = tabelas.AuditLog(
                condominio_id=condominio.id,
                usuario_responsavel=form_data.username,
                acao="LOGIN_FALHOU",
                tabela_afetada="auth",
                registro_id=condominio.id,
                detalhes={"motivo": "Senha incorreta"}
            )
            db.add(log_falha)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. LOGIN COM SUCESSO
    token_acesso = criar_token_acesso(data={"sub": condominio.email, "id": condominio.id})

    log_sucesso = tabelas.AuditLog(
        condominio_id=condominio.id,
        usuario_responsavel=condominio.email,
        acao="LOGIN_SUCESSO",
        tabela_afetada="auth",
        registro_id=condominio.id,
        detalhes={"tipo_token": "bearer"}
    )
    db.add(log_sucesso)
    db.commit()

    return {
        "access_token": token_acesso,
        "token_type": "bearer",
        "condominio_id": condominio.id
    }


# DEPENDÊNCIA que identifica o condomínio logado pelo token. As rotas protegidas usam esta função.
def obter_condominio_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acesso inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        condominio_id: int = payload.get("id")

        if email is None or condominio_id is None:
            raise credenciais_exception

    except jwt.PyJWTError:
        raise credenciais_exception

    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.id == condominio_id).first()
    if condominio is None:
        raise credenciais_exception

    return condominio