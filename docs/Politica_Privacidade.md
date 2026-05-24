# 📄 Aviso de Privacidade — Smarko Security
 
Este Aviso de Privacidade descreve como o projeto **Smarko Security** coleta, utiliza e protege os dados pessoais dos usuários, em conformidade com a Lei Geral de Proteção de Dados Pessoais (**LGPD**).
 
## 1. Agente de Tratamento
O Smarko Security é um projeto acadêmico de segurança defensiva desenvolvido por **Henrique Castro Moreira da Costa**, atuando como Controlador dos dados coletados.
 
## 2. Dados Coletados e Finalidade
Processamos apenas os dados estritamente necessários para as funções de segurança e autenticação do sistema:
 
*   **Perfil do Usuário:** Nome de usuário (username), e-mail e hash de senha criptografada (bcrypt) para fins de identificação e autenticação.
*   **Logs de Auditoria e Segurança:** Endereço IP, descrição de eventos do sistema (ex: solicitações de reset) e data/hora da ocorrência.
*   **Gestão de Acesso:** Controle de tentativas de login falhas e status de bloqueio de conta para prevenção de ataques de força bruta.
 
## 3. Base Legal para o Tratamento
*   **Execução de Contrato:** Necessário para o funcionamento da conta do usuário.
*   **Legítimo Interesse:** Para garantir a segurança da rede, proteção contra fraudes e auditoria de eventos críticos no sistema defensivo.
 
## 4. Compartilhamento e Operadores de Dados
Para garantir a persistência e segurança dos dados, utilizamos provedores de infraestrutura que atuam como operadores:
*   **Google Cloud (Firebase Firestore):** Os perfis e logs de segurança são armazenados em banco de dados NoSQL na nuvem, contando com criptografia em repouso.
*   **Google (SMTP/Gmail):** Processamento de e-mails para envio de tokens de recuperação e 2FA.
 
## 5. Medidas de Segurança Aplicadas
Conforme evidenciado na arquitetura do projeto:
*   **Criptografia de Senhas:** Uso de algoritmos de hash robustos (bcrypt/sha256).
*   **Segurança de Sessão:** Cookies protegidos com atributos *HttpOnly* e *Secure*, além de timeout de 120 segundos.
*   **Proteção de Transporte:** Comunicação integral via protocolo HTTPS/TLS.
 
## 6. Direitos do Titular e Retenção
O usuário pode solicitar a confirmação, acesso ou exclusão de seus dados a qualquer momento. Os dados são mantidos apenas pelo período necessário para a finalidade acadêmica e de segurança do projeto.
