
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import tabelas
from app.routers import condominios, prestadores, chamados, moradores, auth  # ADICIONADO: auth

# Cria as tabelas no PostgreSQL automaticamente
tabelas.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SaaS Condomínio Inovador - Backend",
    description="API de gerenciamento de condomínios integrada com n8n e IA",
    version="1.0.0"
)

# CONFIGURAÇÃO DO CORS (Obrigatório para o seu painel conseguir logar!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua pelo link do seu painel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas na API
app.include_router(auth.router)          # ADICIONADO: Rota de login (/auth/login)
app.include_router(condominios.router)
app.include_router(prestadores.router)
app.include_router(chamados.router)
app.include_router(moradores.router) 

@app.get("/")
def home():
    return {
        "status": "SaaS online",
        "mensagem": "Backend do condomínio operando com sucesso!"
    }