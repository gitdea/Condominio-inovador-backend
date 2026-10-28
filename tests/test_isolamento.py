
from conftest import (
    CNPJ_A, criar_condominio, entrar, criar_morador, abrir_chamado,
)


# ---------- AUTENTICAÇÃO ----------

def test_rotas_protegidas_exigem_login(client):
    """Sem token, as rotas protegidas devem responder 401."""
    for caminho in ["/chamados/", "/moradores/", "/prestadores/", "/condominios/me", "/condominios/me/auditoria"]:
        assert client.get(caminho).status_code == 401, caminho
    assert client.post("/chamados/", json={"morador_id": 1, "descricao": "Sem login aqui"}).status_code == 401


def test_login_com_senha_errada_retorna_401(client, dois_condominios):
    resposta = client.post("/auth/login", data={"username": "condominioa@gmail.com", "password": "senha-errada"})
    assert resposta.status_code == 401


def test_falha_de_login_fica_na_auditoria(client, dois_condominios):
    client.post("/auth/login", data={"username": "condominioa@gmail.com", "password": "senha-errada"})
    logs = client.get("/condominios/me/auditoria", headers=dois_condominios["a"]["headers"]).json()
    assert "LOGIN_FALHOU" in [log["acao"] for log in logs]


def test_resposta_nunca_devolve_a_senha(client, dois_condominios):
    dados = client.get("/condominios/me", headers=dois_condominios["a"]["headers"]).json()
    assert "senha" not in dados


# ---------- CNPJ ----------

def test_cnpj_invalido_e_recusado(client):
    resposta = client.post("/condominios/", json={
        "nome": "Condominio Teste", "cnpj": "12.345.678/0001-99",
        "endereco": "Rua das Flores, 123 - Centro",
        "email": "teste@gmail.com", "senha": "senha123",
    })
    assert resposta.status_code == 422


def test_cnpj_valido_e_salvo_formatado(client):
    resposta = client.post("/condominios/", json={
        "nome": "Condominio Teste", "cnpj": "11222333000181",  # digitado sem pontuação
        "endereco": "Rua das Flores, 123 - Centro",
        "email": "teste@gmail.com", "senha": "senha123",
    })
    assert resposta.status_code == 201
    assert resposta.json()["cnpj"] == CNPJ_A


def test_cnpj_repetido_e_recusado_mesmo_com_outra_pontuacao(client):
    criar_condominio(client, "Condominio A", CNPJ_A, "a@gmail.com")
    resposta = client.post("/condominios/", json={
        "nome": "Outro Condominio", "cnpj": "11222333000181",
        "endereco": "Rua das Flores, 123 - Centro",
        "email": "outro@gmail.com", "senha": "senha123",
    })
    assert resposta.status_code == 400


# ---------- ISOLAMENTO ENTRE CONDOMÍNIOS ----------

def test_b_nao_ve_os_chamados_do_a(client, dois_condominios):
    a, b = dois_condominios["a"], dois_condominios["b"]
    morador = criar_morador(client, a["headers"])
    assert abrir_chamado(client, a["headers"], morador["id"]).status_code == 201

    assert len(client.get("/chamados/", headers=a["headers"]).json()) == 1
    assert client.get("/chamados/", headers=b["headers"]).json() == []


def test_b_nao_consegue_alterar_o_chamado_do_a(client, dois_condominios):
    a, b = dois_condominios["a"], dois_condominios["b"]
    morador = criar_morador(client, a["headers"])
    chamado = abrir_chamado(client, a["headers"], morador["id"]).json()

    resposta = client.patch(f"/chamados/{chamado['id']}/status", json={"status": "Em andamento"}, headers=b["headers"])
    assert resposta.status_code == 404

    # E o chamado do A continua como estava.
    chamados_a = client.get("/chamados/", headers=a["headers"]).json()
    assert chamados_a[0]["status"] == "Iniciado"


def test_b_nao_abre_chamado_com_morador_do_a(client, dois_condominios):
    a, b = dois_condominios["a"], dois_condominios["b"]
    morador = criar_morador(client, a["headers"])
    assert abrir_chamado(client, b["headers"], morador["id"]).status_code == 404


def test_b_nao_ve_moradores_nem_prestadores_do_a(client, dois_condominios):
    a, b = dois_condominios["a"], dois_condominios["b"]
    criar_morador(client, a["headers"], whatsapp="5511999990001")
    resposta = client.post("/prestadores/", json={
        "nome": "Joao Encanador", "categoria": "Encanador", "telefone": "11999998888",
    }, headers=a["headers"])
    assert resposta.status_code == 201

    assert len(client.get("/moradores/", headers=a["headers"]).json()) == 1
    assert len(client.get("/prestadores/", headers=a["headers"]).json()) == 1
    assert client.get("/moradores/", headers=b["headers"]).json() == []
    assert client.get("/prestadores/", headers=b["headers"]).json() == []


def test_b_nao_encontra_morador_do_a_pelo_whatsapp(client, dois_condominios):
    a, b = dois_condominios["a"], dois_condominios["b"]
    criar_morador(client, a["headers"], whatsapp="5511999990001")

    assert client.get("/moradores/buscar", params={"whatsapp": "5511999990001"}, headers=a["headers"]).status_code == 200
    assert client.get("/moradores/buscar", params={"whatsapp": "5511999990001"}, headers=b["headers"]).status_code == 404


def test_morador_e_criado_no_condominio_do_token(client, dois_condominios):
    """O cliente não escolhe o condomínio: ele vem do token."""
    a = dois_condominios["a"]
    morador = criar_morador(client, a["headers"])
    assert morador["condominio_id"] == a["id"]


def test_whatsapp_repetido_retorna_409(client, dois_condominios):
    a = dois_condominios["a"]
    criar_morador(client, a["headers"], whatsapp="5511999990001")
    resposta = client.post("/moradores/", json={
        "nome": "Outra Pessoa", "bloco": "Bloco A", "apartamento": "Apto 1", "whatsapp": "5511999990001",
    }, headers=a["headers"])
    assert resposta.status_code == 409


# ---------- AUDITORIA ----------

def test_auditoria_mostra_so_os_registros_do_proprio_condominio(client, dois_condominios):
    a, b = dois_condominios["a"], dois_condominios["b"]
    morador = criar_morador(client, a["headers"])
    abrir_chamado(client, a["headers"], morador["id"])

    logs_a = client.get("/condominios/me/auditoria", headers=a["headers"]).json()
    logs_b = client.get("/condominios/me/auditoria", headers=b["headers"]).json()

    assert all(log["condominio_id"] == a["id"] for log in logs_a)
    assert all(log["condominio_id"] == b["id"] for log in logs_b)
    assert "CRIAR_CHAMADO" in [log["acao"] for log in logs_a]
    assert "CRIAR_CHAMADO" not in [log["acao"] for log in logs_b]


def test_auditoria_registra_o_email_de_quem_agiu(client, dois_condominios):
    a = dois_condominios["a"]
    criar_morador(client, a["headers"])
    logs = client.get("/condominios/me/auditoria", headers=a["headers"]).json()
    log_morador = next(log for log in logs if log["acao"] == "CRIAR_MORADOR")
    assert log_morador["usuario_responsavel"] == a["email"]


def test_mudanca_de_status_guarda_antes_e_depois(client, dois_condominios):
    a = dois_condominios["a"]
    morador = criar_morador(client, a["headers"])
    chamado = abrir_chamado(client, a["headers"], morador["id"]).json()

    resposta = client.patch(f"/chamados/{chamado['id']}/status", json={"status": "Em andamento"}, headers=a["headers"])
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "Em andamento"

    logs = client.get("/condominios/me/auditoria", headers=a["headers"]).json()
    log_status = next(log for log in logs if log["acao"] == "ATUALIZAR_STATUS_CHAMADO")
    assert log_status["detalhes"] == {"status_anterior": "Iniciado", "status_novo": "Em andamento"}