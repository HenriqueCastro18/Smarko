# 🔐 Política de Segurança da Informação — Smarko Security

Esta Política de Segurança da Informação define as diretrizes adotadas pelo projeto **Smarko Security** para proteger os dados, sistemas e usuários, garantindo confidencialidade, integridade e disponibilidade das informações.

---

## 1. Objetivo

Estabelecer práticas e medidas de segurança que reduzam riscos, previnam incidentes e garantam a proteção dos dados tratados pelo sistema.

---

## 2. Escopo

Esta política se aplica a:

* Dados de usuários cadastrados
* Informações de autenticação
* Logs de segurança e auditoria
* Infraestrutura e serviços utilizados pelo sistema

---

## 3. Princípios de Segurança

O projeto segue os principais pilares da segurança da informação:

* **Confidencialidade:** acesso aos dados apenas por pessoas autorizadas
* **Integridade:** garantia de que os dados não sejam alterados indevidamente
* **Disponibilidade:** sistema acessível sempre que necessário

---

## 4. Controle de Acesso

* O acesso ao sistema é realizado por autenticação com usuário e senha
* Senhas são armazenadas de forma criptografada
* Tentativas de login são monitoradas
* Contas podem ser temporariamente bloqueadas após múltiplas falhas de acesso
 
---

## 5. Autenticação e Sessão

* Uso de autenticação segura
* Sessões possuem tempo de expiração 
* Cookies configurados com atributos de segurança (*HttpOnly* e *Secure*)
* Possibilidade de autenticação em dois fatores (2FA)

---

## 6. Proteção de Dados

* Senhas protegidas com algoritmos de hash (bcrypt/sha256)
* Comunicação protegida via HTTPS/TLS
* Dados armazenados em ambiente seguro na nuvem
* Coleta apenas do mínimo necessário de informações

---

## 7. Monitoramento e Logs

* Registro de eventos importantes (login, tentativas falhas, recuperação de conta)
* Armazenamento de logs com data, hora e IP
* Monitoramento para identificação de comportamentos suspeitos

---

## 8. Gestão de Incidentes

Em caso de incidentes de segurança:

* O evento deve ser identificado e registrado
* Deve ser analisado o impacto nos dados
* Medidas corretivas devem ser aplicadas
* Quando necessário, os usuários podem ser notificados

---

## 9. Uso de Serviços de Terceiros

O sistema utiliza serviços externos para funcionamento:

* **Firebase (Google Cloud):** armazenamento de dados
* **Serviços de e-mail:** envio de notificações e autenticação

Esses serviços seguem padrões de segurança reconhecidos no mercado.

---

## 10. Backup e Continuidade

* Dados devem ser armazenados de forma segura
* Sempre que possível, devem existir mecanismos de backup
* O sistema deve buscar manter sua disponibilidade

---

## 11. Responsabilidades

* O desenvolvedor é responsável pela implementação das medidas de segurança
* Os usuários devem proteger suas credenciais de acesso
* Qualquer uso indevido deve ser reportado

---

## 12. Atualizações da Política

Esta política pode ser atualizada conforme o sistema evolui ou novas medidas de segurança sejam implementadas.

---

## 13. Considerações Finais

O **Smarko Security** foi desenvolvido com foco em segurança desde a base, aplicando boas práticas para proteger dados e reduzir riscos.

Mesmo sendo um projeto acadêmico, busca seguir padrões próximos aos utilizados em sistemas reais.
---
