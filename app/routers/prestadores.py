
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/prestadores", tags=["Prestadores de Serviço"])

# Rota 1: Cadastrar Prestador (Com Auditoria)
@router.post("/", response_model=esquemas.PrestadorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_prestador(prestador: esquemas.PrestadorCreate, db: Session = Depends(get_db)):
    # 1. Verifica se o condomínio informado existe
    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.id == prestador.condominio_id).first()
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    
    # 2. Cria o prestador no banco
    novo_prestador = tabelas.Prestador(**prestador.model_dump(), avaliacao_media=5) # Começa com nota 5
    db.add(novo_prestador)
    db.commit()
    db.refresh(novo_prestador)

    # 3. LOG DE AUDITORIA: Registro de novo prestador de serviço cadastrado
    log_auditoria = tabelas.AuditLog(
        condominio_id=novo_prestador.condominio_id,
        usuario_responsavel="Sistema / Painel do Síndico",
        acao="CRIAR_PRESTADOR",
        tabela_afetada="prestadores",
        registro_id=novo_prestador.id,
        detalhes={
            "nome": novo_prestador.nome,
            "categoria": novo_prestador.categoria,
            "telefone": novo_prestador.telefone
        }
    )
    db.add(log_auditoria)
    db.commit()

    return novo_prestador


# Rota 2: Listar Prestadores do Condomínio (Sem auditoria, pois é apenas leitura GET)
@router.get("/condominio/{condominio_id}", response_model=List[esquemas.PrestadorResponse])
def listar_prestadores_por_condominio(condominio_id: int, db: Session = Depends(get_db)):
    return db.query(tabelas.Prestador).filter(tabelas.Prestador.condominio_id == condominio_id).all()