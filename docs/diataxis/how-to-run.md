# Como iniciar o aplicativo local

Este guia descreve a execução em desenvolvimento. O uso do contêiner depende de um daemon Docker ativo.

## Requisitos

- Python 3.12 ou posterior
- `uv`
- FFmpeg com `ffprobe`
- Conexão de rede na primeira análise para baixar os modelos locais de transcrição e tradução
- Para sugestões semânticas e revisão visual, configure pelo menos um executor: OpenCode autenticado no host ou Codex CLI autenticado no host. O OpenCode usa `opencode/mimo-v2.6-flash-free`; o Codex usa `gpt-6-luna` com esforço `medium`.

## Executar no host

Na raiz do projeto, execute:

```sh
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra <http://127.0.0.1:8000>. Importe um arquivo MKV ou MP4, inicie a análise, revise as sugestões e exporte os itens aprovados. O app salva arquivos de trabalho em `data/` e modelos em `models/`; ambos ficam fora do Git.

A análise vem pré-selecionada com Whisper `medium`. Depois de importar o vídeo, escolha a qualidade no campo **Qualidade da transcrição** antes de clicar em **Analisar gravação**: `tiny`, `base`, `small`, `medium` ou `large-v3`. `large-v3` oferece a maior qualidade entre as opções completas, com maior uso de memória, mais tempo de processamento e um download maior na primeira análise. A escolha fica salva no projeto. A transcrição de nomes próprios e termos técnicos ainda precisa de revisão.

Depois da transcrição local, o backend chama o OpenCode com `opencode/mimo-v2.6-flash-free` para sugerir remoções e cortes verticais/horizontais. Autentique o OpenCode no host com `opencode auth login`; não há chave de IA para configurar no estúdio. O checkbox de validação visual começa marcado; desmarque-o para enviar somente texto. A tela mostra o motivo, uma citação de evidência e a origem da sugestão. Se o OpenCode falhar, as regras locais ainda produzem sugestões revisáveis. Todas as sugestões continuam pendentes até você revisá-las.

O padrão inicial pode ser definido com `WHISPER_MODEL` no ambiente do Compose; por exemplo, `WHISPER_MODEL=large-v3 docker compose up --build`. A escolha feita no projeto prevalece para aquela análise.

Se FFmpeg não estiver instalado, instale o pacote do sistema da sua distribuição e reinicie o aplicativo. O painel de estado informa se `ffmpeg` e `ffprobe` estão disponíveis.

## Executar com Docker Compose

Com Docker Desktop ou outro daemon Docker ativo, o Project Gallery pode iniciar e parar o serviço usando os alvos `make start` e `make stop` da raiz. A Gallery passa a porta local reservada por `WEB_PORT`; o Makefile usa o contexto Docker `default` (substituível por `DOCKER_CONTEXT`) e mantém o serviço em loopback. Para iniciar fora da Gallery, execute:

```sh
make start
```

O serviço fica disponível em `http://127.0.0.1:${WEB_PORT:-8000}`. Para encerrar, execute `make stop`; `data/` e `models/` persistem no host. O Compose monta os arquivos de autenticação configurados em `OPENCODE_AUTH_FILE` e `CODEX_AUTH_FILE` como somente leitura. Ajuste os caminhos no `.env`; escolha o executor ativo em `/settings`. A configuração OAuth do YouTube é opcional para análise/exportação e está descrita em [Como conectar o YouTube](how-to-connect-youtube.md).

## Privacidade

O arquivo de vídeo, a transcrição por áudio e a tradução de legendas são processados localmente. Para sugestões semânticas, o backend envia a transcrição com tempos ao executor selecionado: MiMo via OpenCode ou GPT-6 Luna via Codex. Se a validação visual estiver ligada, envia também até 8 frames reduzidos ao mesmo executor; o arquivo de vídeo completo nunca é enviado. O uso segue os limites e condições da conta autenticada no executor selecionado. As sugestões podem conter erros e precisam de revisão. A rede também é usada para baixar modelos na primeira execução e para a integração YouTube se você a configurar. O upload para o YouTube só ocorre depois de selecionar **Aprovar revisão e enviar como privado**.

## Navegar pelo estúdio

**Gravações** abre a galeria com busca, filtro, paginação e acesso para renomear projetos. As etapas e abas organizam análise, edição, cortes, legendas e publicação. Consulte [Como revisar e exportar](how-to-review.md) para os controles de revisão. As credenciais do YouTube e a seleção/disponibilidade do provedor de análise aparecem em **Configurações**, acessível também em `/settings`.
