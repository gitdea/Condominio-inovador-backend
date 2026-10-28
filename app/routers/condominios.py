
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import tabelas
from app.schemas import esquemas
# ALTERAÇÃO: reaproveita a função de senha do auth.py (antes havia um segundo CryptContext aqui) e a
# dependência que identifica o condomínio logado.
from app.routers.auth import gerar_senha_criptografada, obter_condominio_atual

router = APIRouter(prefix="/condominios", tags=["Condomínios"])


# Rota 1: Criar Condomínio (cadastro público: é assim que um condomínio novo entra no sistema)
@router.post("/", response_model=esquemas.CondominioResponse, status_code=status.HTTP_201_CREATED)
def criar_condominio(condominio: esquemas.CondominioCreate, db: Session = Depends(get_db)):
    # 1. Verifica se o CNPJ já está cadastrado (o schema já devolve o CNPJ validado e formatado)
    db_condominio = db.query(tabelas.Condominio).filter(tabelas.Condominio.cnpj == condominio.cnpj).first()
    if db_condominio:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    # 2. Verifica se o e-mail já está cadastrado
    db_email = db.query(tabelas.Condominio).filter(tabelas.Condominio.email == condominio.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    # 3. Criptografia da senha
    dados_condominio = condominio.model_dump()
    dados_condominio["senha"] = gerar_senha_criptografada(dados_condominio["senha"])

    # 4. Salva no banco de dados
    novo_condominio = tabelas.Condominio(**dados_condominio)
    db.add(novo_condominio)
    db.commit()
    db.refresh(novo_condominio)

    # 5. Log de auditoria (não guarda a senha)
    log_auditoria = tabelas.AuditLog(
        condominio_id=novo_condominio.id,
        usuario_responsavel=novo_condominio.email,
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


# Rota 2: Dados do condomínio logado
# ALTERAÇÃO (isolamento): no lugar de "GET /" que listava TODOS os condomínios (com e-mails), agora cada
# condomínio vê apenas os próprios dados.
@router.get("/me", response_model=esquemas.CondominioResponse)
def meus_dados(condominio: tabelas.Condominio = Depends(obter_condominio_atual)):
    return condominio


# Rota 3: Logs de auditoria do condomínio logado
# ALTERAÇÃO (isolamento): antes era /{condominio_id}/auditoria, e qualquer pessoa lia o log de qualquer
# condomínio. Agora o condomínio vem do token. Também ganhou paginação (limite e deslocamento).
@router.get("/me/auditoria", response_model=List[esquemas.AuditLogResponse])
def listar_auditoria(
    limite: int = Query(50, ge=1, le=200),
    deslocamento: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    condominio: tabelas.Condominio = Depends(obter_condominio_atual),
):
    return (
        db.query(tabelas.AuditLog)
        .filter(tabelas.AuditLog.condominio_id == condominio.id)
        .order_by(tabelas.AuditLog.data_hora.desc())
        .offset(deslocamento)
        .limit(limite)
        .all()
    )