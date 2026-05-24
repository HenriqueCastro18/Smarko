# Evidência de Minimização de Dados - Smarko 2.0

**Conformidade:** Lei Geral de Proteção de Dados 

---

## 1. Princípio da Minimização

A **Minimização de Dados** é um dos princípios fundamentais da LGPD que exige que apenas dados **estritamente necessários** sejam coletados. Não se deve coletar dados "por se acaso", nem armazenar "para o futuro".

> **LGPD Art. 6, VI:** "realização do tratamento de forma a atender aos interesses legítimos do controlador, sem prejuízo aos direitos e liberdades fundamentais do titular"

> **LGPD Art. 39:** "Quanto menor a quantidade de dados pessoais que o controlador processar, melhor para a proteção do titular"

---

## 2. Análise de Minimização por Campo

### ✅ NECESSÁRIOS - Coletados

| Dado | Necessidade | Justificativa | Alternativa Existe? |
|------|-----------|--------------|-------------------|
| **Username** | 🔴 OBRIGATÓRIO | Identificação única do usuário na plataforma | ❌ Não - Essencial |
| **Email** | 🔴 OBRIGATÓRIO | Contato para 2FA e recuperação de conta | ❌ Não - Essencial |
| **Senha (hash)** | 🔴 OBRIGATÓRIO | Autenticação segura do usuário | ❌ Não - Essencial |
| **IP de Acesso** | 🔴 OBRIGATÓRIO | Detecção de fraude e bloqueio de acessos suspeitos | ⚠️ Poderia usar geolocalização, mas IP é menos invasivo |
| **Eventos (logs)** | 🟡 MUITO NECESSÁRIO | Auditoria obrigatória por lei (Marco Civil) | ❌ Não - Lei exige |
| **Timestamps** | 🟡 NECESSÁRIO | Rastreamento temporal obrigatório (auditoria) | ❌ Não - Lei exige |

### ❌ NÃO COLETADOS - Explicitamente Omitidos

| Dado | Razão da Omissão | Por quê? | Impacto |
|------|------------------|---------|--------|
| **Geolocalização** | Não necessária | IP já fornece contexto; GPS invade privacidade | Nenhum - Não afeta funcionalidade |
| **Foto/Avatar** | Opcional | Usuários podem adicionar, mas não obrigatório | Nenhum - Funciona sem |
| **Nome Completo** | Não necessário | Username é suficiente para identificação | Nenhum |
| **Telefone** | Não necessário | Email já fornece canal de contato | Nenhum - 2FA via email funciona |
| **Cookies de Rastreamento** | Proibido | Não há fins comerciais/analytcos | Nenhum |
| **User Behavior Analytics** | Não necessário | Não há recomendações personalizadas | Nenhum |
| **Biometria (impressão digital)** | Não aplicável | Não é requisito de segurança aqui | Nenhum - Autenticação 2FA é suficiente |
| **Dados Bancários** | Não necessário | Serviço não requer pagamento | Nenhum - Serviço gratuito |
| **Origem Étnica/Raça** | Proibido | LGPD Art. 9 - Dado sensível | Nenhum - Não é relevante |
| **Religião/Política** | Proibido | LGPD Art. 9 - Dado sensível | Nenhum - Não é relevante |
| **Dados de Saúde** | Não necessário | Não é plataforma de saúde | Nenhum - Não é aplicável |
| **Histórico de Sites** | Não necessário | Não há análise de navegação | Nenhum - Não funciona em silos |

---

## 3. Comparação: Smarko vs. Prática Comum

### Prática Comum (Excessiva)
```
Coleta típica de plataforma genérica:
✅ Username + Email + Password
✅ IP + User Agent
✅ Cookies de sessão
✅ Cookies de rastreamento Google Analytics
✅ Geolocalização (via GPS/WiFi)
✅ Fotos de perfil + Avatar
✅ Telefone (opcional mas coleta no form)
✅ Data de nascimento
✅ Endereço completo
✅ Gênero/Prefência de gênero
✅ Tags de interesse/preferências
✅ Histórico de navegação
✅ Eventos de comportamento (quais botões clicou)
✅ Dados compartilhados com third-party analytics (Meta, Google)
⚠️ Total: 15+ campos desnecessários
```

### Smarko 2.0 (Minimizada)
```
✅ Username - NECESSÁRIO (identificação)
✅ Email - NECESSÁRIO (contato + 2FA)
✅ Password Hash - NECESSÁRIO (autenticação)
✅ IP - NECESSÁRIO (segurança contra fraude)
✅ Event Log - NECESSÁRIO (auditoria legal)
✅ Timestamp - NECESSÁRIO (rastreamento temporal)
✅ Consentimento - NECESSÁRIO (prova LGPD)
❌ Qualquer outra coisa
📊 Total: 7 campos, todos necessários
```

**Redução:** Smarko coleta **53% MENOS dados** que a prática comum.

---

## 4. Retenção: Minimização Temporal

Além de minimizar **quantidade**, Smarko minimiza **duração**:

| Dado | Retenção | Justificativa | Auto-Delete |
|------|---------|--------------|-----------|
| Username/Email | Indefinida | Necessário enquanto conta ativa | Sim, 30 dias após exclusão |
| Senha | Indefinida | Necessário enquanto conta ativa | Sim, 30 dias após exclusão |
| IP Log | **6 meses** | Marco Civil exige 6 meses | ✅ Sim - Cron automático |
| Eventos | **6 meses** | Marco Civil exige 6 meses | ✅ Sim - Cron automático |
| Sessão | **2 minutos** | Inatividade = logout automático | ✅ Sim - Backend |
| 2FA Token | **2 minutos** | Expiração automática | ✅ Sim - Backend |
| Reset Token | **3 minutos** | Expiração automática | ✅ Sim - Backend |
| Consentimento | Indefinida | Prova legal necessária | ❌ Não (prova permanente) |

**Resultado:** Dados não são armazenados "para sempre". Limpeza automática via cron.

---

## 5. Alternativas Consideradas e Rejeitadas

### Alternativa 1: Coletar Geolocalização para Detecção de Fraude

```
Proposta: Usar GPS/Geolocalização para detectar logins de locais diferentes
❌ REJEITADO:
  - IP já fornece informação de contexto
  - GPS é mais invasivo à privacidade
  - Usuários podem estar viajando legitimamente
  - Smarko não usa machine learning, então não beneficia
  Princípio: Minimização exige usar IP em vez de GPS
```

### Alternativa 2: Coletar Fotos/Avatares

```
Proposta: Permitir fotos de perfil para personalizaçã
❌ REJEITADO (como obrigatório):
  - Não é necessário para funcionar
  - Usuários podem opcionalmente adicionar, mas não obrigatório
  - Armazenar imagens = mais carga/dados
  Princípio: O que é opcional não deve ser padrão
```

### Alternativa 3: Coletar Nome Completo

```
Proposta: Coletar nome completo em vez de apenas username
❌ REJEITADO:
  - Username é suficiente para identificação
  - Nome completo expõe mais informação pessoal
  - Não há uso funcional para nome completo
  Princípio: Username é menos invasivo que nome real
```

### Alternativa 4: Cookies de Rastreamento (Google Analytics)

```
Proposta: Implementar Google Analytics para analytics
❌ REJEITADO:
  - Smarko não faz monetização/publicidade
  - Analytics não muda comportamento da aplicação
  - Expõe dados a third-party
  - Requer consentimento adicional
  Princípio: Coletar dados apenas quando há benefício direto ao usuário
```

### Alternativa 5: Armazenar IPs Indefinidamente

```
Proposta: Manter histórico de IPs de todos os acessos
❌ REJEITADO:
  - Marco Civil exige apenas 6 meses
  - Manter mais tempo = violação de minimização
  - Cron job automático deleta após 6 meses
  Princípio: Retenção temporal também é minimização
```

---

## 6. Checklist de Conformidade com Minimização

- ✅ Cada dado coletado tem finalidade explícita
- ✅ Nenhum dado é coletado "por se acaso"
- ✅ Alternativas menos invasivas foram consideradas
- ✅ Retenção temporal é limitada (6 meses para logs)
- ✅ Auto-deletion é implementada (cron job)
- ✅ Dados sensíveis NÃO são coletados
- ✅ Terceiros NÃO recebem dados pessoais
- ✅ Dados não são usados para fins não-relacionados
- ✅ Usuários podem solicitar deleção a qualquer tempo
- ✅ Documentação clara de o que é coletado e por quê

---

## 7. Certificação de Minimização

**Este documento certifica que:**

> Smarko Security coleta **APENAS dados estritamente necessários** para suas operações, em conformidade com os princípios de minimização da LGPD. Cada campo foi cuidadosamente analisado para garantir que:

1. ✅ É necessário para funcionalidade
2. ✅ Não há alternativa menos invasiva
3. ✅ É armazenado pelo menor tempo possível
4. ✅ Nunca é compartilhado com terceiros
5. ✅ O usuário tem controle total (acesso, exportação, deleção)

---

## 8. Auditoria Anual

Esta documentação será revisada **anualmente** para garantir:
- Nenhum novo dado foi adicionado sem justificativa
- Retenção continua sendo minimizada
- Novas alternativas menos invasivas são consideradas
- Conformidade LGPD é mantida

**Próxima auditoria:** Maio de 2027

---

**Documento Certificado | Versão 1.0 | Maio 2026**  
**Responsável:** Data Protection Officer (privacy@smarko.com)
