
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env. Se a variável já existir no ambiente (como nos testes,
# que definem a DATABASE_URL antes de importar a aplicação), o valor do ambiente é mantido.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ALTERAÇÃO: antes, sem a DATABASE_URL, o erro aparecia só dentro do SQLAlchemy e era difícil de entender.
if not DATABASE_URL:
    raise RuntimeError("Defina a variável DATABASE_URL no arquivo .env")

# ALTERAÇÃO: o SQLite (usado só nos testes automatizados) precisa desta opção para funcionar com as
# threads do FastAPI. Para o PostgreSQL ela não é usada.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# ALTERAÇÃO: o pool_pre_ping testa a conexão antes de usá-la. Se o PostgreSQL for reiniciado, ou se um
# banco hospedado fechar uma conexão parada, a próxima chamada abre uma nova em vez de dar erro.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

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