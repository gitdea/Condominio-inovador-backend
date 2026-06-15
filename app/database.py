
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env (que vamos criar em breve)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# O engine é o cara que gerencia a conexão física com o PostgreSQL
engine = create_engine(DATABASE_URL)

# O SessionLocal é o que usamos para abrir e fechar consultas/inserções no banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função injetável que abre a conexão quando uma rota é chamada e fecha assim que ela termina
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()