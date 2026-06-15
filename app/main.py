
from fastapi import FastAPI
from app.database import engine
from app.models import tabelas
from app.routers import condominios, prestadores, chamados # Importa as rotas novas

# Cria as tabelas no PostgreSQL automaticamente
tabelas.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SaaS Condomínio Inovador - Backend",
    description="API de gerenciamento de condomínios integrada com n8n e IA",
    version="1.0.0"
)

# Inclui as rotas na API
app.include_router(condominios.router)
app.include_router(prestadores.router)
app.include_router(chamados.router)

@app.get("/")
def home():
    return {
        "status": "SaaS online",
        "mensagem": "Backend do condomínio operando com sucesso!"
    }