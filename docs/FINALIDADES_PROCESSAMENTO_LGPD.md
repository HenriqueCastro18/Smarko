# Finalidades de Processamento de Dados - Smarko 2.0

**Conformidade:** Lei Geral de Proteção de Dados 
---

## Finalidades Registradas

### Finalidade 1: Autenticação e Acesso

**Descrição:** Permitir que o usuário acesse a plataforma de forma segura através de verificação de credenciais e autenticação de dois fatores.

**Dados Utilizados:**
- Username
- Email
- Senha (hash)
- Código 2FA (temporário, 2 minutos)

**Objetivo Específico:**
- Validar identidade do usuário
- Permitir login seguro
- Gerar token de sessão
- Manter sessão ativa (heartbeat)

**Base Legal:** 
- ✅ Consentimento do Usuário (LGPD Art. 7, I)
- ✅ Contrato (LGPD Art. 7, III) - Necessário para usar o serviço

**Necessário:** **SIM** - Obrigatório
**Retenção:** Dados indefinidos; sessão expira em 2 minutos de inatividade

**Legislação Aplicável:**
- Consentimento obtido durante registro
- Usuário pode revogar a qualquer momento
- Revogação afeta acesso futuro

---

### Finalidade 2: Segurança e Detecção de Fraude

**Descrição:** Proteger a conta do usuário contra acessos não autorizados, detectar padrões suspeitos e investigar tentativas de fraude.

**Dados Utilizados:**
- IP de Acesso
- Tentativas de Login (contador)
- User Agent (browser/device)
- Histórico de Eventos

**Objetivo Específico:**
- Detectar múltiplas tentativas de login falhas
- Bloquear conta temporariamente após 3 tentativas
- Registrar acessos incomuns
- Investigar comportamentos suspeitos

**Base Legal:**
- ✅ Obrigação Legal (LGPD Art. 7, II) - Proteção do usuário
- ✅ Interesse Legítimo (LGPD Art. 7, IX) - Defesa de direitos

**Necessário:** **SIM** - Obrigatório
**Retenção:** IP registrado por 6 meses, depois deletado automaticamente

**Detalhes de Implementação:**
- Bloqueio automático após 3 tentativas falhas
- Desbloqueio automático em 5 minutos
- Logs armazenados por auditoria
- Cron job deleta logs > 6 meses

---

### Finalidade 3: Comunicação e Notificações

**Descrição:** Enviar mensagens ao usuário para autenticação, recuperação de conta e notificações importantes de segurança.

**Dados Utilizados:**
- Email
- Nome de Usuário (para personalização)
- Código 2FA (6 dígitos, gerado aleatoriamente)
- Link de Reset (com token único de 3 minutos)

**Objetivo Específico:**
- Enviar código 2FA por email
- Enviar link de reset de senha
- Notificar sobre mudanças de segurança
- Confirmar ações sensíveis

**Base Legal:**
- ✅ Consentimento (LGPD Art. 7, I)
- ✅ Contrato (LGPD Art. 7, III) - Serviço requer comunicação
- ✅ Obrigação Legal (LGPD Art. 7, II) - Notificações de segurança

**Necessário:** **SIM** - Obrigatório
**Retenção:** Tokens expiram em:
- 2FA: 2 minutos
- Reset Link: 3 minutos (deletado após uso)
- Email armazenado indefinidamente

**Email Enviados:**
1. Código de Verificação 2FA (durante login)
2. Link de Reset de Senha (durante reset)
3. Confirmação de Revogação de Consentimento
4. Alerta de Exclusão de Conta (com opção de cancelar)

---

### Finalidade 4: Conformidade e Auditoria

**Descrição:** Manter registros de todas as atividades para conformidade regulatória, investigação de incidentes e defesa legal.

**Dados Utilizados:**
- ID do Usuário (Firebase UID)
- Nome de Usuário
- Tipo de Evento (Login, Reset, Consentimento, etc)
- IP de Acesso
- Timestamp
- User Agent
- Status da Ação

**Objetivo Específico:**
- Rastrear quem fez o quê e quando
- Investigar incidentes de segurança
- Demonstrar conformidade regulatória
- Defesa em caso de disputa legal
- Auditoria interna

**Eventos Registrados:**
- `Conta Criada` - Novo usuário
- `Login Sucesso` - Autenticação bem-sucedida
- `Login Falha` - Tentativa falhou
- `Bloqueio de Conta` - Bloqueada por segurança
- `Desbloqueio` - Desbloqueio de conta
- `Senha Redefinida` - Senha alterada
- `Reset Solicitado` - Link de reset enviado
- `Consentimento LGPD Concedido` - Aceito
- `Consentimento Atualizado` - Novo consentimento
- `Consentimento Revogado` - Retirado
- `Exclusão Solicitada` - Deleção iniciada
- `Exclusão Cancelada` - Deleção abortada

**Base Legal:**
- ✅ Obrigação Legal (LGPD Art. 7, II) - Conformidade regulatória
- ✅ Interesse Legítimo (LGPD Art. 7, IX) - Defesa de direitos

**Necessário:** **SIM** - Obrigatório
**Retenção:** **6 meses** conforme "Marco Civil da Internet"
- Auto-deletion via cron job diário
- Apagamento irreversível

**Conformidade Legal:**
- Marco Civil da Internet (Lei 12.965/2014) - Art. 15
- Exigência: manter por mínimo 6 meses
- Smarko: implementa exato 6 meses + auto-delete

---

### Finalidade 5: Gestão de Consentimento (Próprio LGPD)

**Descrição:** Registrar, rastrear e gerenciar o consentimento do usuário conforme exigências da LGPD. Manter prova de quando e como o consentimento foi obtido.

**Dados Utilizados:**
- Firebase UID
- Email no momento do consentimento
- Versão da política aceita
- Data/hora do consentimento
- IP de consentimento
- User Agent (browser/device)
- Checkboxes aceitas (termos, privacidade, por finalidade)
- Data/hora de revogação (se aplicável)

**Objetivo Específico:**
- Provar consentimento foi obtido
- Manter histórico de todas as versões
- Permitir revogação a qualquer momento
- Rastrear quando cada versão foi aceita
- Demonstrar conformidade LGPD

**Base Legal:**
- ✅ Obrigação Legal (LGPD Art. 8, 13, 14) - Prova de consentimento

**Necessário:** **SIM** - Obrigatório para LGPD
**Retenção:** Indefinida (prova auditável)

**Ciclo de Vida do Consentimento:**
1. **Novo Consentimento** - Usuário novo ou atualização
2. **Ativo** - Consentimento válido e em uso
3. **Revogado** - Usuário retirou consentimento
4. **Deletado** - Exclusão de conta

---

## Resumo de Bases Legais

| Finalidade | Base Legal | Obrigatório |
|-----------|-----------|-----------|
| Autenticação | Consentimento + Contrato | ✅ SIM |
| Segurança | Obrigação Legal + Interesse Legítimo | ✅ SIM |
| Comunicação | Consentimento + Contrato + Obrigação Legal | ✅ SIM |
| Auditoria | Obrigação Legal | ✅ SIM |
| Consentimento | Obrigação Legal (LGPD) | ✅ SIM |

---

## Princípio da Proporcionalidade

Cada finalidade é:
- ✅ Explícita - Claramente definida
- ✅ Necessária - Não há alternativa
- ✅ Proporcional - Dados coletados são mínimos
- ✅ Documentada - Registrada neste documento
- ✅ Limitada - Usada apenas para a finalidade descrita

---

## Acesso e Compartilhamento

**Quem Acessa os Dados:**
- ✅ Equipe de Segurança - Para investigações
- ✅ Admin da Plataforma - Para manutenção
- ❌ Terceiros - Dados NÃO são vendidos/compartilhados
- ❌ Publicidade - Sem dados para marketing

---

## Mudanças em Finalidades

Se futuras versões adicionarem novas finalidades:
1. Será criada uma nova versão desta documentação
2. Usuários serão notificados
3. Novo consentimento será solicitado
4. Versão anterior permanece registrada

---

**Documento de Conformidade | Versão 1.0 | Maio 2026**  
**Próxima Revisão: Maio 2027 ou quando houver mudanças**
