
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas
from passlib.context import CryptContext

router = APIRouter(prefix="/condominios", tags=["Condomínios"])

# Configuração do hash de senha (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=esquemas.CondominioResponse, status_code=status.HTTP_201_CREATED)
def criar_condominio(condominio: esquemas.CondominioCreate, db: Session = Depends(get_db)):
    # 1. Verifica se o CNPJ já está cadastrado
    db_condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.cnpj == condominio.cnpj).first()
    if db_condominio:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")
    
    # 2. Verifica se o E-mail já está cadastrado (Boa prática para evitar duplicidade de login)
    db_email = db.query(tabelas.Condominio).filter(tabelas.Condominio.email == condominio.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    # 3. Transforma os dados do Pydantic em dicionário
    dados_condominio = condominio.model_dump()
    
    # 4. CRIPTOGRAFIA DA SENHA: Altera a senha pura pelo hash seguro antes de salvar
    dados_condominio["senha"] = pwd_context.hash(dados_condominio["senha"])
    
    # 5. Salva no banco de dados
    novo_condominio = tabelas.Condominio(**dados_condominio)
    db.add(novo_condominio)
    db.commit()
    db.refresh(novo_condominio)
    return novo_condominio

@router.get("/", response_model=List[esquemas.CondominioResponse])
def listar_condominios(db: Session = Depends(get_db)):
    return db.query(tabelas.Condominio).all()