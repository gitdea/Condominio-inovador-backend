
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/moradores", tags=["Moradores"])

# Rota 1: Cadastrar Morador (O Síndico vai usar pelo Painel)
@router.post("/", response_model=esquemas.MoradorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_morador(morador: esquemas.MoradorCreate, db: Session = Depends(get_db)):
    novo_morador = tabelas.Morador(**morador.model_dump())
    db.add(novo_morador)
    db.commit()
    db.refresh(novo_morador)
    return novo_morador

# Rota 2: Buscar por WhatsApp (A rota crucial que o n8n vai chamar)
@router.get("/buscar", response_model=esquemas.MoradorResponse)
def buscar_morador_por_whatsapp(whatsapp: str, db: Session = Depends(get_db)):
    # Busca o morador no banco filtrando pelo número de WhatsApp recebido
    morador = db.query(tabelas.Morador).filter(tabelas.Morador.whatsapp == whatsapp).first()
    
    if not morador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Morador com este WhatsApp não foi encontrado."
        )
    
    return morador