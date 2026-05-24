# 📄 Política de Cookies — Smarko Security
 
Este documento estabelece as diretrizes sobre o uso de cookies e tecnologias de rastreamento no sistema **Smarko Security**, em estrita conformidade com a Lei Geral de Proteção de Dados Pessoais (**LGPD**). Como um projeto de segurança focado em autenticação defensiva para automação comercial, a transparência no tratamento de dados técnicos é um pilar fundamental da nossa arquitetura.
 
## 1. Definição e Propósito
Cookies são identificadores alfanuméricos transferidos para o navegador do usuário para permitir que o sistema reconheça o estado da navegação, garanta a segurança da sessão e proteja a integridade dos dados trafegados entre o cliente e o servidor Django.
 
## 2. Inventário de Cookies Técnicos e Medidas de Segurança
O Smarko Security utiliza exclusivamente **cookies estritamente necessários**. Implementamos camadas adicionais de endurecimento (*hardening*) para garantir que esses identificadores não sejam interceptados ou manipulados.
 
| Nome Técnico | Finalidade | Medidas de Segurança Aplicadas |
| :--- | :--- | :--- |
| `sessionid` | Gerenciamento de sessão e manutenção do estado de login. | **HttpOnly**: Impede acesso via JavaScript (mitiga XSS). <br> **Secure**: Transmitido apenas via HTTPS. |
| `csrftoken` | Proteção contra ataques *Cross-Site Request Forgery*. | **Secure**: Só viaja em conexões cifradas (HTTPS). |
| `messages` | Armazenamento temporário de notificações e alertas do sistema. | Persistência volátil (limpa após o consumo da mensagem). |
 
## 3. Configurações de Ciclo de Vida e Proteção Ativa
Com base na análise do código-fonte e nas configurações de segurança do projeto, aplicamos as seguintes políticas restritivas:
 
*   **Expiração Curta (Timeout):** Os cookies de sessão expiram em **120 segundos** de inatividade, mitigando riscos de sequestro de sessão (*Session Hijacking*).
*   **Encerramento de Sessão:** O sistema invalida o cookie automaticamente assim que o navegador é fechado (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`).
*   **Proteção contra XSS:** O uso de `SESSION_COOKIE_HTTPONLY = True` garante que os cookies de sessão fiquem invisíveis para scripts maliciosos no navegador.
*   **Segurança de Transporte (HSTS):** O sistema utiliza o cabeçalho *Strict Transport Security* para forçar navegadores a interagirem apenas via conexões seguras por 1 ano.
 
## 4. Cookies de Terceiros e Rastreamento
*   **Ausência de Rastreamento Comercial:** O Smarko Security não utiliza cookies de publicidade, marketing ou rastreadores de terceiros (como Google Analytics ou redes sociais).
*   **Foco em Privacidade:** Todos os identificadores processados possuem finalidade estritamente técnica, alinhada aos objetivos de segurança e proteção de dados do projeto.
 
## 5. Gestão de Preferências
O usuário pode configurar seu navegador para bloquear ou alertar sobre esses cookies, entretanto, a desativação impossibilitará o acesso à área restrita do sistema. O processo de autenticação em duas etapas (**2FA**) e as camadas de proteção defensiva dependem diretamente da persistência desses cookies para validar a identidade com segurança.
