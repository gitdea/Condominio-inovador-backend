
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas
from passlib.context import CryptContext

router = APIRouter(prefix="/condominios", tags=["Condomínios"])

# Configuração do hash de senha (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rota 1: Criar Condomínio (Com Auditoria)
@router.post("/", response_model=esquemas.CondominioResponse, status_code=status.HTTP_201_CREATED)
def criar_condominio(condominio: esquemas.CondominioCreate, db: Session = Depends(get_db)):
    # 1. Verifica se o CNPJ já está cadastrado
    db_condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.cnpj == condominio.cnpj).first()
    if db_condominio:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")
    
    # 2. Verifica se o E-mail já está cadastrado
    db_email = db.query(tabelas.Condominio).filter(tabelas.Condominio.email == condominio.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    # 3. Transforma os dados do Pydantic em dicionário
    dados_condominio = condominio.model_dump()
    
    # 4. CRIPTOGRAFIA DA SENHA
    dados_condominio["senha"] = pwd_context.hash(dados_condominio["senha"])
    
    # 5. Salva no banco de dados
    novo_condominio = tabelas.Condominio(**dados_condominio)
    db.add(novo_condominio)
    db.commit()
    db.refresh(novo_condominio)

    # 6. LOG DE AUDITORIA: Registro de criação da conta do condomínio
    log_auditoria = tabelas.AuditLog(
        condominio_id=novo_condominio.id,
        usuario_responsavel=novo_condominio.email, # E-mail do síndico que criou
        acao="CRIAR_CONDOMINIO",
        tabela_afetada="condominios",
        registro_id=novo_condominio.id,
        detalhes={
            "nome": novo_condominio.nome,
            "cnpj": novo_condominio.cnpj,
            "email": novo_condominio.email
        }
    )
    db.add(log_auditoria)
    db.commit()

    return novo_condominio


# Rota 2: Listar Condomínios (Sem auditoria, pois é apenas leitura GET)
@router.get("/", response_model=List[esquemas.CondominioResponse])
def listar_condominios(db: Session = Depends(get_db)):
    return db.query(tabelas.Condominio).all()


# Rota 3: Consultar os Logs de Auditoria do Condomínio
@router.get("/{condominio_id}/auditoria", response_model=List[esquemas.AuditLogResponse])
def listar_auditoria_condominio(condominio_id: int, db: Session = Depends(get_db)):
    # 1. Verifica se o condomínio existe
    condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.id == condominio_id).first()
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")

    # 2. Busca todos os registros de auditoria ordenados do mais recente para o mais antigo
    logs = db.query(tabelas.AuditLog)\
             .filter(tabelas.AuditLog.condominio_id == condominio_id)\
             .order_by(tabelas.AuditLog.data_hora.desc())\
             .all()
             
    return logs