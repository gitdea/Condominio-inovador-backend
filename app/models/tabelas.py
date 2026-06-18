
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
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
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos (Para o SQLAlchemy saber quem está ligado a quem)
    prestadores = relationship("Prestador", back_populates="condominio", cascade="all, delete-orphan")
    solicitacoes = relationship("Solicitacao", back_populates="condominio", cascade="all, delete-orphan")
    # ADICIONADO: Relacionamento com moradores
    moradores = relationship("Morador", back_populates="condominio", cascade="all, delete-orphan")


# 1.5 NOVO - TABELA DE MORADORES
class Morador(Base):
    __tablename__ = "moradores"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    bloco = Column(String(20), nullable=False)
    apartamento = Column(String(20), nullable=False)
    whatsapp = Column(String(20), unique=True, nullable=False, index=True) # Campo que o n8n vai ler
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="moradores")
    solicitacoes = relationship("Solicitacao", back_populates="morador")


# 2. TABELA DE PRESTADORES DE SERVIÇO (Catálogo de Profissionais)
class Prestador(Base):
    __tablename__ = "prestadores"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)  # Ex: Encanador, Eletricista, Pintor
    telefone = Column(String(20), nullable=False)
    avaliacao_media = Column(Integer, default=5)     # Nota de 1 a 5 para a IA ler depois

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="prestadores")
    solicitacoes = relationship("Solicitacao", back_populates="prestador")


# 3. TABELA DE CHAMADOS / SOLICITAÇÕES (Onde o n8n vai atuar)
class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False)
    
    # AJUSTADO: Agora aponta corretamente para a chave estrangeira da tabela de moradores
    morador_id = Column(Integer, ForeignKey("moradores.id", ondelete="CASCADE"), nullable=False) 
    
    prestador_id = Column(Integer, ForeignKey("prestadores.id", ondelete="SET NULL"), nullable=True)
    
    descricao = Column(Text, nullable=False)
    status = Column(String(30), default="Iniciado") # Iniciado, Em andamento, Concluído com sucesso, Cancelado
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    condominio = relationship("Condominio", back_populates="solicitacoes")
    prestador = relationship("Prestador", back_populates="solicitacoes")
    # ADICIONADO: Relacionamento para conseguir buscar dados do morador a partir do chamado
    morador = relationship("Morador", back_populates="solicitacoes")