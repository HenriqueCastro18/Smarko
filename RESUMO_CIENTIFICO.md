# Resumo Científico - Sistema Smarko 2.0

## Resumo (200-300 palavras)

**Smarko 2.0** é um sistema web de autenticação defensiva com conformidade integral à Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018). O projeto implementa camadas múltiplas de segurança criptográfica e controles de acesso para proteger credenciais e dados pessoais contra ataques modernos, enquanto garante aos usuários direitos de consulta, portabilidade e exclusão de dados conforme mandatório pela legislação brasileira.

**Objetivo:** Desenvolver uma arquitetura de autenticação que combina padrões de segurança da indústria com conformidade regulatória, demonstrando a viabilidade técnica de integrar proteção de dados desde o design (privacy-by-design).

**Metodologia Técnica:**
- Implementação de hashing criptográfico com BCrypt-SHA256 (14 rounds) para armazenamento seguro de senhas
- Autenticação multifator (2FA) via email com tokens de 6 dígitos
- Rate limiting e bloqueio de conta (3 tentativas, 5 minutos de cooldown)
- Gestão de sessão com cookies assinados (120s de expiração, HttpOnly, SameSite=Lax)
- Criptografia em repouso (AES-256 nativo do Firestore) e em trânsito (TLS 1.2+, HSTS)

**Mecanismos de Segurança:**
- Proteção contra força bruta, injeção SQL, XSS e CSRF
- Auditoria completa via logs estruturados no Firestore
- Validação de integridade de dados com hashes SHA-256
- Isolamento de segredos (API keys, credenciais) via variáveis de ambiente

**Conformidade LGPD:** 
Sistema implementa os 8 requisitos fundamentais: listagem de dados coletados, associação a finalidades legais, minimização de dados, consentimento explícito e revogável, portabilidade (exportação JSON), exclusão agendada (30 dias), histórico de versões de política e auditoria completa.

**Resultados:** Prototipo funcional validando viabilidade técnica de conformidade simultânea com segurança de nível empresarial, adequado para sistemas comerciais em produção.

## Terminologia Técnica

- **BCrypt:** Algoritmo de hashing adaptativo com fator de trabalho configurável (rounds)
- **2FA (Two-Factor Authentication):** Autenticação de dois fatores aumentando segurança
- **Rate Limiting:** Proteção contra ataques de força bruta limitando tentativas
- **Cookies Assinados:** Cookies criptograficamente verificados contra manipulação
- **AES-256:** Advanced Encryption Standard com chave de 256 bits (padrão militar)
- **TLS (Transport Layer Security):** Protocolo de criptografia para comunicação segura
- **HSTS (HTTP Strict Transport Security):** Obrigatoriedade de HTTPS via header HTTP
- **LGPD:** Lei Geral de Proteção de Dados (Lei 13.709/2018 do Brasil)
- **Privacy-by-Design:** Princípio de incorporar privacidade desde o design inicial

## Qualidade Textual e Científica

O sistema foi desenvolvido seguindo normas técnicas internacionais (NIST Special Publications, OWASP Top 10) e legislação brasileira específica, com documentação técnica detalhada, testes de segurança e auditoria formal de conformidade.
