# 📑 Registro de Operações de Tratamento de Dados Pessoais (ROPA)

===

## 1. Fluxo de Tratamento e Bases Legais
| Dado Pessoal | Finalidade Técnica | Base Legal (LGPD) |
| :--- | :--- | :--- |
| **E-mail** | Identificação única e envio de código 2FA. | Execução de Contrato (Art. 7, V) |
| **Senha (Hash BCrypt)** | Verificação de identidade sem armazenamento de texto claro. | Legítimo Interesse (Art. 7, IX) |
| **IP e Logs** | Prevenção de ataques (Rate Limiting) e auditoria. | Obrigação Legal (Art. 7, II) |

## 2. Segurança Defensiva (Medidas Técnicas)
O sistema implementa controles rigorosos para garantir a tríade de segurança (Confidencialidade, Integridade e Disponibilidade):
*   **Criptografia em Repouso:** Dados no Firestore utilizam AES-256.
*   **Criptografia em Trânsito:** Uso de TLS 1.2+ e HSTS obrigatório.
*   **Proteção Anti-Brute Force:** Custo de Hash BCrypt em nível 14 e monitoramento de tentativas falhas.
*   **Segregação de Sessão:** `Session_Cookie_Age` reduzido para 120s para prevenir sequestro de sessão em ambientes compartilhados.

## 3. Transferência Internacional
Considerando o uso da infraestrutura **Google Cloud (Firebase)**, os dados podem ser processados em servidores localizados fora do território nacional (EUA/UE). O tratamento é legitimado por cláusulas contratuais padrão que garantem nível de proteção adequado à LGPD.

## 4. Gestão de Incidentes
Em caso de detecção de vulnerabilidade ou acesso não autorizado:
1. O mecanismo de defesa ativa bloqueia a origem do tráfego.
2. Os logs são isolados para perícia técnica.
3. Os usuários afetados serão notificados via e-mail cadastrado em até 48 horas, conforme recomendação da ANPD.

## 5. Direitos dos Titulares
Os usuários podem exercer seus direitos de consulta, retificação e exclusão enviando uma solicitação formal aos desenvolvedores através do sistema.
