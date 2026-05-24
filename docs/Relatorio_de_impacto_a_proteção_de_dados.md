# 📄 Aviso de Privacidade — Smarko Security

Este Aviso de Privacidade explica, de forma clara e direta, como o projeto **Smarko Security** coleta, utiliza e protege os dados dos usuários, seguindo as diretrizes da Lei Geral de Proteção de Dados (LGPD).

---

## 1. Quem é responsável pelos dados?

O **Smarko Security** é um projeto acadêmico voltado à segurança defensiva que atua como responsável (controlador) pelos dados coletados no sistema.

---

## 2. Quais dados são coletados e por quê?

O sistema coleta apenas o necessário para funcionar com segurança:

* **Informações de conta:** nome de usuário, e-mail e senha (armazenada de forma criptografada)
  → usados para identificar o usuário e permitir o login

* **Logs de segurança:** endereço IP, eventos do sistema (como tentativas de login ou redefinição de senha) e data/hora
  → usados para monitoramento e prevenção de atividades suspeitas

* **Controle de acesso:** tentativas de login e bloqueios temporários
  → usados para evitar ataques como força bruta

---

## 3. Por que esses dados podem ser usados?

Os dados são tratados com base em:

* **Execução do serviço:** necessário para criar e manter a conta do usuário
* **Legítimo interesse:** garantir a segurança do sistema, prevenir fraudes e registrar atividades importantes

---

## 4. Os dados são compartilhados com alguém?

Alguns serviços são utilizados para que o sistema funcione corretamente:

* **Google Cloud (Firebase Firestore):** onde os dados e logs ficam armazenados com segurança
* **Serviços de e-mail (SMTP/Gmail):** usados para envio de recuperação de senha e autenticação em duas etapas (2FA)

Esses serviços atuam apenas como suporte técnico (operadores), seguindo boas práticas de segurança.

---

## 5. Como os dados são protegidos?

O projeto aplica medidas importantes de segurança, como:

* Senhas protegidas com criptografia (bcrypt/sha256)
* Uso de HTTPS para proteger a comunicação
* Cookies seguros (HttpOnly e Secure)
* Sessões com tempo de expiração (timeout)
* Monitoramento de atividades suspeitas

---

## 6. Quais são os seus direitos?

Você pode, a qualquer momento:

* Solicitar acesso aos seus dados
* Corrigir informações
* Pedir a exclusão da sua conta
* Revogar permissões concedidas

---

## 7. Por quanto tempo os dados ficam armazenados?

Os dados são mantidos apenas pelo tempo necessário para o funcionamento do sistema e para fins acadêmicos relacionados ao projeto.

---

## 8. Considerações finais

O **Smarko Security** foi desenvolvido com foco em boas práticas de segurança e respeito à privacidade dos usuários, buscando sempre utilizar apenas o mínimo necessário de dados e protegê-los da melhor forma possível.

---
