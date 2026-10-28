
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ALTERAÇÃO (CNPJ): antes só conferíamos o tamanho. Agora calculamos os dois dígitos verificadores
# (regra oficial do módulo 11) e guardamos sempre no formato 00.000.000/0000-00, para o mesmo CNPJ
# não ser cadastrado duas vezes só porque foi digitado com pontuação diferente.
def validar_e_formatar_cnpj(cnpj: str) -> str:
    numeros = re.sub(r"\D", "", cnpj)
    if len(numeros) != 14 or numeros == numeros[0] * 14:
        raise ValueError("CNPJ inválido.")

    def digito(base: str) -> str:
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if len(base) == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        resto = sum(int(n) * p for n, p in zip(base, pesos)) % 11
        return "0" if resto < 2 else str(11 - resto)

    d1 = digito(numeros[:12])
    d2 = digito(numeros[:12] + d1)
    if numeros[12:] != d1 + d2:
        raise ValueError("CNPJ inválido.")
    return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"


# Define os status que o chamado pode ter
class StatusEnum(str, Enum):
    iniciado = "Iniciado"
    em_andamento = "Em andamento"
    cancelado = "Cancelado"
    concluido = "Concluído com sucesso"


# Dados necessários para cadastrar um condomínio (Aqui pedimos e-mail e senha)
class CondominioCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, examples=["Condomínio Vista Verde"])
    # ALTERAÇÃO: o exemplo agora é um CNPJ de teste válido (o antigo não passaria na validação).
    cnpj: str = Field(..., min_length=14, max_length=18, examples=["11.222.333/0001-81"])
    endereco: str = Field(..., min_length=10, max_length=255, examples=["Rua Flores, 123 - Centro"])
    email: EmailStr = Field(..., examples=["sindico@vistaverde.com"])
    senha: str = Field(..., min_length=6, max_length=100, examples=["senha123"])

    @field_validator("cnpj")
    @classmethod
    def cnpj_deve_ser_valido(cls, valor: str) -> str:
        return validar_e_formatar_cnpj(valor)


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
# ALTERAÇÃO (isolamento): o condominio_id saiu do que o cliente envia. Ele vem do token de login.
class PrestadorCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    categoria: str = Field(..., min_length=3, max_length=50)  # Ex: Encanador, Eletricista
    telefone: str = Field(..., min_length=10, max_length=20, examples=["11999998888"])


# ALTERAÇÃO: a resposta agora é declarada por completo (antes herdava do Create, que tinha o condominio_id).
class PrestadorResponse(BaseModel):
    id: int
    condominio_id: int
    nome: str
    categoria: str
    telefone: str
    avaliacao_media: int

    class Config:
        from_attributes = True


# SCHEMAS PARA CHAMADOS / SOLICITAÇÕES
# ALTERAÇÃO (isolamento): sem condominio_id aqui. O condomínio vem do token.
class SolicitacaoCreate(BaseModel):
    morador_id: int
    descricao: str = Field(..., min_length=5)


# Schema usado quando o síndico ou o n8n atualizar o STATUS do chamado
class SolicitacaoUpdateStatus(BaseModel):
    status: StatusEnum


class SolicitacaoResponse(BaseModel):
    id: int
    condominio_id: int
    morador_id: int
    prestador_id: Optional[int] = None
    descricao: str
    status: StatusEnum

    model_config = {"from_attributes": True}


# SCHEMAS PARA MORADORES
# ALTERAÇÃO (isolamento): sem condominio_id. O morador sempre entra no condomínio de quem está logado.
class MoradorCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, examples=["Carlos Silva"])
    bloco: str = Field(..., min_length=1, max_length=20, examples=["Bloco B"])
    apartamento: str = Field(..., min_length=1, max_length=20, examples=["Apto 104"])
    whatsapp: str = Field(..., min_length=10, max_length=20, examples=["5511999998888"])


# ALTERAÇÃO: resposta declarada por completo, com o id e o condominio_id.
class MoradorResponse(BaseModel):
    id: int
    condominio_id: int
    nome: str
    bloco: str
    apartamento: str
    whatsapp: str

    class Config:
        from_attributes = True


# SCHEMAS PARA AUDITORIA
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