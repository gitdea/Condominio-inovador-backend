
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
if "condominio_id" not in st.session_state:
    st.session_state.condominio_id = None  # Guarda o ID do condomínio logado

# TELA DE AUTENTICAÇÃO (Login ou Cadastro)
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>🏢 Condomínio Inovador</h2>", unsafe_allow_html=True)
    
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
                                
                                # SALVA O ID DO CONDOMÍNO VEIO DA API
                                # Nota: Certifique-se de que sua rota /auth/login retorna o 'condominio_id'
                                st.session_state.condominio_id = dados_token.get("condominio_id", 1) 
                                
                                st.success("Login realizado com sucesso! Carregando painel...")
                                st.rerun()
                            elif response.status_code == 401:
                                st.error("E-mail ou senha incorretos.")
                            else:
                                st.error(f"Erro ao autenticar (Status {response.status_code})")
                        except requests.exceptions.ConnectionError:
                            st.error("Não foi possível conectar ao servidor backend.")
                    else:
                        st.error("Por favor, preencha o e-mail e a senha.")
                        
        # FLUXO DE CADASTRO INICIAL
        with aba_registrar:
            st.markdown("<h4 style='color: gray;'>Criar Conta do Síndico / Condomínio</h4>", unsafe_allow_html=True)
            with st.form("form_cadastro_inicial", clear_on_submit=True):
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
                                st.success("🎉 Conta criada com sucesso! Clique na aba '🔑 Fazer Login' para entrar.")
                            else:
                                st.error(f"Erro na API ao cadastrar (Status {response.status_code}).")
                        except requests.exceptions.ConnectionError:
                            st.error("Erro de conexão com o servidor FastAPI.")

# PAINEL ADMINISTRATIVO (Logado)
else:
    col_titulo, col_usuario = st.columns([4, 1])
    with col_titulo:
        st.title("🏢 Condomínio Inovador - Painel Administrativo")
    with col_usuario:
        st.write(f"👤 `{st.session_state.usuario_email}`")
        st.caption(f"🆔 Condomínio ID: **{st.session_state.condominio_id}**")
        if st.button("Sair / Logout", type="secondary"):
            st.session_state.logado = False
            st.session_state.token = None
            st.session_state.usuario_email = ""
            st.session_state.condominio_id = None
            st.rerun()

    aba_chamados, aba_moradores, aba_prestadores, aba_condominios = st.tabs([
        "📝 Chamados", 
        "👥 Moradores", 
        "🔧 Prestadores", 
        "🏢 Condomínios"
    ])

    # ABA 1: GERENCIAMENTO DE CHAMADOS
    with aba_chamados:
        st.header("Histórico e Evolução de Chamados")
        
        # Agora filtra automaticamente pelo condomínio logado
        if st.button("Carregar Chamados Deste Condomínio", type="primary"):
            try:
                response = requests.get(f"{API_URL}/chamados/")
                if response.status_code == 200:
                    chamados_reais = response.json()
                    if chamados_reais:
                        df_completo = pd.DataFrame(chamados_reais)
                        df_filtrado = df_completo[df_completo["condominio_id"] == st.session_state.condominio_id]
                        
                        if not df_filtrado.empty:
                            st.dataframe(df_filtrado, use_container_width=True)
                        else:
                            st.info("Nenhum chamado encontrado para o seu condomínio.")
                    else:
                        st.info("O banco de dados de chamados está vazio.")
            except requests.exceptions.ConnectionError:
                st.error("Não foi possível conectar à API.")

    # ABA 2: MORADORES
    with aba_moradores:
        st.header("👥 Gestão de Moradores")
        st.info(f"Cadastrando para o Condomínio ID: **{st.session_state.condominio_id}**")
        
        st.subheader("➕ Cadastrar Novo Morador")
        with st.form("form_cadastro_morador", clear_on_submit=True):
            # REMOVIDO o input manual de ID do Condomínio!
            nome_morador = st.text_input("Nome Completo do Morador:")
            bloco_morador = st.text_input("Bloco / Torre (ex: Bloco B):")
            ap_morador = st.text_input("Apartamento / Unidade (ex: Apto 104):")
            whatsapp_morador = st.text_input("WhatsApp do Morador (ex: 5511999998888):")
            
            enviar_morador = st.form_submit_button("Salvar Morador", type="primary")
            
            if enviar_morador:
                if nome_morador and bloco_morador and ap_morador and whatsapp_morador:
                    payload = {
                        "condominio_id": int(st.session_state.condominio_id), # 🟢 ID Automático!
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

    # ABA 3: PRESTADORES
    with aba_prestadores:
        st.header("🔧 Prestadores de Serviço")
        st.info(f"Cadastrando para o Condomínio ID: **{st.session_state.condominio_id}**")
        
        with st.form("form_prestador", clear_on_submit=True):
            # REMOVIDO o input manual de ID do Condomínio!
            nome_prestador = st.text_input("Nome do Prestador / Empresa:")
            categoria_prestador = st.text_input("Categoria / Especialidade:")
            telefone_prestador = st.text_input("Telefone de Contato:")
            
            enviar_prestador = st.form_submit_button("Salvar Prestador", type="primary")
            
            if enviar_prestador and nome_prestador and categoria_prestador and telefone_prestador:
                payload = {
                    "condominio_id": int(st.session_state.condominio_id), # 🟢 ID Automático!
                    "nome": nome_prestador, 
                    "categoria": categoria_prestador, 
                    "telefone": telefone_prestador
                }
                try:
                    response = requests.post(f"{API_URL}/prestadores/", json=payload)
                    if response.status_code in [200, 201]:
                        st.success(f"Prestador '{nome_prestador}' cadastrado com sucesso!")
                except requests.exceptions.ConnectionError:
                    st.error("Erro de conexão.")

    # ABA 4: CONDOMÍNIOS
    with aba_condominios:
        st.header("🏢 Cadastrar Outro Condomínio")
        with st.form("form_condominio", clear_on_submit=True):
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
                    except requests.exceptions.ConnectionError:
                        st.error("Erro de conexão.")