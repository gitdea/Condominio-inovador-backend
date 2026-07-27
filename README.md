

# 🏢 Condomínio Inovador 

O **Condomínio Inovador** é um ecossistema completo voltado para a gestão operacional, segurança e automação de condomínios inteligentes. O sistema é composto por uma API robusta de alta performance (Back-end) integrada a um banco de dados relacional e protegida por autenticação moderna, além de um painel administrativo intuitivo (Front-end/Dashboard) projetado para o dia a dia do síndico.

---

## 🚀 Funcionalidades Chave

* **Autenticação Segura (JWT):** Sistema de login profissional utilizando criptografia de senhas (`bcrypt`) e emissão de Tokens JWT (JSON Web Tokens) com tempo de expiração dinâmico.
* **Sistema de Auditoria Interna (Audit Logs):** Registra e rastreia em banco de dados eventos críticos de segurança e operações (como tentativas de login com sucesso ou falha, com detalhes de quem executou, ação realizada, tabela afetada e horário).
* **Gestão Multitenant:** Cadastro e controle isolado de múltiplos condomínios com validações rigorosas de CNPJ.
* **Controle de Chamados em Tempo Real:** Abertura, monitoramento e atualização cirúrgica do ciclo de vida de ordens de serviço (Iniciado, Em andamento, Concluído) refletidas instantaneamente no banco.
* **Preparado para Integração com n8n:** O sistema foi desenvolvido com endpoints padronizados e organizados estrategicamente para facilitar o acoplamento futuro em fluxos de automação do n8n e agentes de IA.
* **Catálogo de Prestadores:** Registro organizado de profissionais parceiros vinculados aos condomínios por categoria de especialidade.
* **Interface do Síndico (Dashboard):** Painel interativo com navegação por abas para busca, gerenciamento e visualização de dados via tabelas integradas.
* **Documentação Automática:** Roteamento com interface interativa (Swagger UI) integrada no FastAPI para testes em tempo real de todos os endpoints.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.13
* **Framework Web (API):** FastAPI
* **Interface / Frontend:** Streamlit
* **Base de Dados:** PostgreSQL
* **ORM / Conexão:** SQLAlchemy
* **Segurança:** PyJWT & Passlib (Bcrypt)
* **Configurações:** `python-dotenv` para gerenciamento seguro de variáveis de ambiente

---

## 🔑 Boas Práticas de Segurança e Arquitetura
O projeto foi estruturado seguindo padrões rigorosos de desenvolvimento de software:
* **Isolamento de Credenciais:** Chaves críticas como `SECRET_KEY` e tempo de expiração de tokens são gerenciadas fora do código-fonte através de arquivos `.env` e protegidas via `.gitignore`.
* **Separação de Camadas:** Arquitetura limpa dividida em Roteadores (`routers`), Modelos de Banco (`models`), Esquemas de Validação (`schemas`) e o Painel Visual (`dashboard.py`).
* **Políticas de CORS:** Configuração de middlewares para permitir a comunicação fluida e segura entre o painel e o servidor da API.
* **Trilha de Auditoria (Audit Trail):** Rastreabilidade total das interações no sistema, garantindo visibilidade em tentativas de acesso incorretas ou fraudes.

---

## 🔧 Como Executar o Projeto (Desenvolvimento Local)

### 1. Configurar as Variáveis de Ambiente
Crie um arquivo chamado `.env` na raiz do seu projeto e insira suas configurações confidenciais:

SECRET_KEY="sua_chave_secreta_super_segura_e_longa"

ALGORITHM="HS256"

ACCESS_TOKEN_EXPIRE_MINUTES=30

---

2. Rodar o Backend (FastAPI)

Com o seu ambiente virtual ativo e as dependências instaladas, inicialize o servidor Uvicorn:

uvicorn app.main:app --reload

---

3. Rodar o Dashboard (Streamlit)
   
Em outro terminal (também com a venv ativa), initialize o painel visual do síndico:

streamlit run dashboard.py

---

👤 Desenvolvedora
Andrea Da Cruz Leonardo 

Desenvolvendo soluções inteligentes, seguras e prontas para o futuro da automação.
