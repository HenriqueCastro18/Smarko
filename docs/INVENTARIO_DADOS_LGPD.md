# Inventário de Dados Pessoais - Smarko 2.0

**Conformidade:** Lei Geral de Proteção de Dados 
---

## 1. Dados Pessoais Coletados

### Categoria: Identificação

**Nome de Usuário (username)**
- Coletado em: Registro
- Armazenado em: Firestore (collection: `perfis`)
- Finalidade: Identificação do usuário
- Retenção: Indefinida (enquanto conta ativa)
- Necessário: SIM (obrigatório)

### Categoria: Contato

**Email**
- Coletado em: Registro, Login
- Armazenado em: Firebase Auth + Firestore
- Finalidade: Autenticação, Comunicação, 2FA
- Retenção: Indefinida (enquanto conta ativa)
- Necessário: SIM (obrigatório)

### Categoria: Credencial

**Senha (Hash BCrypt + SHA256)**
- Coletado em: Registro, Reset
- Armazenado em: Firebase Auth + Firestore
- Finalidade: Autenticação Segura
- Retenção: Indefinida
- Criptografia: BCrypt 14 rounds (irreversível)
- Necessário: SIM (obrigatório)

### Categoria: Segurança

**IP de Acesso**
- Coletado em: Login, 2FA, Reset
- Armazenado em: Firestore (collection: `logs_seguranca`)
- Finalidade: Detecção de Fraude, Segurança
- Retenção: **6 meses**, depois auto-deletado
- Necessário: SIM (obrigatório)

**Eventos de Auditoria**
- Coletado em: Cada ação significativa
- Tipos: Login, Logout, Reset, Consentimento, etc
- Armazenado em: Firestore (`logs_seguranca`)
- Finalidade: Conformidade, Auditoria
- Retenção: **6 meses**
- Necessário: SIM (obrigatório)

**Timestamp de Eventos**
- Coletado em: Automaticamente
- Armazenado em: Firestore
- Finalidade: Rastreamento temporal
- Retenção: **6 meses**
- Necessário: SIM

### Categoria: Consentimento

**Registro de Consentimento (ConsentRecord)**
- Coletado em: Registro + Atualizações
- Armazenado em: Django Database
- Dados: UID, Email, Versão, Data, IP, User Agent, Status
- Finalidade: Prova de Conformidade LGPD
- Retenção: Indefinida (prova auditável)
- Necessário: SIM (obrigatório LGPD)

---

## 2. Dados NÃO Coletados

✅ **Garantidamente Não Coletamos:**
- Localização/GPS
- Fotos/Vídeos
- Cookies de rastreamento
- Dados biométricos
- Informações bancárias
- Dados familiares
- Informações de saúde
- Origem étnica/racial
- Religião/Política
- Atividade em redes sociais

---

## 3. Conformidade com Minimização

| Dado | Necessário | Justificativa |
|------|-----------|--------------|
| Username | ✅ | Identificação única |
| Email | ✅ | Contato/2FA essencial |
| Senha | ✅ | Segurança obrigatória |
| IP | ✅ | Detecção fraude |
| Logs | ✅ | Auditoria legal |
| Consentimento | ✅ | Prova LGPD |
| Localização | ❌ | Não funcional |
| Rastreamento | ❌ | Não comercial |
| Biometria | ❌ | Não aplicável |

**Conclusão:** Apenas dados **estritamente necessários** são coletados.

---

## 4. Direitos do Titular

- ✅ Acessar dados: `/user-data/`
- ✅ Exportar dados: `/data-access-request/` (JSON)
- ✅ Revogar consentimento: `/revoke-consent/`
- ✅ Excluir conta: `/request-deletion/` (30 dias)
- ✅ Transparência: Política de Privacidade

---

**Versão 1.0 | Maio 2026**
