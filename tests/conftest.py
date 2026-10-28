
import os
import sys
import tempfile
from pathlib import Path

# Coloca a raiz do projeto no caminho do Python, para o "import app" funcionar de dentro da pasta tests.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# IMPORTANTE (segurança dos dados): as variáveis abaixo são definidas ANTES de importar a aplicação.
# Assim, os testes usam um banco SQLite temporário e NUNCA tocam no banco de verdade (o do .env).
# O load_dotenv() do projeto não sobrescreve variáveis que já existem no ambiente.
_pasta_temporaria = tempfile.mkdtemp(prefix="condominio_teste_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_pasta_temporaria, 'teste.db').as_posix()}"
os.environ["SECRET_KEY"] = "chave-usada-apenas-nos-testes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import pytest
from fastapi.testclient import TestClient

from app.database import engine, Base
from app.main import app

# Trava de segurança: se por algum motivo o banco não for SQLite, os testes param antes de apagar qualquer dado.
assert engine.url.get_backend_name() == "sqlite", "Os testes só podem rodar com o banco SQLite de teste."


@pytest.fixture(autouse=True)
def banco_limpo():
    """Antes de CADA teste, apaga e recria as tabelas do banco de teste. Assim, um teste não interfere no outro."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


# CNPJs de teste com dígitos verificadores válidos
CNPJ_A = "11.222.333/0001-81"
CNPJ_B = "12.345.678/0001-95"
SENHA = "senha123"


def criar_condominio(client, nome, cnpj, email, senha=SENHA):
    resposta = client.post("/condominios/", json={
        "nome": nome,
        "cnpj": cnpj,
        "endereco": "Rua das Flores, 123 - Centro",
        "email": email,
        "senha": senha,
    })
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def entrar(client, email, senha=SENHA):
    """Faz login e devolve o cabeçalho com o token, pronto para usar nas chamadas protegidas."""
    resposta = client.post("/auth/login", data={"username": email, "password": senha})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def criar_morador(client, headers, whatsapp="5511999990001"):
    resposta = client.post("/moradores/", json={
        "nome": "Carlos Silva",
        "bloco": "Bloco B",
        "apartamento": "Apto 104",
        "whatsapp": whatsapp,
    }, headers=headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def abrir_chamado(client, headers, morador_id):
    resposta = client.post("/chamados/", json={
        "morador_id": morador_id,
        "descricao": "Vazamento no banheiro",
    }, headers=headers)
    return resposta


@pytest.fixture
def dois_condominios(client):
    """Cria os condomínios A e B e devolve os ids e os cabeçalhos de login de cada um."""
    a = criar_condominio(client, "Condominio A", CNPJ_A, "condominioa@gmail.com")
    b = criar_condominio(client, "Condominio B", CNPJ_B, "condominiob@gmail.com")
    return {
        "a": {"id": a["id"], "email": "condominioa@gmail.com", "headers": entrar(client, "condominioa@gmail.com")},
        "b": {"id": b["id"], "email": "condominiob@gmail.com", "headers": entrar(client, "condominiob@gmail.com")},
    }