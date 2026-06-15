
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/condominios", tags=["Condomínios"])

@router.post("/", response_model=esquemas.CondominioResponse, status_code=status.HTTP_201_CREATED)
def criar_condominio(condominio: esquemas.CondominioCreate, db: Session = Depends(get_db)):
    # Verifica se o CNPJ já está cadastrado
    db_condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.cnpj == condominio.cnpj).first()
    if db_condominio:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")
    
    novo_condominio = tabelas.Condominio(**condominio.model_dump())
    db.add(novo_condominio)
    db.commit()
    db.refresh(novo_condominio)
    return novo_condominio

@router.get("/", response_model=List[esquemas.CondominioResponse])
def listar_condominios(db: Session = Depends(get_db)):
    return db.query(tabelas.Condominio).all()