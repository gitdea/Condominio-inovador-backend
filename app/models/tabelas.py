
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# 1. TABELA DE CONDOMÍNIOS
class Condominio(Base):
    __tablename__ = "condominios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False, index=True)
    endereco = Column(String(255), nullable=False)
    
    # CAMPOS PARA LOGIN DO SÍNDICO
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha = Column(String(255), nullable=False)
    
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    prestadores = relationship("Prestador", back_populates="condominio", cascade="all, delete-orphan")
    solicitacoes = relationship("Solicitacao", back_populates="condominio", cascade="all, delete-orphan")
    moradores = relationship("Morador", back_populates="condominio", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="condominio", cascade="all, delete-orphan")


# 1.5 TABELA DE MORADORES
class Morador(Base):
    __tablename__ = "moradores"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    bloco = Column(String(20), nullable=False)
    apartamento = Column(String(20), nullable=False)
    whatsapp = Column(String(20), unique=True, nullable=False, index=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="moradores")
    solicitacoes = relationship("Solicitacao", back_populates="morador")


# 2. TABELA DE PRESTADORES DE SERVIÇO
class Prestador(Base):
    __tablename__ = "prestadores"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    telefone = Column(String(20), nullable=False)
    avaliacao_media = Column(Integer, default=5)

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="prestadores")
    solicitacoes = relationship("Solicitacao", back_populates="prestador")


# 3. TABELA DE CHAMADOS / SOLICITAÇÕES
class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    morador_id = Column(Integer, ForeignKey("moradores.id", ondelete="CASCADE"), nullable=False) 
    prestador_id = Column(Integer, ForeignKey("prestadores.id", ondelete="SET NULL"), nullable=True)
    
    descricao = Column(Text, nullable=False)
    status = Column(String(30), default="Iniciado")
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="solicitacoes")
    prestador = relationship("Prestador", back_populates="solicitacoes")
    morador = relationship("Morador", back_populates="solicitacoes")


# 4. TABELA DE AUDITORIA
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    
    usuario_responsavel = Column(String(150), nullable=False) 
    acao = Column(String(50), nullable=False)
    tabela_afetada = Column(String(50), nullable=False)
    registro_id = Column(Integer, nullable=True)
    detalhes = Column(JSON, nullable=True)
    data_hora = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="audit_logs")