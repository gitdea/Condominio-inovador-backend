
import streamlit as st
import requests
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Condomínio Inovador - Painel", page_icon="🏢", layout="wide")

# URL base da sua API
API_URL = "http://127.0.0.1:8000"

# INICIALIZAÇÃO DO ESTADO DE LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False
if "token" not in st.session_state:
    st.session_state.token = None
if "usuario_email" not in st.session_state:
    st.session_state.usuario_email = ""

# TELA DE AUTENTICAÇÃO (Login ou Cadastro)
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>🏢 Condomínio Inovador</h2>", unsafe_allow_html=True)
    
    # Centralizando o formulário na tela
    col_esq, col_centro, col_dir = st.columns([1, 2, 1])
    
    with col_centro:
        # Abas para o Síndico escolher o que quer fazer
        aba_entrar, aba_registrar = st.tabs(["🔑 Fazer Login", "📝 Cadastrar-se (Nova Conta)"])
        
        # FLUXO DE LOGIN 
        with aba_entrar:
            st.markdown("<h4 style='color: gray;'>Painel de Acesso do Síndico</h4>", unsafe_allow_html=True)
            with st.form("form_login"):
                email_input = st.text_input("E-mail:")
                senha_input = st.text_input("Senha:", type="password")
                botao_entrar = st.form_submit_button("Entrar no Panel", type="primary", use_container_width=True)
                
                if botao_entrar:
                    if email_input and senha_input:
                        try:
                            payload_login = {
                                "username": email_input,
                                "password": senha_input
                            }
                            response = requests.post(f"{API_URL}/auth/login", data=payload_login)
                            
                            if response.status_code == 200:
                                dados_token = response.json()
                                st.session_state.logado = True
                                st.session_state.token = dados_token.get("access_token")
                                st.session_state.usuario_email = email_input
                                st.success("Login realizado com sucesso! Carregando painel...")
                                st.rerun()
                            elif response.status_code == 401:
                                st.error("E-mail ou senha incorretos.")
                            elif response.status_code == 404:
                                st.error("Erro 404: Rota de login não encontrada no servidor. Verifique o prefixo da API.")
                            else:
                                st.error(f"Erro ao autenticar (Status {response.status_code})")
                        except requests.exceptions.ConnectionError:
                            st.error("Não foi possível conectar ao servidor backend. O FastAPI está rodando?")
                    else:
                        st.error("Por favor, preencha o e-mail e a senha.")
                        
        # FLUXO DE CADASTRO
        with aba_registrar:
            st.markdown("<h4 style='color: gray;'>Criar Conta do Síndico / Condomínio</h4>", unsafe_allow_html=True)
            with st.form("form_cadastro_inicial"):
                nome_condominio = st.text_input("Nome do Condomínio:")
                cnpj_condominio = st.text_input("CNPJ (Apenas números):")
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
                            "senha": senha_condominio
                        }
                        try:
                            response = requests.post(f"{API_URL}/condominios/", json=payload_cadastro)
                            if response.status_code in [200, 201]:
                                st.success("🎉 Conta criada com sucesso! Agora clique na aba '🔑 Fazer Login' acima para entrar.")
                            elif response.status_code == 422:
                                st.error("Validação falhou. Verifique o tamanho do CNPJ (min 14) e Endereço (min 10).")
                            else:
                                st.error(f"Erro na API ao cadastrar (Status {response.status_code}).")
                        except requests.exceptions.ConnectionError:
                            st.error("Erro de conexão com o servidor FastAPI.")
                    else:
                        st.error("Por favor, preencha todos os campos do cadastro.")

# PAINEL ADMINISTRATIVO (Só aparece se logado)
else:
    # Barra superior com informações do usuário logado e botão de Sair
    col_titulo, col_usuario = st.columns([4, 1])
    with col_titulo:
        st.title("🏢 Condomínio Inovador - Painel Administrativo")
    with col_usuario:
        st.write(f"👤 `{st.session_state.usuario_email}`")
        if st.button("Sair / Logout", type="secondary"):
            st.session_state.logado = False
            st.session_state.token = None
            st.session_state.usuario_email = ""
            st.rerun()

    st.markdown("Gerenciamento de condomínios, moradores, prestadores e chamados operacionais em tempo real.")

    # Criando as abas de gerenciamento interno do painel
    aba_chamados, aba_moradores, aba_prestadores, aba_condominios = st.tabs([
        "📝 Chamados", 
        "👥 Moradores", 
        "🔧 Prestadores", 
        "🏢 Condomínios"
    ])

    # ABA 1: GERENCIAMENTO DE CHAMADOS
    with aba_chamados:
        st.header("Histórico e Evolução de Chamados")
        
        with st.form("form_filtrar_chamados"):
            id_condominio_busca = st.number_input("Digite o ID do Condomínio para filtrar:", min_value=1, step=1, value=2)
            botao_listar = st.form_submit_button("Buscar Chamados Reais", type="primary")
        
        if botao_listar:
            try:
                response = requests.get(f"{API_URL}/chamados/")
                if response.status_code == 200:
                    chamados_reais = response.json()
                    if chamados_reais:
                        df_completo = pd.DataFrame(chamados_reais)
                        df_filtrado = df_completo[df_completo["condominio_id"] == int(id_condominio_busca)]
                        
                        if not df_filtrado.empty:
                            st.dataframe(df_filtrado, use_container_width=True)
                        else:
                            st.info(f"Nenhum chamado encontrado no banco para o Condomínio ID {id_condominio_busca}.")
                    else:
                        st.info("O banco de dados de chamados está vazio.")
                else:
                    st.error(f"Erro na API (Status {response.status_code}).")
            except requests.exceptions.ConnectionError:
                st.error("Não foi possível conectar à API.")
                
        st.divider()
        st.subheader("🎛️ Atualizar Status do Chamado")
        
        with st.form("form_status"):
            col1, col2 = st.columns(2)
            with col1:
                chamado_id = st.number_input("ID do Chamado que deseja alterar:", min_value=1, step=1)
            with col2:
                novo_status = st.selectbox("Novo Status", ["Iniciado", "Em andamento", "Cancelado", "Concluído com sucesso"])
            
            botao_atualizar = st.form_submit_button("Atualizar Status no Banco", type="primary")
            
            if botao_atualizar:
                try:
                    payload = {"status": novo_status}
                    patch_response = requests.patch(f"{API_URL}/chamados/{chamado_id}/status", json=payload)
                    if patch_response.status_code == 200:
                        st.toast(f"✅ Status do chamado #{chamado_id} atualizado!", icon="📝")
                        st.success(f"Chamado #{chamado_id} atualizado para '{novo_status}' com sucesso!")
                    else:
                        st.error(f"Erro ao atualizar status. (Status {patch_response.status_code})")
                except requests.exceptions.ConnectionError:
                    st.error("Erro de conexão com o servidor FastAPI.")

    # ABA 2: CONSULTA E CADASTRO DE MORADORES
    with aba_moradores:
        st.header("👥 Gestão de Moradores (n8n Ready)")
        
        st.subheader("🔍 Buscar Morador por WhatsApp")
        with st.form("form_busca_morador"):
            whatsapp_busca = st.text_input("Digite o número de WhatsApp do morador (ex: 5511999998888):")
            botao_buscar = st.form_submit_button("Buscar Morador")
            
            if botao_buscar and whatsapp_busca:
                try:
                    response = requests.get(f"{API_URL}/moradores/buscar", params={"whatsapp": whatsapp_busca})
                    if response.status_code == 200:
                        morador = response.json()
                        st.success("Morador localizado com sucesso!")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Nome", morador.get("nome", "Não informado"))
                        col2.metric("Bloco / Ap", f"{morador.get('bloco', '-')} - {morador.get('apartamento', '-')}")
                        col3.metric("ID Condomínio", morador.get("condominio_id", "-"))
                    elif response.status_code == 404:
                        st.warning("Nenhum morador cadastrado com esse número de WhatsApp.")
                except requests.exceptions.ConnectionError:
                    st.error("Erro de conexão com o servidor FastAPI.")

        st.divider()
        st.subheader("➕ Cadastrar Novo Morador")
        with st.form("form_cadastro_morador", clear_on_submit=True):
            id_condominio_morador = st.number_input("ID do Condomínio Vinculado:", min_value=1, step=1)
            nome_morador = st.text_input("Nome Completo do Morador:")
            bloco_morador = st.text_input("Bloco / Torre (ex: Bloco B):")
            ap_morador = st.text_input("Apartamento / Unidade (ex: Apto 104):")
            whatsapp_morador = st.text_input("WhatsApp do Morador (ex: 5511999998888):")
            
            enviar_morador = st.form_submit_button("Salvar Morador", type="primary")
            
            if enviar_morador:
                if nome_morador and bloco_morador and ap_morador and whatsapp_morador:
                    payload = {
                        "condominio_id": int(id_condominio_morador),
                        "nome": nome_morador,
                        "bloco": bloco_morador,
                        "apartamento": ap_morador,
                        "whatsapp": whatsapp_morador
                    }
                    try:
                        response = requests.post(f"{API_URL}/moradores/", json=payload)
                        if response.status_code in [200, 201]:
                            st.success(f"Morador '{nome_morador}' cadastrado com sucesso!")
                        else:
                            st.error(f"Erro ao salvar morador (Status {response.status_code}).")
                    except requests.exceptions.ConnectionError:
                        st.error("Erro de conexão.")

    # ABA 3: GESTÃO DE PRESTADORES
    with aba_prestadores:
        st.header("Prestadores de Serviço Cadastrados")
        try:
            response = requests.get(f"{API_URL}/prestadores/")
            if response.status_code == 200:
                prestadores = response.json()
                if prestadores:
                    st.dataframe(pd.DataFrame(prestadores), use_container_width=True)
                else:
                    st.info("Nenhum prestador cadastrado ainda.")
        except requests.exceptions.ConnectionError:
            st.error("Erro de conexão.")
            
        st.divider()
        st.subheader("➕ Cadastrar Novo Prestador de Serviço")
        with st.form("form_prestador", clear_on_submit=True):
            id_condominio_prestador = st.number_input("ID do Condomínio Vinculado:", min_value=1, step=1)
            nome_prestador = st.text_input("Nome do Prestador / Empresa:")
            categoria_prestador = st.text_input("Categoria / Especialidade:")
            telefone_prestador = st.text_input("Telefone de Contato:")
            
            enviar_prestador = st.form_submit_button("Salvar Prestador", type="primary")
            
            if enviar_prestador and nome_prestador and categoria_prestador and telefone_prestador:
                payload = {
                    "condominio_id": int(id_condominio_prestador),
                    "nome": nome_prestador, 
                    "categoria": categoria_prestador, 
                    "telefone": telefone_prestador
                }
                try:
                    response = requests.post(f"{API_URL}/prestadores/", json=payload)
                    if response.status_code in [200, 201]:
                        st.success(f"Prestador '{nome_prestador}' cadastrado com sucesso!")
                        st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("Erro de conexão.")

    # ABA 4: CADASTRO DE CONDOMÍNIOS
    with aba_condominios:
        st.header("Cadastrar Novo Condomínio")
        with st.form("form_condominio"):
            nome_condominio = st.text_input("Nome do Condomínio:")
            cnpj_condominio = st.text_input("CNPJ (Apenas números):")
            endereco_condominio = st.text_input("Endereço Completo:")
            email_condominio = st.text_input("E-mail do Administrador:")
            senha_condominio = st.text_input("Senha de Acesso:", type="password")
            
            enviar_condominio = st.form_submit_button("Salvar Condomínio", type="primary")
            
            if enviar_condominio:
                if nome_condominio and cnpj_condominio and endereco_condominio and email_condominio and senha_condominio:
                    payload = {
                        "nome": nome_condominio, 
                        "cnpj": cnpj_condominio,
                        "endereco": endereco_condominio,
                        "email": email_condominio,
                        "senha": senha_condominio
                    }
                    try:
                        response = requests.post(f"{API_URL}/condominios/", json=payload)
                        if response.status_code in [200, 201]:
                            st.success(f"Condomínio '{nome_condominio}' cadastrado com sucesso!")
                        elif response.status_code == 422:
                            st.error("Validação falhou. Verifique o tamanho do CNPJ (min 14) e Endereço (min 10).")
                        else:
                            st.error(f"Erro na API (Status {response.status_code}).")
                    except requests.exceptions.ConnectionError:
                        st.error("Erro de conexão.")