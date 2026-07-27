
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas

router = APIRouter(prefix="/moradores", tags=["Moradores"])

# Rota 1: Cadastrar Morador (Com auditoria!)
@router.post("/", response_model=esquemas.MoradorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_morador(morador: esquemas.MoradorCreate, db: Session = Depends(get_db)):
    # 1. Cria o objeto do novo morador
    novo_morador = tabelas.Morador(**morador.model_dump())
    db.add(novo_morador)
    db.commit()
    db.refresh(novo_morador)

    # 2. CRIA O LOG DE AUDITORIA
    # Guarda o evento de que um novo morador foi cadastrado no sistema
    log_auditoria = tabelas.AuditLog(
        condominio_id=novo_morador.condominio_id,
        usuario_responsavel="Sistema / Painel do Síndico", # Quando você colocar autenticação JWT, aqui vai o e-mail do síndico
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
    
    # 3. Salva o log de auditoria no banco
    db.add(log_auditoria)
    db.commit()

    return novo_morador


# Rota 2: Buscar por WhatsApp (Sem auditoria, pois é apenas leitura GET)
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