
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas
from app.routers.auth import obter_condominio_atual

router = APIRouter(prefix="/moradores", tags=["Moradores"])


# Rota 1: Cadastrar Morador (com auditoria)
@router.post("/", response_model=esquemas.MoradorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_morador(
    morador: esquemas.MoradorCreate,
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),  # ALTERAÇÃO: exige login
):
    # ALTERAÇÃO: o WhatsApp é único na tabela. Sem esta checagem, um número repetido virava erro 500;
    # agora devolve um erro 409 com mensagem clara.
    existente = db.query(tabelas.Morador).filter(tabelas.Morador.whatsapp == morador.whatsapp).first()
    if existente:
        raise HTTPException(status_code=409, detail="Este WhatsApp já está cadastrado.")

    # ALTERAÇÃO (isolamento): o condominio_id vem do token, e não do corpo da requisição.
    novo_morador = tabelas.Morador(**morador.model_dump(), condominio_id=condominio.id)
    db.add(novo_morador)
    db.commit()
    db.refresh(novo_morador)

    log_auditoria = tabelas.AuditLog(
        condominio_id=condominio.id,
        usuario_responsavel=condominio.email,  # ALTERAÇÃO: quem realmente fez a ação
        acao="CRIAR_MORADOR",
        tabela_afetada="moradores",
        registro_id=novo_morador.id,
        detalhes={
            "nome": novo_morador.nome,
            "bloco": novo_morador.bloco,
            "apartamento": novo_morador.apartamento,
            "whatsapp": novo_morador.whatsapp
        }
    )
    db.add(log_auditoria)
    db.commit()

    return novo_morador


# Rota 2: Listar os moradores do condomínio logado (rota nova)
@router.get("/", response_model=List[esquemas.MoradorResponse])
def listar_moradores(
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),
):
    return db.query(tabelas.Morador).filter(tabelas.Morador.condominio_id == condominio.id).all()


# Rota 3: Buscar por WhatsApp (apenas leitura)
@router.get("/buscar", response_model=esquemas.MoradorResponse)
def buscar_morador_por_whatsapp(
    whatsapp: str,
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),
):
    # ALTERAÇÃO (isolamento): busca só dentro do condomínio logado. Antes, qualquer pessoa descobria
    # os dados de um morador de qualquer condomínio só pelo número.
    morador = db.query(tabelas.Morador).filter(
        tabelas.Morador.whatsapp == whatsapp,
        tabelas.Morador.condominio_id == condominio.id,
    ).first()

    if not morador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Morador com este WhatsApp não foi encontrado."
        )

    return morador