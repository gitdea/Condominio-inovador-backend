
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/prestadores", tags=["Prestadores de Serviço"])

@router.post("/", response_model=esquemas.PrestadorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_prestador(prestador: esquemas.PrestadorCreate, db: Session = Depends(get_db)):
    # Verifica se o condomínio informado existe
    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.id == prestador.condominio_id).first()
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    
    novo_prestador = tabelas.Prestador(**prestador.model_dump(), avaliacao_media=5) # Começa com nota 5
    db.add(novo_prestador)
    db.commit()
    db.refresh(novo_prestador)
    return novo_prestador

@router.get("/condominio/{condominio_id}", response_model=List[esquemas.PrestadorResponse])
def listar_prestadores_por_condominio(condominio_id: int, db: Session = Depends(get_db)):
    return db.query(tabelas.Prestador).filter(tabelas.Prestador.condominio_id == condominio_id).all()