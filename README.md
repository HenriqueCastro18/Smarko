# 🛡️ Smarko 2.0 - Autenticação Defensiva + Conformidade LGPD

## 📌 Sobre o Projeto
**O Smarko é um sistema de automação comercial focado no gerenciamento de mercados. O grande diferencial desta aplicação é a sua arquitetura robusta de segurança e autenticação, garantindo a integridade dos dados, o controle rigoroso de acesso dos usuários e conformidade total com a LGPD (Lei Geral de Proteção de Dados).**

> **Status do Projeto:** ✅ Funcional / TFC (Trabalho de Final de Curso)
> **Versão:** 2.0 - Com LGPD Compliance & Advanced Security

---

## ⚖️ Conformidade e Privacidade (LGPD)

**Smarko 2.0 implementa conformidade total com LGPD (Lei Geral de Proteção de Dados Pessoais):**

### Requisitos LGPD Implementados ✅
1. ✅ **Listagem completa de dados pessoais** — Dashboard `/user-data/` com inventário
2. ✅ **Associação de dados a finalidades** — Mapeamento via `DataPurpose` + `ConsentRecord`
3. ✅ **Evidência de minimização de dados** — Documentação + validação no registro
4. ✅ **Registro explícito de consentimento** — Checkboxes obrigatórios no signup
5. ✅ **Consentimento associado à finalidade** — Multi-select por propósito de processamento
6. ✅ **Possibilidade de revogação** — Endpoint `/revoke-consent/` com confirmação por email
7. ✅ **Registro de data e versão** — Histórico completo com timestamps
8. ✅ **Consulta aos dados do titular** — Exportação JSON `/data-access-request/`

### Documentação LGPD
* [Política de Cookies](./docs/Politica_Cookies.md)
* [Aviso de Privacidade](./docs/Politica_Privacidade.md)
* [Termos de Uso](./docs/Termo_Uso.md)
* [Inventário de Dados (LGPD)](./docs/INVENTARIO_DADOS_LGPD.md)
* [Finalidades de Processamento (LGPD)](./docs/FINALIDADES_PROCESSAMENTO_LGPD.md)
* [Minimização de Dados (LGPD)](./docs/MINIMIZACAO_DADOS_LGPD.md)
* [Tratamento de Dados](./docs/Tratamento_de_Dados.md)
* [Relatorio de impacto a proteção de dados](./docs/Relatorio_de_impacto_a_proteção_de_dados.md)
* [Politica de Segurança da informação](./docs/Politica_de_Segurança_da_informação.md)

---

## 📊 Gerenciamento de Dados LGPD

### Funcionalidades de Controle de Dados do Usuário

| Feature | Endpoint | Descrição |
| :--- | :--- | :--- |
| **Ver Meus Dados** | `/user-data/` | Dashboard com perfil, histórico de consentimento e logs de auditoria |
| **Exportar Dados** | `/data-access-request/` | Download JSON com todos os dados pessoais (direito de portabilidade) |
| **Revogar Consentimento** | `/revoke-consent/` | Parar processamento de dados com confirmação por email |
| **Política de Privacidade** | `/privacy/` | Versão atual com histórico de mudanças |
| **Atualizar Consentimento** | `/update-consent/` | Reaceitação obrigatória para usuários legados |
| **Solicitar Exclusão** | `/request-deletion/` | Agendamento de exclusão com período de 30 dias para arrependimento |
| **Cancelar Exclusão** | `/cancel-deletion/` | Link por email para cancelar solicitação antes da exclusão |

### Limpeza Automática de Dados

```bash
# Executar diariamente:
python manage.py cleanup_old_logs  # Delete logs > 6 meses (LGPD Art. 15-18)
```

---

## 🚀 Tech Stack

O projeto utiliza tecnologias de ponta para garantir performance, integridade e conformidade:

### Backend
* **Linguagem:** Python 3.10+
* **Framework:** Django 5.1.8
* **Banco de Dados (Local):** SQLite3
* **Banco de Dados (Produção):** Firestore (Google Cloud)
* **Autenticação:** Firebase Authentication

### Bibliotecas de Segurança & LGPD
* `firebase-admin` — Autenticação e Firestore
* `bcrypt==4.1.2` — Hashing com 14 rounds
* `python-dotenv` — Gestão segura de variáveis de ambiente
* `django-cors-headers` — CORS controlado
* `requests` — Chamadas seguras a APIs externas
* `whitenoise` — Servir estáticos em produção

### Frontend
* **HTML5** com Bootstrap 5
* **CSS3** com variáveis de tema
* **JavaScript vanilla** (sem frameworks pesados)
* **Bootstrap Icons** para ícones

---

## 🔒 Camadas de Segurança Implementadas

### 1. Proteção de Credenciais
* **BCrypt SHA-256** com **14 rounds** de custo (aumentado de 12 para mais segurança)
* Hashing computacionalmente caro, protegendo contra ataques de dicionário e *rainbow tables*
* Senha nunca é armazenada em texto plano

### 2. Autenticação Multifator (2FA)
* **Two-Factor Authentication via Email** com código de 6 dígitos
* Expiração de código em **120 segundos**
* Audit logging de tentativas (válidas e inválidas)
* Proteção contra replay attacks

### 3. Rate Limiting & Account Lockout
* **3 tentativas de login** antes de bloqueio
* **5 minutos de cooldown** automático após limite atingido
* Audit logging de tentativas de força bruta
* IP tracking para detecção de padrões anormais

### 4. Gestão de Sessão Segura
* **Signed Cookies** (sem banco de dados de sessão)
* **HttpOnly Cookies** — previne acesso via JavaScript
* **SameSite=Lax** — proteção contra CSRF
* **Secure Flag** ativado em produção (Vercel)
* **Timeout de 2 minutos** para sessões inativas

### 5. Proteção contra CSRF
* Tokens CSRF em todos os formulários
* Validação de origem de requisição
* Cookie CSRF com proteção SameSite

### 6. Auditoria e Logging
* **Registro detalhado de eventos** no Firestore:
  - Criação de conta
  - Login com sucesso
  - Tentativas de login falhadas (senha incorreta)
  - Bloqueio de conta (exceção de 3 tentativas)
  - Validação 2FA (código expirado/inválido)
  - Reset de senha
  - Operações de consentimento LGPD
  - Revogação de consentimento
  - Solicitação de exclusão de dados
* Cada log contém: `usuario_id`, `usuario_nome`, `evento`, `ip`, `data_hora`

### 7. Controle de Acesso por Papel (RBAC)
* **3 papéis:** `user` (padrão), `developer`, `admin`
* Exibição de role dinâmico na dashboard
* Funcionalidade de migração para usuários existentes
* Extensível para novos papéis

### 8. Criptografia em Trânsito
* **TLS/HTTPS** obrigatório em produção
* **HSTS** (HTTP Strict Transport Security) por 1 ano
* Redirecionamento automático HTTP → HTTPS
* Suporte a proxies reversos (Vercel)

---

## ⚙️ Configuração do Ambiente

O projeto exige um arquivo `.env` na raiz do diretório para funcionar corretamente.

**Variáveis obrigatórias:**
* `SECRET_KEY` = sua_chave_secreta_aqui
* `EMAIL_USER` = exemplo@gmail.com
* `EMAIL_PASS` = Pass do email.

---

## 🛠️ Automação (Setup Local)

Para facilitar o desenvolvimento e a instalação, utilize os scripts `.bat` inclusos (ambiente Windows):

1.  **Instalação:** Execute `install.bat` para criar o ambiente virtual (`venv`), instalar dependências e rodar as migrações do banco de dados.
2.  **Execução:** Execute `run.bat` para ativar o ambiente e inicializar o servidor de desenvolvimento.

---

## 📍 Endpoints Principais

### Autenticação
| Endpoint | Método | Função | Segurança |
| :--- | :--- | :--- | :--- |
| `/login/` | POST | Autenticação primária | Rate Limit (3 tentativas) & CSRF |
| `/verificar_2fa/` | POST | Validação 2FA | Expiração 120s & Audit Logging |
| `/register/` | POST | Criar nova conta | CSRF & Validação LGPD |
| `/reset_password/` | POST | Solicitar reset | Rate Limit & Token Seguro |
| `/reset_confirm/` | POST | Confirmar novo password | Token expirado em 24h |
| `/logout/` | POST | Encerrar sessão | CSRF & Audit Logging |

### Gerenciamento de Dados (LGPD)
| Endpoint | Método | Função | Autenticação |
| :--- | :--- | :--- | :--- |
| `/user-data/` | GET | Ver dados pessoais + consentimento | Firebase Login Obrigatório |
| `/data-access-request/` | POST | Exportar dados em JSON | Firebase Login Obrigatório |
| `/revoke-consent/` | POST | Revogar consentimento + email | Firebase Login Obrigatório |
| `/request-deletion/` | POST | Agendar exclusão (30 dias) | Firebase Login Obrigatório |
| `/cancel-deletion/` | GET | Cancelar exclusão via link | Token por email |
| `/update-consent/` | GET/POST | Reaceitação de política | Sesão pré-auth |
| `/privacy/` | GET | Política de privacidade + versões | Público |

### Páginas Principais
| Endpoint | Função | Status |
| :--- | :--- | :--- |
| `/` | Home (dashboard) | ✅ Logado |
| `/home/` | Dashboard completa | ✅ Logado |
| `/admin/` | Painel Django Admin | 🔒 Superuser Only |

---

## 🚀 Deploy no Vercel

### Pré-requisitos
1. Conta no Vercel (vercel.com)
2. Projeto no GitHub (push do repositório)
3. Firebase Service Account JSON
4. Variáveis de ambiente configuradas

### Passo 1: Adicionar Variáveis de Ambiente no Vercel
Na dashboard do Vercel, adicione em **Settings → Environment Variables**:

```
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=False
FIREBASE_API_KEY=sua_firebase_web_key
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",..}
EMAIL_USER=seu_email@gmail.com
EMAIL_PASS=sua_senha_app
VERCEL=True
```

### Passo 2: Configurar Build
Vercel detecta Django automaticamente. Certifique-se de ter:
- `requirements.txt` atualizado
- `Procfile` ou `vercel.json` (opcional)

### Passo 3: Deploy
```bash
# Vercel CLI
npm i -g vercel
vercel
```

Ou conecte seu GitHub repo diretamente na dashboard do Vercel.

### Segurança em Produção
✅ HTTPS automático  
✅ HSTS headers ativados  
✅ Cookies Secure=True  
✅ Redirecionamento HTTP→HTTPS  
✅ Firestore criptografia AES-256  

---

## 📚 Estrutura do Projeto

```
Smarko-TFC/
├── Smarko/                          # Configurações Django
│   ├── settings.py                  # Segurança + LGPD
│   ├── urls.py                      # Rotas principais
│   └── wsgi.py                      # WSGI para produção
├── Smarko_App/                      # Aplicação principal
│   ├── views.py                     # Lógica de autenticação + LGPD
│   ├── models.py                    # ConsentRecord, DataPurpose, etc
│   ├── templates/                   # HTML com Bootstrap 5
│   ├── static/                      # CSS/JS
│   └── management/commands/         # Cleanup automático
├── docs/                            # Documentação LGPD
│   ├── INVENTARIO_DADOS_LGPD.md
│   ├── FINALIDADES_PROCESSAMENTO_LGPD.md
│   └── MINIMIZACAO_DADOS_LGPD.md
├── .env.example                     # Template de variáveis
├── requirements.txt                 # Dependências Python
└── README.md                        # Este arquivo
```

---

## 👤 Autores

**Henrique Castro** <br/>
**Victor Fozato** <br/>
**Rafael Barbosa** 
