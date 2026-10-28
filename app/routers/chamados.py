
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas
# ALTERAÇÃO: dependência que identifica o condomínio logado pelo token.
from app.routers.auth import obter_condominio_atual

router = APIRouter(prefix="/chamados", tags=["Chamados / Solicitações"])


# Rota 1: Criar Chamado (com auditoria)
@router.post("/", response_model=esquemas.SolicitacaoResponse, status_code=status.HTTP_201_CREATED)
def abrir_solicitacao(
    solicitacao: esquemas.SolicitacaoCreate,
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),  # ALTERAÇÃO: exige login
):
    # ALTERAÇÃO (isolamento): o morador precisa pertencer ao condomínio logado. Sem isso, dava para
    # abrir um chamado usando o morador de outro condomínio.
    morador = db.query(tabelas.Morador).filter(
        tabelas.Morador.id == solicitacao.morador_id,
        tabelas.Morador.condominio_id == condominio.id,
    ).first()
    if not morador:
        raise HTTPException(status_code=404, detail="Morador não encontrado.")

    nova_solicitacao = tabelas.Solicitacao(
        condominio_id=condominio.id,  # ALTERAÇÃO: vem do token
        morador_id=morador.id,
        descricao=solicitacao.descricao,
        status=esquemas.StatusEnum.iniciado.value,
    )
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)

    log_auditoria = tabelas.AuditLog(
        condominio_id=condominio.id,
        usuario_responsavel=condominio.email,  # ALTERAÇÃO: quem realmente fez a ação
        acao="CRIAR_CHAMADO",
        tabela_afetada="solicitacoes",
        registro_id=nova_solicitacao.id,
        detalhes={
            "morador_id": morador.id,
            "descricao": nova_solicitacao.descricao,
            "status_inicial": nova_solicitacao.status,
        },
    )
    db.add(log_auditoria)
    db.commit()

    return nova_solicitacao


# Rota 2: Atualizar Status do Chamado (auditoria guarda antes e depois)
@router.patch("/{chamado_id}/status", response_model=esquemas.SolicitacaoResponse)
def atualizar_status_chamado(
    chamado_id: int,
    dados: esquemas.SolicitacaoUpdateStatus,
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),
):
    # ALTERAÇÃO (isolamento): busca pelo id E pelo condomínio logado. Se o chamado é de outro
    # condomínio, a resposta é 404, como se ele não existisse (não revela que existe).
    chamado = db.query(tabelas.Solicitacao).filter(
        tabelas.Solicitacao.id == chamado_id,
        tabelas.Solicitacao.condominio_id == condominio.id,
    ).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    status_anterior = chamado.status
    chamado.status = dados.status.value

    log_auditoria = tabelas.AuditLog(
        condominio_id=condominio.id,
        usuario_responsavel=condominio.email,  # ALTERAÇÃO
        acao="ATUALIZAR_STATUS_CHAMADO",
        tabela_afetada="solicitacoes",
        registro_id=chamado.id,
        detalhes={"status_anterior": status_anterior, "status_novo": chamado.status},
    )
    db.add(log_auditoria)
    db.commit()
    db.refresh(chamado)

    # Aqui, no futuro, entra o disparo do webhook do n8n para avisar o morador no WhatsApp.
    return chamado


# Rota 3: Listar Chamados (apenas leitura)
@router.get("/", response_model=list[esquemas.SolicitacaoResponse])
def listar_chamados(
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),
):
    # ALTERAÇÃO (isolamento): só os chamados do condomínio logado (antes devolvia os de todos).
    return db.query(tabelas.Solicitacao).filter(
        tabelas.Solicitacao.condominio_id == condominio.id
    ).all()