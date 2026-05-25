# Notas de Implementação - Smarko 2.0

## Histórico de Decisões Técnicas

### Autenticação (Requisito 1)

Usamos Firebase Authentication com hash PBKDF2/bcrypt no Django porque:
- Firebase gerencia tokens de forma segura
- Django hash garante segunda camada de proteção
- Rate limiting foi implementado manualmente em `views.py:195-200` após alguns testes mostrarem que força bruta era possível

O bloqueio de 5 minutos após 3 tentativas falhas foi testado empiricamente e funciona bem em produção.

### 2FA via Email (Requisito 1.5-1.6)

Inicialmente tentei usar TOTP (Google Authenticator) mas usuários reclamaram da complexidade. Email é mais acessível.

O código de 6 dígitos expira em 2 minutos - foi achado empiricamente que:
- Menos de 2 min: muitos usuários não conseguem digitar a tempo
- Mais de 3 min: segurança comprometida
- 2 min é o sweet spot

### Recuperação de Senha (Requisito 2)

Firebase fornece o `oobCode` nativamente. Armazenamos em Firestore com timestamp para validação extra de expiração (180 segundos).

Problema que tivemos: tokens sendo reutilizados. Solução: `token_ref.delete()` após uso bem-sucedido em `views.py:365`.

### Criptografia e HTTPS (Requisito 3)

- HTTPS obrigatório via `SECURE_SSL_REDIRECT=True`
- HSTS header por 1 ano (365 dias em produção)
- Firebase gerencia chaves (AES-256 nativo)

Testamos com curl e verificamos headers:
```bash
curl -I https://smarko.app
```

### Conformidade LGPD (Requisito 4)

A parte mais demorada. Implementamos:
- Coleta explícita de consentimento com checkboxes
- Histórico de versões de política
- Endpoint de revogação (`/revoke-consent/`)
- Exportação de dados em JSON (`/data-access-request/`)
- Agendamento de exclusão com período de reflexão

Usuários queriam ver o que temos sobre eles - criamos `/user-data/` como dashboard.

### Logs e Auditoria (Requisito 5)

Cada ação de segurança registra:
- IP do cliente
- Timestamp
- Tipo de evento (login, 2FA falha, reset de senha, etc)

Armazenamos em Firestore collection `logs_seguranca`. Logs são read-only após 30 dias para compliance.

## Problemas Encontrados e Soluções

### Problema 1: Firebase SDK não inicializa
**Sintoma**: ValueError quando app é inicializado 2 vezes

**Solução**: Usar `try/except` global e variável `db`

### Problema 2: Email de 2FA indo para spam
**Sintoma**: Usuários não recebem código

**Solução**: 
- Adicionei SPF/DKIM records
- Mudei "Smarko" para "Smarko Security" no subject
- Adicionar logo na imagem do email

### Problema 3: Session timeout muito curto
**Sintoma**: Usuários sendo desconectados a cada 2 minutos

**Original**: `SESSION_COOKIE_AGE = 120` segundos
**Agora**: `SESSION_COOKIE_AGE = 3600` segundos (1 hora)

## Como Testar Localmente

```bash
# Instalar deps
pip install -r requirements.txt

# Rodar testes
python manage.py test Smarko_App.tests

# Rodar servidor
python manage.py runserver

# Testar 2FA (via terminal)
curl -X POST http://localhost:8000/login/ \
  -d "username=test@example.com&password=teste123"
```

## Dados Sensíveis

Credenciais Firebase armazenadas em `.env`:
- FIREBASE_PROJECT_ID
- FIREBASE_PRIVATE_KEY (rotacionada a cada 90 dias)
- FIREBASE_CLIENT_EMAIL
- FIREBASE_WEB_API_KEY

Nunca fazer commit disso no repo. Usar GitHub Secrets para CI/CD.

## Performance

- Firestore queries otimizadas com índices (criados via console)
- Rate limiting não bloqueia IPs legítimos em proxies
- Email de 2FA envia em ~3 segundos

## TODO Futuro

- [ ] Implementar WebAuthn (FIDO2) como alternativa a 2FA
- [ ] Audit logs importáveis para SIEM
- [ ] Biometria no frontend (Web API)
- [ ] Rate limiting por usuário (não só por IP)
