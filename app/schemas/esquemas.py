
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

# Define os status que o chamado pode ter
class StatusEnum(str, Enum):
    iniciado = "Iniciado"
    em_andamento = "Em andamento"
    cancelado = "Cancelado"
    concluido = "Concluído com sucesso"

# SCHEMAS PARA CONDOMÍNIO 
# Dados necessários para cadastrar um condomínio
class CondominioCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, examples=["Condomínio Vista Verde"])
    cnpj: str = Field(..., min_length=14, max_length=18, examples=["12.345.678/0001-99"])
    endereco: str = Field(..., min_length=10, max_length=255, examples=["Rua Flores, 123 - Centro"])

# Como o condomínio será retornado pela API (já com o ID gerado pelo banco)
class CondominioResponse(CondominioCreate):
    id: int

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