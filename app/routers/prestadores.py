
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas
from app.routers.auth import obter_condominio_atual

router = APIRouter(prefix="/prestadores", tags=["Prestadores de Serviço"])


# Rota 1: Cadastrar Prestador (com auditoria)
@router.post("/", response_model=esquemas.PrestadorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_prestador(
    prestador: esquemas.PrestadorCreate,
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),  # ALTERAÇÃO: exige login
):
    # ALTERAÇÃO (isolamento): o condomínio vem do token. A checagem "o condomínio existe?" deixou de
    # ser necessária, porque o token já prova que ele existe.
    novo_prestador = tabelas.Prestador(
        **prestador.model_dump(),
        condominio_id=condominio.id,
        avaliacao_media=5,  # Começa com nota 5
    )
    db.add(novo_prestador)
    db.commit()
    db.refresh(novo_prestador)

    log_auditoria = tabelas.AuditLog(
        condominio_id=condominio.id,
        usuario_responsavel=condominio.email,  # ALTERAÇÃO: quem realmente fez a ação
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


# Rota 2: Listar os prestadores do condomínio logado (apenas leitura)
# ALTERAÇÃO (isolamento): antes era /condominio/{condominio_id}, e qualquer pessoa listava os
# prestadores de qualquer condomínio. Agora a rota é "/" e usa o condomínio do token.
@router.get("/", response_model=List[esquemas.PrestadorResponse])
def listar_prestadores(
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),
):
    return db.query(tabelas.Prestador).filter(tabelas.Prestador.condominio_id == condominio.id).all()