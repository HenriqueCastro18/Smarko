# Guia de GitHub Actions - Smarko 2.0

## O que é e Por que Usar?

GitHub Actions executa testes automaticamente toda vez que você faz push ou abre PR. Isso valida que seu código:

1. ✅ Atende aos requisitos de segurança
2. ✅ Não quebra funcionalidades existentes
3. ✅ Mantém conformidade LGPD
4. ✅ Segue padrões de código

## Como Funciona

Quando você faz `git push` ou abre um Pull Request:

```
1. GitHub dispara o workflow "Security & Compliance Tests"
   ↓
2. Ubuntu 20.04 inicia (máquina virtual no GitHub)
   ↓
3. Python 3.10 e 3.11 são instalados (testa em ambas versões)
   ↓
4. Dependências do requirements.txt são instaladas
   ↓
5. Cada teste de requisito roda (1-6)
   ↓
6. Se tudo passar: ✅ Build green
   Se falhar: ❌ Build red + notificação
```

## Testes Executados

### 1. **AuthenticationTests**
Valida se senhas usam hashing seguro (bcrypt):
```python
test_password_hashing_uses_bcrypt()
test_login_requires_email_and_password()
test_session_expiration_configured()
test_rate_limiting_blocks_after_failures()
```

### 2. **PasswordRecoveryTests**
Valida fluxo de reset de senha:
```python
test_password_reset_token_generation()
test_password_reset_email_sent()
```

### 3. **CryptographyTests**
Valida HTTPS e headers de segurança:
```python
test_https_redirect_enabled()
test_hsts_header_enabled()
test_session_cookie_secure()
```

### 4. **LGPDComplianceTests**
Valida conformidade com lei de proteção de dados:
```python
test_privacy_policy_exists()
test_terms_of_service_exists()
test_consent_checkbox_required()
```

### 5. **AuditLoggingTests**
Valida que logs de segurança são registrados:
```python
test_log_function_exists()
test_ip_extraction_works()
```

### 6. **SecurityHeadersTests**
Valida headers HTTP de segurança:
```python
test_security_headers_present()
```

## Acessando Resultados

### No GitHub Web

1. Vá para seu repositório
2. Clique em "Actions" (aba no topo)
3. Veja os workflows em execução/concluídos

```
📊 Actions
├─ Security & Compliance Tests (latest)
│  ├─ ✅ Run #125 - 2min 34s
│  ├─ ✅ Run #124 - 2min 18s
│  └─ ❌ Run #123 - 2min 12s (falhou em LGPDComplianceTests)
└─ Lint
   └─ ✅ Run #125 - 45s
```

### Ver Logs Detalhados

1. Clique no workflow que falhou
2. Clique em "test (3.10)" ou "test (3.11)"
3. Veja cada teste em detalhe:

```
✓ Run Django tests
✓ Check authentication requirements
  - test_password_hashing_uses_bcrypt ... ok
  - test_login_requires_email_and_password ... ok
✓ Check password recovery
✓ Check cryptography & secure communication
❌ Check LGPD compliance
  FAILED: test_consent_checkbox_required
  Error: Privacy policy endpoint returned 404
```

## Configurar Notificações

### Receber emails quando build falha

1. GitHub > Settings > Notifications
2. Ativar "Email for build failures"

### Status badge no README

Adicione isto no `README.md`:

```markdown
[![Security & Compliance Tests](https://github.com/seu-usuario/Smarko-TFC/actions/workflows/security-tests.yml/badge.svg)](https://github.com/seu-usuario/Smarko-TFC/actions)
```

Aparecerá assim:
[![Security & Compliance Tests](https://img.shields.io/github/actions/workflow/status/seu-usuario/Smarko-TFC/security-tests.yml)](https://github.com/seu-usuario/Smarko-TFC/actions)

## Troubleshooting

### ❌ Erro: "ModuleNotFoundError: No module named 'firebase_admin'"

**Causa**: Dependência não instalada

**Solução**: Confirma que `firebase-admin==6.6.0` está em `requirements.txt`

### ❌ Erro: "Django settings not configured"

**Causa**: `DJANGO_SETTINGS_MODULE` não definido

**Solução**: Já incluído no workflow, mas se rodar localmente:
```bash
export DJANGO_SETTINGS_MODULE=Smarko.settings
python manage.py test Smarko_App.tests
```

### ❌ Erro: "DJANGO_SECRET_KEY not set"

**Causa**: Variável de ambiente não configurada

**Solução**: No GitHub:
1. Settings > Secrets and variables > Actions
2. Clique "New repository secret"
3. Nome: `DJANGO_SECRET_KEY`
4. Value: sua chave (gere com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)

### ❌ Testes passam localmente mas falham no GitHub

**Causa Comum**: Firebase credentials não configuradas no CI

**Solução**: Mocke Firebase nos testes:
```python
from unittest.mock import patch

@patch('Smarko_App.views.db')
def test_login(self, mock_db):
    mock_db.collection.return_value.document.return_value.get.return_value.to_dict.return_value = {...}
```

## Rodando Testes Localmente

Antes de fazer push:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar todos os testes
python manage.py test Smarko_App.tests -v 2

# 3. Rodar testes específicos
python manage.py test Smarko_App.tests.AuthenticationTests -v 2

# 4. Ver cobertura de testes
pip install coverage
coverage run --source='.' manage.py test Smarko_App.tests
coverage report
```

## Exemplo de Fluxo de Trabalho

```bash
# 1. Faça uma mudança na autenticação
# vim Smarko_App/views.py

# 2. Commit e push
git add .
git commit -m "refactor: improve 2FA token validation"
git push origin main

# 3. GitHub Actions roda automaticamente
# Aguarde ~2-3 minutos

# 4. Veja resultado
# Se falhou: git log, corrige, faz push novamente
# Se passou: ✅ pronto para produção!
```

## Status de Compliance

Cada build que passa no GitHub Actions gera um badge verde ✅ que mostra:

```
✅ Requisito 1: Autenticação & Gestão de Credenciais
✅ Requisito 2: Recuperação de Senha
✅ Requisito 3: Criptografia & Comunicação Segura
✅ Requisito 4: Conformidade LGPD
✅ Requisito 5: Auditoria e Logs
✅ Requisito 6: Headers de Segurança
```

Isso valida que seu TFC atende aos requisitos acadêmicos automaticamente a cada mudança!

## Próximos Passos

1. ✅ Faça commit deste arquivo
2. ✅ Espere o primeiro build rodar (3-5 min)
3. ✅ Veja resultado em Actions
4. ✅ Se houver falhas, corrija localmente e faça push novamente
5. ✅ Badge ✅ aparecerá no README quando tudo passar
