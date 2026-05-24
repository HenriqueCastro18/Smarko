# Arquitetura do Sistema Smarko 2.0

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENTE (Browser)                          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Frontend     │  │ LocalStorage │  │ Session Cookies (HttpOnly)  │
│  │ HTML/CSS/JS  │  │ (Não usado)  │  │ - uid, username, email    │
│  └──────┬───────┘  └──────────────┘  └──────────────────────────┘ │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          │ HTTPS (TLS 1.2+)
          │ HSTS Header Obrigatório
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│                  VERCEL (Aplicação Django)                         │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Django 5.1.8                            │  │
│  │  ┌───────────────┐  ┌──────────────────┐  ┌────────────┐  │  │
│  │  │  views.py    │  │  models.py       │  │  urls.py   │  │  │
│  │  │              │  │                  │  │            │  │  │
│  │  │ - register   │  │ - ConsentRecord  │  │ - /auth    │  │  │
│  │  │ - login      │  │ - DataCategory   │  │ - /lgpd    │  │  │
│  │  │ - 2FA        │  │ - DataPurpose    │  │ - /user    │  │  │
│  │  │ - reset pass │  │ - AccountDel..   │  │ - /privacy │  │  │
│  │  │ - LGPD ops   │  │                  │  │            │  │  │
│  │  └───┬─────────┘  └────────┬──────────┘  └────────────┘  │  │
│  │      │                     │                              │  │
│  │      └─────────┬───────────┘                              │  │
│  │                │                                          │  │
│  │  ┌─────────────▼──────────────┐                           │  │
│  │  │  Middleware & Segurança    │                           │  │
│  │  │                            │                           │  │
│  │  │ - SecurityMiddleware       │                           │  │
│  │  │ - SessionMiddleware        │                           │  │
│  │  │ - CsrfViewMiddleware       │                           │  │
│  │  │ - AuthenticationMiddleware │                           │  │
│  │  │ - XFrame/XXSProtection     │                           │  │
│  │  └─────────────┬──────────────┘                           │  │
│  │                │                                          │  │
│  └────────────────┼──────────────────────────────────────────┘  │
│                   │                                             │
└───────────────────┼─────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        │ (HTTPS)   │ (HTTPS)   │ (SMTP/SendGrid)
        │           │           │
┌───────▼──────┐   │   ┌────────▼──────────┐
│   Firebase   │   │   │ SendGrid (Email)  │
│ Auth API     │   │   │                   │
│              │   │   │ - 2FA codes       │
│ - login      │   │   │ - Reset links     │
│ - register   │   │   │ - Notifications   │
│ - password   │   │   └───────────────────┘
└──────────────┘   │
                   │
            ┌──────▼──────┐
            │  Firestore  │
            │  (NoSQL)    │
            │             │
            │ ┌─────────┐ │
            │ │ perfis  │ │
            │ ├─────────┤ │
            │ │ consent │ │
            │ ├─────────┤ │
            │ │  logs   │ │
            │ ├─────────┤ │
            │ │ tokens  │ │
            │ └─────────┘ │
            │             │
            │ Criptografia│
            │ AES-256     │
            │ (Nativa)    │
            └─────────────┘
```

## Fluxos Principais

### 1. Fluxo de Autenticação (Login + 2FA)

```
1. Usuário submete email/senha
   │
2. Django valida contra Firebase Auth
   │
3. Se OK, gera código 6-dígitos
   │
4. Envia email via SendGrid
   │
5. Usuário submete código
   │
6. Valida código (120s expiração)
   │
7. Cria sessão (120s cookie, HttpOnly)
   │
8. Registra log em Firestore
   │
9. Redireciona para dashboard
```

### 2. Fluxo de Consentimento LGPD

```
No Registro:
1. Exibe checkboxes de Termos/Privacidade
   │
2. Usuário aceita (consentimento obrigatório)
   │
3. Salva registro em Firestore
   │
Logout/Login Posterior:
4. Verifica se consentimento está ativo
   │
5. Se não, força revalidação
   │
6. Registra versão e timestamp
   │
7. Permite acesso apenas após revalidação
```

### 3. Fluxo de Exclusão de Dados (LGPD)

```
1. Usuário solicita exclusão
   │
2. Django cria token único
   │
3. Envia email com link de cancelamento
   │
4. Agenda exclusão para 30 dias depois
   │
5. Registra request em Firestore
   │
6. Se não cancelado em 30 dias:
   a. Deleta perfil do Firestore
   b. Deleta logs/consentimentos/tokens
   c. Deleta conta Firebase
   d. Registra evento de exclusão
```

## Componentes de Segurança

### Proteção de Credenciais
- **Armazenamento:** BCrypt-SHA256 (14 rounds)
- **Transmissão:** TLS 1.2+ obrigatório
- **Validação:** Nunca em texto plano

### Proteção de Sessão
- **Assinatura:** Signed cookies (Django)
- **Expiração:** 120 segundos
- **Flags:** HttpOnly, Secure (prod), SameSite=Lax
- **Storage:** Nunca em localStorage

### Proteção contra Força Bruta
- **Rate Limit:** 3 tentativas de login
- **Cooldown:** 5 minutos automáticos
- **Registro:** Log de cada tentativa com IP

### Auditoria Completa
- **Firestore logs_seguranca:** Todos eventos
- **Campos:** usuario_id, evento, ip, data_hora
- **Retenção:** 6 meses + limpeza automática
- **Integridade:** Gravação do lado do servidor

## Dependências Críticas

| Tecnologia | Versão | Função |
|:---|:---|:---|
| Django | 5.1.8 | Framework web principal |
| Firebase Admin | Latest | Autenticação + Firestore |
| BCrypt | 4.1.2 | Hashing de senhas |
| SendGrid | Latest | Envio de emails |
| WhiteNoise | Latest | Arquivos estáticos em produção |
| Python | 3.10+ | Runtime |

## Modelo de Dados (Firestore Collections)

```
perfis/{uid}
├── username: string
├── email: string
├── senha_hash: string (BCrypt)
├── tentativas_falhas: integer
├── bloqueado_ate: timestamp
├── created_at: timestamp
└── role: string (user/developer/admin)

consent_records/{firebase_uid}
├── firebase_uid: string
├── email: string
├── version: string
├── purposes: array
├── accepted_terms: boolean
├── accepted_privacy: boolean
├── given_at: timestamp
├── revoked_at: timestamp (null se ativo)
├── ip_address: string
└── user_agent: string

logs_seguranca/
├── usuario_id: string
├── usuario_nome: string
├── evento: string
├── ip: string
├── data_hora: timestamp

tokens_recuperacao/{oobCode}
├── email: string
└── criado_em: number (unix timestamp)

account_deletion_requests/{uid_token}
├── firebase_uid: string
├── email: string
├── requested_at: timestamp
├── deletion_scheduled_for: timestamp
├── confirmation_token: string
└── status: string (pending/canceled/completed)
```

## Conformidade e Regulamentação

- **LGPD Art. 37:** Registro de Operações de Processamento de Dados Pessoais (ROPA)
- **OWASP:** Top 10 - A07:2021 Authentication & A05:2021 Access Control
- **NIST:** SP 800-63B (Authentication) & SP 800-63C (Federation & Assertions)
- **Marco Civil da Internet:** Art. 15 (retenção mínima de logs = 6 meses)

## Deploýment e Infraestrutura

- **Plataforma:** Vercel (Serverless)
- **Banco de Dados:** Google Cloud Firestore (Multi-region)
- **Email:** SendGrid (SMTP relayed)
- **SSL/TLS:** Automático via Vercel
- **DNS:** Vercel + domínio customizado
- **Backup:** Automático via Google Cloud

