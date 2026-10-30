

# Condomínio Inovador

API de gestão de condomínios com painel para o síndico. Cada condomínio entra com o próprio login e enxerga apenas os seus dados: moradores, prestadores de serviço e chamados (ordens de serviço), com um histórico de auditoria de tudo o que acontece na conta.

🔗 **Teste online:** [painel do síndico](https://condominio-inovador-backend-h2ll93zfhvph8itg27exwp.streamlit.app/)

## O que o projeto faz?
* **Login com JWT:** as senhas são guardadas com `bcrypt`, e o login devolve um token com tempo de expiração (30 minutos por padrão).
* **Isolamento entre condomínios (multitenant):** todas as rotas, exceto o login e o cadastro de condomínio, exigem o token. O condomínio é descoberto pelo token, e nunca por um número enviado na requisição. Quem tenta ler ou alterar dados de outro condomínio recebe "não encontrado" (404).
* **CNPJ validado:** o cadastro confere os dois dígitos verificadores, guarda o CNPJ sempre no formato `00.000.000/0000-00` e recusa CNPJs repetidos, mesmo digitados com outra pontuação.
* **Chamados (ordens de serviço):** a API abre chamados e atualiza o status (Iniciado, Em andamento, Cancelado e Concluído com sucesso). O morador do chamado precisa pertencer ao condomínio logado.
* **Moradores e prestadores de serviço:** cadastro e listagem por condomínio.
* **Auditoria:** registra os logins (com sucesso e com falha), as criações e as mudanças de status, com o e-mail de quem fez a ação. Na mudança de status, o log guarda o valor antes e depois. Cada condomínio consulta só o próprio histórico, com paginação.
* **Painel do síndico (Streamlit):** login, cadastro de moradores e prestadores, lista de chamados e consulta da auditoria.
* **Documentação automática:** o Swagger fica em `/docs`, e dá para testar todas as rotas por ele.
* **Testes automatizados:** 17 testes com `pytest` provam o isolamento entre condomínios, o login, a validação do CNPJ e a auditoria.

## Demonstração online

O painel está publicado e pode ser testado sem instalar nada. Ele roda no Streamlit, a API no Render e o banco é um PostgreSQL na nuvem.

1. Abra o [painel online](https://condominio-inovador-backend-h2ll93zfhvph8itg27exwp.streamlit.app/). Os servidores gratuitos "dormem" quando ficam sem uso, então o primeiro acesso pode levar cerca de um minuto.
2. Na aba **Cadastrar-se**, crie um condomínio de teste com **dados fictícios**. Para o CNPJ, use um de teste com dígitos válidos, como `11.222.333/0001-81`. Cada CNPJ só pode ser usado uma vez, então, se ele já estiver em uso, tente `12.345.678/0001-95` ou `10.000.000/0001-45`.
3. Entre com o e-mail e a senha que você criou. Cadastre moradores e prestadores, veja a lista de chamados e o histórico de auditoria.

> **Demonstração pública:** use apenas dados fictícios. Não informe e-mails, telefones nem senhas reais. Cada condomínio vê só os próprios dados, mas tudo fica registrado no servidor e pode ser apagado a qualquer momento.

## Quais tecnologias foram usadas?
* **Python 3.13 e FastAPI:** a API.
* **PostgreSQL e SQLAlchemy:** o banco de dados e o acesso a ele.
* **PyJWT e Passlib (bcrypt):** o login e a criptografia das senhas.
* **Pydantic:** a validação dos dados, incluindo o CNPJ.
* **Streamlit, Pandas e Requests:** o painel do síndico.
* **Pytest e HTTPX:** os testes automatizados.
* **python-dotenv:** as variáveis de ambiente, fora do código.

## Como o isolamento funciona
1. O síndico faz login em `POST /auth/login` e recebe um token.
2. Nas outras rotas, a função `obter_condominio_atual` lê o token e carrega o condomínio logado.
3. Toda consulta filtra por esse condomínio. Exemplo: para alterar um chamado, a busca é por `id` **e** `condominio_id`. Se o chamado é de outro condomínio, ele não é encontrado.

## Principais rotas

| Rota | O que faz | Exige login |
|---|---|---|
| `POST /auth/login` | Entra e recebe o token | Não |
| `POST /condominios/` | Cadastra um condomínio novo | Não |
| `GET /condominios/me` | Dados do condomínio logado | Sim |
| `GET /condominios/me/auditoria` | Histórico de auditoria | Sim |
| `POST /moradores/` e `GET /moradores/` | Cadastra e lista moradores | Sim |
| `GET /moradores/buscar?whatsapp=` | Busca um morador pelo WhatsApp | Sim |
| `POST /prestadores/` e `GET /prestadores/` | Cadastra e lista prestadores | Sim |
| `POST /chamados/` e `GET /chamados/` | Abre e lista chamados | Sim |
| `PATCH /chamados/{id}/status` | Atualiza o status de um chamado | Sim |

## Como rodar no seu computador?

Você precisa de Python 3.13 e de um PostgreSQL funcionando.

**1. Clone e instale as dependências**

```bash
git clone https://github.com/gitdea/Condominio-inovador-backend.git
cd Condominio-inovador-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Crie o arquivo `.env` na raiz**

```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
SECRET_KEY=cole_aqui_uma_chave_gerada
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

A `SECRET_KEY` é obrigatória: a API não sobe sem ela. Para gerar uma chave segura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**3. Suba a API**

```bash
uvicorn app.main:app --reload
```

O Swagger fica em `http://127.0.0.1:8000/docs`. As tabelas são criadas automaticamente na primeira execução.

**4. Suba o painel** (em outro terminal, na mesma pasta)

```bash
pip install -r requirements-painel.txt
streamlit run dashboard.py
```

Por padrão, o painel fala com `http://127.0.0.1:8000`. Para usar outro endereço, defina a variável `BACKEND_URL`.

## Como rodar os testes?

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes usam um banco SQLite temporário, criado do zero a cada teste, e não tocam no banco do seu `.env`.

## Autora
**Andrea Cruz Leonardo**: Desenvolvedora Back-End Python
[LinkedIn](https://www.linkedin.com/in/andrea-cruz-leonardo/) · [GitHub](https://github.com/gitdea) · [Portfólio](https://gitdea.github.io/portfolio/)