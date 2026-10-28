
import os
import requests
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Condomínio Inovador - Painel", page_icon="🏢", layout="wide")

# ALTERAÇÃO: o endereço da API agora pode vir da variável BACKEND_URL (para publicar sem mudar o código).
# Sem a variável, usa a API local.
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
TIMEOUT = 30  # segundos de espera por resposta da API

# INICIALIZAÇÃO DO ESTADO DE LOGIN
for chave, padrao in {
    "logado": False,
    "token": None,
    "usuario_email": "",
    "condominio_id": None,
    "condominio_nome": "",
    "aviso": None,
}.items():
    if chave not in st.session_state:
        st.session_state[chave] = padrao


def sair(aviso=None):
    """Limpa a sessão. Usada no botão Sair e quando o token expira."""
    st.session_state.logado = False
    st.session_state.token = None
    st.session_state.usuario_email = ""
    st.session_state.condominio_id = None
    st.session_state.condominio_nome = ""
    st.session_state.aviso = aviso


# ALTERAÇÃO (autenticação): todas as chamadas ao painel passam por esta função, que envia o token no
# cabeçalho Authorization. A API agora exige o token para saber de qual condomínio são os dados.
def chamar_api(metodo, caminho, **kwargs):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        resposta = requests.request(metodo, f"{API_URL}{caminho}", headers=headers, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.RequestException:
        st.error("Não foi possível conectar à API. Tente novamente em instantes.")
        return None
    if resposta.status_code == 401:
        # Token inválido ou expirado: volta para a tela de login com um aviso.
        sair("Sua sessão expirou. Entre novamente.")
        st.rerun()
    return resposta


# ALTERAÇÃO (erros): mostra a mensagem que a API devolveu (por exemplo "CNPJ inválido.") em vez de só o
# número do status.
def mensagem_erro(resposta):
    try:
        detalhe = resposta.json().get("detail")
    except ValueError:
        detalhe = None
    if isinstance(detalhe, str):
        return detalhe
    if isinstance(detalhe, list) and detalhe:
        item = detalhe[0]
        campo = item.get("loc", [""])[-1]
        texto = str(item.get("msg", "Dados inválidos.")).replace("Value error, ", "")
        return f"{campo}: {texto}" if campo else texto
    return f"Erro (status {resposta.status_code})."


# TELA DE AUTENTICAÇÃO (Login ou Cadastro)
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>🏢 Condomínio Inovador</h2>", unsafe_allow_html=True)

    if st.session_state.aviso:
        st.warning(st.session_state.aviso)
        st.session_state.aviso = None

    col_esq, col_centro, col_dir = st.columns([1, 2, 1])

    with col_centro:
        aba_entrar, aba_registrar = st.tabs(["🔑 Fazer Login", "📝 Cadastrar-se (Nova Conta)"])

        # FLUXO DE LOGIN
        with aba_entrar:
            st.markdown("<h4 style='color: gray;'>Painel de Acesso do Síndico</h4>", unsafe_allow_html=True)
            with st.form("form_login"):
                email_input = st.text_input("E-mail:")
                senha_input = st.text_input("Senha:", type="password")
                botao_entrar = st.form_submit_button("Entrar no Painel", type="primary", use_container_width=True)

                if botao_entrar:
                    if email_input and senha_input:
                        try:
                            response = requests.post(
                                f"{API_URL}/auth/login",
                                data={"username": email_input, "password": senha_input},
                                timeout=TIMEOUT,
                            )
                            if response.status_code == 200:
                                dados_token = response.json()
                                st.session_state.logado = True
                                st.session_state.token = dados_token.get("access_token")
                                st.session_state.usuario_email = email_input
                                # ALTERAÇÃO: antes, se a API não devolvesse o id, o painel assumia o condomínio 1
                                # (dados_token.get("condominio_id", 1)). Isso podia mostrar o condomínio errado.
                                st.session_state.condominio_id = dados_token.get("condominio_id")

                                # Busca o nome do condomínio uma vez, para mostrar no topo do painel.
                                dados_condominio = chamar_api("GET", "/condominios/me")
                                if dados_condominio is not None and dados_condominio.status_code == 200:
                                    st.session_state.condominio_nome = dados_condominio.json().get("nome", "")

                                st.success("Login realizado com sucesso! Carregando painel...")
                                st.rerun()
                            elif response.status_code == 401:
                                st.error("E-mail ou senha incorretos.")
                            else:
                                st.error(f"Erro ao autenticar (Status {response.status_code})")
                        except requests.exceptions.RequestException:
                            st.error("Não foi possível conectar ao servidor backend.")
                    else:
                        st.error("Por favor, preencha o e-mail e a senha.")

        # FLUXO DE CADASTRO INICIAL (público: é assim que um condomínio novo entra no sistema)
        with aba_registrar:
            st.markdown("<h4 style='color: gray;'>Criar Conta do Síndico / Condomínio</h4>", unsafe_allow_html=True)
            with st.form("form_cadastro_inicial", clear_on_submit=True):
                nome_condominio = st.text_input("Nome do Condomínio:")
                # ALTERAÇÃO: o rótulo mudou, porque a API agora valida os dígitos do CNPJ e aceita com ou sem pontuação.
                cnpj_condominio = st.text_input("CNPJ:")
                endereco_condominio = st.text_input("Endereço Completo:")
                email_condominio = st.text_input("Seu E-mail (Será seu usuário de login):")
                senha_condominio = st.text_input("Crie uma Senha de Acesso:", type="password")

                botao_cadastrar = st.form_submit_button("Criar Conta e Cadastrar", type="primary", use_container_width=True)

                if botao_cadastrar:
                    if nome_condominio and cnpj_condominio and endereco_condominio and email_condominio and senha_condominio:
                        payload_cadastro = {
                            "nome": nome_condominio,
                            "cnpj": cnpj_condominio,
                            "endereco": endereco_condominio,
                            "email": email_condominio,
                            "senha": senha_condominio,
                        }
                        try:
                            response = requests.post(f"{API_URL}/condominios/", json=payload_cadastro, timeout=TIMEOUT)
                            if response.status_code in [200, 201]:
                                st.success("🎉 Conta criada com sucesso! Clique na aba '🔑 Fazer Login' para entrar.")
                            else:
                                st.error(mensagem_erro(response))
                        except requests.exceptions.RequestException:
                            st.error("Erro de conexão com o servidor FastAPI.")
                    else:
                        st.error("Preencha todos os campos.")

# PAINEL ADMINISTRATIVO (Logado)
else:
    col_titulo, col_usuario = st.columns([4, 1])
    with col_titulo:
        st.title("🏢 Condomínio Inovador - Painel Administrativo")
    with col_usuario:
        st.write(f"👤 `{st.session_state.usuario_email}`")
        if st.session_state.condominio_nome:
            st.caption(f"🏢 {st.session_state.condominio_nome}")
        if st.button("Sair / Logout", type="secondary"):
            sair()
            st.rerun()

    # ALTERAÇÃO: a aba "Condomínios" (que cadastrava outro condomínio) virou "Meu Condomínio", com os dados da
    # conta e o histórico de auditoria. Cadastrar um condomínio novo continua na tela de login.
    aba_chamados, aba_moradores, aba_prestadores, aba_condominio = st.tabs([
        "📝 Chamados",
        "👥 Moradores",
        "🔧 Prestadores",
        "🏢 Meu Condomínio",
    ])

    # ABA 1: CHAMADOS
    with aba_chamados:
        st.header("Histórico e Evolução de Chamados")
        if st.button("Carregar Chamados Deste Condomínio", type="primary"):
            # ALTERAÇÃO (isolamento): a API já devolve só os chamados do condomínio logado, então o filtro
            # que existia aqui com pandas (condominio_id == ...) deixou de ser necessário.
            response = chamar_api("GET", "/chamados/")
            if response is not None:
                if response.status_code == 200:
                    chamados = response.json()
                    if chamados:
                        st.dataframe(pd.DataFrame(chamados), use_container_width=True)
                    else:
                        st.info("Nenhum chamado encontrado para o seu condomínio.")
                else:
                    st.error(mensagem_erro(response))

    # ABA 2: MORADORES
    with aba_moradores:
        st.header("👥 Gestão de Moradores")

        st.subheader("➕ Cadastrar Novo Morador")
        with st.form("form_cadastro_morador", clear_on_submit=True):
            nome_morador = st.text_input("Nome Completo do Morador:")
            bloco_morador = st.text_input("Bloco / Torre (ex: Bloco B):")
            ap_morador = st.text_input("Apartamento / Unidade (ex: Apto 104):")
            whatsapp_morador = st.text_input("WhatsApp do Morador (ex: 5511999998888):")

            enviar_morador = st.form_submit_button("Salvar Morador", type="primary")

            if enviar_morador:
                if nome_morador and bloco_morador and ap_morador and whatsapp_morador:
                    # ALTERAÇÃO (isolamento): o condominio_id saiu do payload. A API pega do token.
                    payload = {
                        "nome": nome_morador,
                        "bloco": bloco_morador,
                        "apartamento": ap_morador,
                        "whatsapp": whatsapp_morador,
                    }
                    response = chamar_api("POST", "/moradores/", json=payload)
                    if response is not None:
                        if response.status_code in [200, 201]:
                            st.success(f"Morador '{nome_morador}' cadastrado com sucesso!")
                        else:
                            st.error(mensagem_erro(response))
                else:
                    st.error("Preencha todos os campos.")

        st.subheader("📋 Moradores cadastrados")
        if st.button("Ver moradores"):
            response = chamar_api("GET", "/moradores/")
            if response is not None:
                if response.status_code == 200:
                    moradores = response.json()
                    if moradores:
                        st.dataframe(pd.DataFrame(moradores), use_container_width=True)
                    else:
                        st.info("Nenhum morador cadastrado ainda.")
                else:
                    st.error(mensagem_erro(response))

    # ABA 3: PRESTADORES
    with aba_prestadores:
        st.header("🔧 Prestadores de Serviço")

        with st.form("form_prestador", clear_on_submit=True):
            nome_prestador = st.text_input("Nome do Prestador / Empresa:")
            categoria_prestador = st.text_input("Categoria / Especialidade:")
            telefone_prestador = st.text_input("Telefone de Contato:")

            enviar_prestador = st.form_submit_button("Salvar Prestador", type="primary")

            if enviar_prestador:
                if nome_prestador and categoria_prestador and telefone_prestador:
                    # ALTERAÇÃO (isolamento): sem condominio_id no payload.
                    payload = {
                        "nome": nome_prestador,
                        "categoria": categoria_prestador,
                        "telefone": telefone_prestador,
                    }
                    response = chamar_api("POST", "/prestadores/", json=payload)
                    if response is not None:
                        if response.status_code in [200, 201]:
                            st.success(f"Prestador '{nome_prestador}' cadastrado com sucesso!")
                        else:
                            # ALTERAÇÃO: antes, se a API recusasse, o painel não mostrava nenhum aviso.
                            st.error(mensagem_erro(response))
                else:
                    st.error("Preencha todos os campos.")

        st.subheader("📋 Prestadores cadastrados")
        if st.button("Ver prestadores"):
            response = chamar_api("GET", "/prestadores/")
            if response is not None:
                if response.status_code == 200:
                    prestadores = response.json()
                    if prestadores:
                        st.dataframe(pd.DataFrame(prestadores), use_container_width=True)
                    else:
                        st.info("Nenhum prestador cadastrado ainda.")
                else:
                    st.error(mensagem_erro(response))

    # ABA 4: MEU CONDOMÍNIO E AUDITORIA
    with aba_condominio:
        st.header("🏢 Meu Condomínio")
        response = chamar_api("GET", "/condominios/me")
        if response is not None and response.status_code == 200:
            dados = response.json()
            st.write(f"**Nome:** {dados.get('nome')}")
            st.write(f"**CNPJ:** {dados.get('cnpj')}")
            st.write(f"**Endereço:** {dados.get('endereco')}")
            st.write(f"**E-mail do síndico:** {dados.get('email')}")

        st.subheader("🕵️ Histórico de auditoria")
        st.caption("Registro de quem fez o quê neste condomínio, do mais recente para o mais antigo.")
        if st.button("Carregar auditoria"):
            response = chamar_api("GET", "/condominios/me/auditoria", params={"limite": 50})
            if response is not None:
                if response.status_code == 200:
                    logs = response.json()
                    if logs:
                        st.dataframe(pd.DataFrame(logs), use_container_width=True)
                    else:
                        st.info("Ainda não há registros de auditoria.")
                else:
                    st.error(mensagem_erro(response))