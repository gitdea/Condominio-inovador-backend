
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/chamados", tags=["Chamados / Solicitações"])

@router.post("/", response_model=esquemas.SolicitacaoResponse, status_code=status.HTTP_201_CREATED)
def abrir_solicitacao(solicitacao: esquemas.SolicitacaoCreate, db: Session = Depends(get_db)):
    nova_solicitacao = tabelas.Solicitacao(
        **solicitacao.model_dump(),
        status=esquemas.StatusEnum.iniciado
    )
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)
    return nova_solicitacao

# Rota que o n8n ou o Síndico vão chamar para mudar o status (Ex: Em andamento -> Concluído)
@router.patch("/{chamado_id}/status", response_model=esquemas.SolicitacaoResponse)
def atualizar_status_chamado(chamado_id: int, dados: esquemas.SolicitacaoUpdateStatus, db: Session = Depends(get_db)):
    chamado = db.query(tabelas.Solicitacao).filter(tabelas.Solicitacao.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    
    chamado.status = dados.status
    db.commit()
    db.refresh(chamado)
    
    # DICA: É aqui que no futuro colocamos o disparo para o webhook do n8n avisar o WhatsApp!
    
    return chamado