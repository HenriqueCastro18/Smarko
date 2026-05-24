## 1. Testes de Segurança Realizados

Os seguintes testes foram executados para validar a implementação segura:

### 1.1 Testes de Autenticação
- ✅ **Login com credenciais inválidas:** Validação de erro 401 sem exposição de informações
- ✅ **Força bruta (3+ tentativas):** Bloqueio automático com cooldown de 5 minutos
- ✅ **Token 2FA expirado (>120s):** Rejeição e redirecionamento para novo código
- ✅ **Sessão timeout (>120s AFK):** Invalidação automática requerendo re-autenticação
- ✅ **Logout:** Invalidação completa da sessão via `session.flush()`

### 1.2 Testes de Criptografia
- ✅ **Hashing BCrypt:** Validação de 14 rounds, impossibilidade de recuperação de senha original
- ✅ **TLS/HTTPS em produção:** Enforced via SECURE_SSL_REDIRECT + HSTS header (1 ano)
- ✅ **Cookies assinados:** Impossibilidade de modificação sem SECRET_KEY
- ✅ **Dados em Firestore:** Criptografia AES-256 nativa verificada via Google Cloud console

### 1.3 Testes de Proteção contra Ataques
- ✅ **XSS (Cross-Site Scripting):** HttpOnly cookies + Escape HTML automático no Django template
- ✅ **CSRF (Cross-Site Request Forgery):** Token CSRF obrigatório em todos formulários POST
- ✅ **SQL Injection:** ORM Django utiliza parametrização; Firestore não sujeito a SQL
- ✅ **Host Header Injection:** ALLOWED_HOSTS configurado com whitelist explícita
- ✅ **Clickjacking:** X-Frame-Options = DENY via SecurityMiddleware

### 1.4 Testes de Auditoria e Logging
- ✅ **Registro de logins:** Todos sucessos/falhas registrados em logs_seguranca
- ✅ **Tentativas 2FA:** Código expirado/inválido registrado com timestamp
- ✅ **Reset de senha:** Email enviado registrado; link utilizado registrado
- ✅ **Operações LGPD:** Consentimento, revogação, exclusão todas auditadas com IP + User-Agent

### 1.5 Testes de Conformidade LGPD
- ✅ **Consentimento:** Registro em Firestore com timestamp, versão, propósito
- ✅ **Revogação:** Atualiza campo `revoked_at`, envia email de confirmação
- ✅ **Exportação de dados:** Endpoint `/data-access-request/` retorna JSON completo
- ✅ **Exclusão agendada:** 30 dias + link de cancelamento por email
- ✅ **Limpeza automática:** Comando `cleanup_old_logs` remove logs > 6 meses

### 1.6 Testes Manuais Executados
| Teste | Status | Evidência |
|:---|:---|:---|
| Login com email válido | ✅ Passa | Redirecionamento para 2FA |
| Login com senha incorreta (3x) | ✅ Bloqueia | Mensagem "bloqueado 5 min" |
| 2FA com código correto | ✅ Sessão criada | Cookie `uid` assinado no navegador |
| Reset password + link | ✅ Funciona | Email recebido, senha atualizada |
| Revoga consentimento | ✅ Registrado | Firestore `revoked_at` preenchido |
| Solicita exclusão | ✅ Agendada | Email de cancelamento recebido |
| Acesso sem autenticação | ✅ Redireciona | Django `@firebase_login_required` funciona |

---

## 2. Conformidade com Normas Técnicas

- **OWASP Top 10 2021:**
  - A01:2021 – Broken Access Control: ✅ Decorador `@firebase_login_required`
  - A05:2021 – Access Control: ✅ RBAC (roles: user/developer/admin)
  - A07:2021 – Authentication: ✅ 2FA + Rate Limit
  - A02:2021 – Cryptographic Failures: ✅ TLS 1.2+, AES-256, BCrypt-SHA256

- **NIST SP 800-63B (Authentication):**
  - ✅ Memorized Secret Strength: Validação de senha forte no Django
  - ✅ Out-of-Band Devices: 2FA via email (SMS equivalente)
  - ✅ Activation & Binding: Email confirmation + consent binding

- **Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018):**
  - ✅ Art. 5 - Definições: Dados pessoais identificados e categorizados
  - ✅ Art. 7 - Base Legal: Consentimento explícito no registro
  - ✅ Art. 15-18 - Direitos do Titular: Acesso, portabilidade, exclusão
  - ✅ Art. 37 - ROPA: Registro de operações de processamento

---

## 3. Estratégia de Criptografia e Comunicação Segura (Smarko Security)

Para garantir a confidencialidade e integridade dos dados transitados e armazenados no sistema Smarko, adotamos os seguintes padrões e algoritmos criptográficos da indústria:

### 3.1. Dados em Trânsito (TLS/HTTPS)
* **Estratégia:** Toda a comunicação entre o cliente e o servidor exige tráfego cifrado.
* **Justificativa Técnica:** O Django foi configurado (`SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`) para forçar o redirecionamento HTTP para HTTPS e garantir que cookies de sessão não sejam interceptados em redes abertas. Utilizamos HSTS (`SECURE_HSTS_SECONDS`) para prevenir ataques de *downgrade* de protocolo.

### 3.2. Dados em Repouso (AES-256)
* **Estratégia:** Criptografia transparente de dados armazenados no banco de dados.
* **Justificativa Técnica:** O Smarko utiliza o Google Cloud Firestore como solução de banco de dados (NoSQL). O Firestore criptografa automaticamente todos os dados em repouso antes de serem gravados no disco, utilizando o algoritmo **AES-256** (Advanced Encryption Standard), considerado de nível militar e resistente a ataques de força bruta modernos.

### 3.3. Armazenamento de Senhas (PBKDF2)
* **Estratégia:** Senhas nunca são armazenadas em texto plano, passando por um processo de *hashing* com *salt* dinâmico.
* **Justificativa Técnica:** Utilizamos o algoritmo **PBKDF2** combinado com a função de hash **SHA-256** (`BCryptSHA256PasswordHasher` do Django). Esta escolha adiciona um custo computacional (work factor) que inviabiliza ataques de dicionário e *rainbow tables*, protegendo as credenciais mesmo em caso de vazamento do banco de dados.

### 3.4. Gestão de Chaves Criptográficas e Segredos
* **Estratégia:** Isolamento completo de chaves de API e segredos de aplicação do código-fonte.
* **Justificativa Técnica:** A `SECRET_KEY` do Django e a `FIREBASE_WEB_API_KEY` são injetadas no ambiente de execução via variáveis de ambiente (`.env`). O arquivo `.env` e o certificado `serviceAccountKey.json` são estritamente ignorados pelo controle de versão (Git) para prevenir a exposição acidental de credenciais críticas.