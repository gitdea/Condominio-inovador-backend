
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from app.database import engine
from app.models import tabelas
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# AJUSTADO: Agora temos tanto a criptografia quanto o esquema de leitura do token ativos
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Carrega as variáveis do arquivo .env
load_dotenv()

# Carrega as variáveis do arquivo .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "chave_padrao_caso_nao_encontre_o_env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# O int() converte o "30" (texto) para 30 (número inteiro)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Funções auxiliares de segurança
def verificar_senha(senha_pura, senha_criptografada):
    return pwd_context.verify(senha_pura, senha_criptografada)

def gerar_senha_criptografada(senha):
    return pwd_context.hash(senha)

def criar_token_acesso(data: dict):
    dados_para_criptografar = data.copy()
    tempo_expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_para_criptografar.update({"exp": tempo_expiracao})
    return jwt.encode(dados_para_criptografar, SECRET_KEY, algorithm=ALGORITHM)

# Função para pegar a sessão do banco de dados
def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# ROTA DE LOGIN PROFISSIONAL (Gera o Token JWT)
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Busca o condomínio pelo e-mail informado no campo username
    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.email == form_data.username).first()
    
    if not condominio or not verificar_senha(form_data.password, condominio.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Gera o token carregando o ID e o E-mail do condomínio/síndico
    token_acesso = criar_token_acesso(data={"sub": condominio.email, "id": condominio.id})
    
    return {"access_token": token_acesso, "token_type": "bearer"}

# FUNÇÃO DE DEPENDÊNCIA (Para proteger as outras rotas do sistema)
def obter_condominio_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acesso inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica o token usando a sua chave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        condominio_id: int = payload.get("id")
        
        if email is None or condominio_id is None:
            raise credenciais_exception
            
    except jwt.PyJWTError:
        raise credenciais_exception
        
    # Busca no banco para garantir que esse condomínio ainda existe
    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.id == condominio_id).first()
    if condominio is None:
        raise credenciais_exception
        
    return condominio  # Retorna o condomínio logado