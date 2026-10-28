# Referência: configuração local

| Variável | Padrão/uso | Observação |
|---|---|---|
| `APP_DATA_DIR` | `data` | Diretório persistente para projetos, mídia importada, exports e configurações. |
| `MODEL_CACHE_DIR` | `models` no Compose | Cache de modelos. |
| `ARGOS_PACKAGES_DIR` | `models/argos/packages` no Compose | Pacotes locais de tradução. |
| `WEB_PORT` | `8000` | Porta loopback do serviço Compose. |
| `DOCKER_CONTEXT` | `default` | Contexto Docker usado pelo Makefile. |
| `WHISPER_MODEL` | `medium` | Padrão para novos projetos; opções também podem ser escolhidas na interface. |
| `YOUTUBE_CLIENT_SECRETS` | `secrets/client_secret.json` local | Credencial OAuth opcional; mantenha fora do Git. |
| `OPENCODE_AUTH_FILE` | autenticação do OpenCode no host | Montada como somente leitura pelo Compose. |
| `CODEX_AUTH_FILE` | autenticação Codex no host | Montada como somente leitura pelo Compose. |

Copie `.env.example` para `.env` e ajuste apenas as variáveis necessárias. `.env` e diretórios locais são ignorados pelo Git. Para mudar `APP_DATA_DIR` em Compose, ajuste também o volume `./data:/data` em `compose.yaml` para o novo caminho persistente.
