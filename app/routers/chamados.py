
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/chamados", tags=["Chamados / Solicitações"])

# Rota 1: Criar Chamado (Com Auditoria)
@router.post("/", response_model=esquemas.SolicitacaoResponse, status_code=status.HTTP_201_CREATED)
def abrir_solicitacao(solicitacao: esquemas.SolicitacaoCreate, db: Session = Depends(get_db)):
    nova_solicitacao = tabelas.Solicitacao(
        **solicitacao.model_dump(),
        status=esquemas.StatusEnum.iniciado
    )
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)

    # 1. LOG DE AUDITORIA: Registro de criação do chamado
    log_auditoria = tabelas.AuditLog(
        condominio_id=nova_solicitacao.condominio_id,
        usuario_responsavel=f"Morador ID: {nova_solicitacao.morador_id}", # Ou o e-mail do usuário no futuro
        acao="CRIAR_CHAMADO",
        tabela_afetada="solicitacoes",
        registro_id=nova_solicitacao.id,
        detalhes={
            "morador_id": nova_solicitacao.morador_id,
            "descricao": nova_solicitacao.descricao,
            "status_inicial": nova_solicitacao.status
        }
    )
    db.add(log_auditoria)
    db.commit()

    return nova_solicitacao


# Rota 2: Atualizar Status do Chamado (Com Auditoria guardando Antes vs Depois)
@router.patch("/{chamado_id}/status", response_model=esquemas.SolicitacaoResponse)
def atualizar_status_chamado(chamado_id: int, dados: esquemas.SolicitacaoUpdateStatus, db: Session = Depends(get_db)):
    chamado = db.query(tabelas.Solicitacao).filter(tabelas.Solicitacao.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    
    # Guarda o status anterior antes de fazer a alteração no objeto
    status_anterior = chamado.status

    # Atualiza o status com o novo valor
    chamado.status = dados.status.value if hasattr(dados.status, 'value') else dados.status

    # 2. LOG DE AUDITORIA: Registra a mudança de estado e quem solicitou/alterou
    log_auditoria = tabelas.AuditLog(
        condominio_id=chamado.condominio_id,
        usuario_responsavel="Sistema / Síndico / n8n", # Quando integrar com autenticação/n8n passa o identificador
        acao="ATUALIZAR_STATUS_CHAMADO",
        tabela_afetada="solicitacoes",
        registro_id=chamado.id,
        detalhes={
            "status_anterior": status_anterior,
            "status_novo": chamado.status
        }
    )
    db.add(log_auditoria)
    
    db.commit()
    db.refresh(chamado)
    
    # É aqui que no futuro colocamos o disparo para o webhook do n8n avisar o WhatsApp!
    
    return chamado


# Rota 3: Listar Chamados (Sem auditoria, pois é apenas leitura GET)
@router.get("/", response_model=list[esquemas.SolicitacaoResponse])
def listar_todos_chamados(db: Session = Depends(get_db)):
    chamados = db.query(tabelas.Solicitacao).all()
    return chamados