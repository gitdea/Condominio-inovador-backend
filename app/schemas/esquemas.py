
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

# Define os status que o chamado pode ter
class StatusEnum(str, Enum):
    iniciado = "Iniciado"
    em_andamento = "Em andamento"
    cancelado = "Cancelado"
    concluido = "Concluído com sucesso"

# Dados necessários para cadastrar um condomínio (Aqui pedimos e-mail e senha)
class CondominioCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, examples=["Condomínio Vista Verde"])
    cnpj: str = Field(..., min_length=14, max_length=18, examples=["12.345.678/0001-99"])
    endereco: str = Field(..., min_length=10, max_length=255, examples=["Rua Flores, 123 - Centro"])
    # ADICIONADOS PARA LOGIN:
    email: EmailStr = Field(..., examples=["sindico@vistaverde.com"]) # Valida automaticamente se é um e-mail real
    senha: str = Field(..., min_length=6, max_length=100, examples=["senha123"])

# Como o condomínio será retornado pela API (PROTEGIDO: NUNCA retorna a senha)
class CondominioResponse(BaseModel):
    id: int
    nome: str
    cnpj: str
    endereco: str
    email: EmailStr

    class Config:
        from_attributes = True


# SCHEMAS PARA PRESTADORES DE SERVIÇO 
class PrestadorCreate(BaseModel):
    condominio_id: int
    nome: str = Field(..., min_length=3, max_length=100)
    categoria: str = Field(..., min_length=3, max_length=50) # Ex: Encanador, Eletricista
    telefone: str = Field(..., min_length=10, max_length=20, examples=["11999998888"])

class PrestadorResponse(PrestadorCreate):
    id: int
    avaliacao_media: int

    class Config:
        from_attributes = True


# SCHEMAS PARA CHAMADOS / SOLICITAÇÕES 
class SolicitacaoCreate(BaseModel):
    condominio_id: int
    morador_id: int
    descricao: str = Field(..., min_length=5)

# Schema usado especificamente quando o síndico ou o n8n atualizar o STATUS do chamado
class SolicitacaoUpdateStatus(BaseModel):
    status: StatusEnum

class SolicitacaoResponse(BaseModel):
    id: int
    condominio_id: int
    morador_id: int
    prestador_id: Optional[int] = None
    descricao: str
    status: StatusEnum

    model_config = {
        "from_attributes": True
    }


# SCHEMAS PARA MORADORES (Onde o n8n e o Painel vão atuar)
# Dados necessários para cadastrar um morador
class MoradorCreate(BaseModel):
    condominio_id: int
    nome: str = Field(..., min_length=3, max_length=100, examples=["Carlos Silva"])
    bloco: str = Field(..., min_length=1, max_length=20, examples=["Bloco B"])
    apartamento: str = Field(..., min_length=1, max_length=20, examples=["Apto 104"])
    whatsapp: str = Field(..., min_length=10, max_length=20, examples=["5511999998888"])

# Como o morador será retornado pela API (já com o ID do banco)
class MoradorResponse(MoradorCreate):
    id: int

    class Config:
        from_attributes = True


# SCHEMAS PARA AUDITORIA 
# Usado para enviar logs manualmente se necessário
class AuditLogCreate(BaseModel):
    condominio_id: int
    usuario_responsavel: str = Field(..., examples=["sindico@vistaverde.com", "Sistema n8n"])
    acao: str = Field(..., examples=["CRIAR", "ATUALIZAR_STATUS", "DELETAR"])
    tabela_afetada: str = Field(..., examples=["solicitacoes", "moradores", "prestadores"])
    registro_id: Optional[int] = Field(None, examples=[12])
    detalhes: Optional[Dict[str, Any]] = Field(None, examples=[{"status_antigo": "Iniciado", "status_novo": "Em andamento"}])

# Como a API vai retornar o log de auditoria ao consultar
class AuditLogResponse(AuditLogCreate):
    id: int
    data_hora: datetime

    class Config:
        from_attributes = True