# Como instalar e executar localmente

Este guia ajuda a preparar uma cópia local do estúdio e escolher entre execução direta no host ou Docker Compose. As duas opções mantêm projetos e modelos no computador. A execução por Compose usa FFmpeg dentro da imagem; a execução no host precisa de FFmpeg instalado no sistema.

## O que você precisa

### Para executar no host

- Git, para clonar o repositório.
- Python 3.12 ou posterior.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/), para criar o ambiente e instalar as dependências Python a partir de `uv.lock`.
- FFmpeg e `ffprobe`, acessíveis pelo `PATH`. O aplicativo usa ambos para inspecionar, analisar e exportar mídia.
- Acesso à internet na primeira análise para baixar o modelo Whisper escolhido e, quando necessário, pacotes de tradução Argos.

### Para executar com Docker Compose

- Git e Docker Engine com o plugin `docker compose`, ou Docker Desktop com o Compose disponível.
- Daemon Docker iniciado e acessível ao seu usuário.
- Uma CLI de análise autenticada no host para sugestões semânticas: OpenCode ou Codex. O Compose monta a CLI e o arquivo de autenticação do host no contêiner. Sem um provedor disponível, a aplicação ainda inicia e oferece sugestões locais baseadas em regras.

Não é necessário instalar Python, `uv` ou FFmpeg no host para usar o caminho Compose: eles são incluídos na imagem. Também não é necessário Node.js para executar pelo host; os CLIs de IA são opcionais e instalados separadamente. Node.js é usado pela imagem Docker para fornecer esses CLIs.

## Obter o código

```sh
git clone https://github.com/alsvinicius/ai-studioeditor.git
cd ai-studioeditor
```

Não copie gravações, tokens ou arquivos de autenticação para a pasta do projeto. O `.gitignore` exclui os diretórios locais de dados e modelos.

## Opção A: executar no host

Instale Python 3.12+, `uv`, FFmpeg e `ffprobe` conforme as instruções oficiais da sua plataforma. Confirme que os programas estão disponíveis:

```sh
python3 --version
uv --version
ffmpeg -version
ffprobe -version
```

Na raiz do clone, instale as dependências travadas e inicie o servidor:

```sh
uv sync --locked
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra <http://127.0.0.1:8000>. `uv` cria o ambiente virtual local em `.venv/`. O servidor fica vinculado a loopback; não o exponha a uma rede não confiável.

Para sugestões semânticas, instale e autentique uma das ferramentas suportadas no host:

- OpenCode: instale a [CLI OpenCode](https://opencode.ai/docs/) e autentique com `opencode auth login`.
- Codex: instale a [CLI Codex](https://developers.openai.com/codex/cli/) e autentique-a. O aplicativo procura a CLI `codex` no `PATH`. Na execução pelo host, defina `CODEX_AUTH_FILE` com o caminho do arquivo `auth.json` da instalação Codex; o padrão interno `/run/secrets/codex-auth.json` é voltado ao contêiner.

Escolha o provedor em **Configurações → Provedor de análise**. A autenticação não é necessária para iniciar o app; sem ela, a análise semântica fica indisponível e as regras locais continuam produzindo sugestões. O texto da transcrição é enviado ao provedor escolhido; o envio de frames reduzidos depende da opção de validação visual. O vídeo completo permanece local. Consulte [como revisar e exportar](review-and-export.md) para o fluxo de trabalho e seus limites.

## Opção B: executar com Docker Compose

O Compose salva dados persistentes em `data/` e modelos em `models/`. O Makefile mantém o serviço em loopback e usa a porta `8000` por padrão.

1. (Opcional) Copie `.env.example` para `.env` e ajuste os caminhos de autenticação se os arquivos do seu host estiverem em locais diferentes. `.env` é ignorado pelo Git.
2. Para usar análise semântica, instale e autentique OpenCode ou Codex no host. Por padrão, o Compose procura `~/.local/share/opencode/auth.json` e `~/.codex/auth.json`; os caminhos podem ser alterados por `OPENCODE_AUTH_FILE` e `CODEX_AUTH_FILE` no `.env`. Os arquivos são montados como somente leitura.
3. Inicie a imagem e aguarde o teste de saúde:

   ```sh
   make start
   ```

4. Abra <http://127.0.0.1:8000>. Encerre o serviço quando terminar:

   ```sh
   make stop
   ```

Para escolher outra porta, defina `WEB_PORT` nos comandos, por exemplo `WEB_PORT=8010 make start` e `WEB_PORT=8010 make stop`. O Makefile usa o contexto Docker `default`; para outro contexto, defina `DOCKER_CONTEXT`. Para alterar o modelo Whisper padrão de projetos novos, defina `WHISPER_MODEL` antes de iniciar, por exemplo `WHISPER_MODEL=large-v3 make start`. A qualidade também pode ser escolhida por projeto na interface.

O arquivo `.env.example` inclui valores para integrar o cliente OAuth do YouTube por ambiente. Para a maioria das instalações, configure a integração pela tela **Configurações → YouTube**; veja [como conectar o YouTube](connect-youtube.md). OAuth é opcional para análise e exportação.

## Dados, modelos e primeira análise

Por padrão, projetos, gravações importadas, exports, configurações e tokens ficam em `data/`; modelos de transcrição e tradução ficam em `models/`. Esses diretórios são ignorados pelo Git. Restrinja o acesso aos dados locais e mantenha backups protegidos. A [referência de configuração](../reference/configuration.md) descreve as variáveis e os diretórios.

Escolha o idioma e a qualidade da transcrição ao iniciar a análise. O padrão é Whisper `medium`; opções maiores, como `large-v3`, exigem mais memória, espaço e tempo. A primeira análise baixa o modelo Whisper selecionado. Uma tradução pode baixar pacotes Argos adicionais. Mantenha acesso à internet até que os downloads terminem.

## Verificar disponibilidade e resolver problemas

- Abra `/api/health` no mesmo endereço do estúdio. A resposta informa se FFmpeg e `ffprobe` estão disponíveis, se o YouTube está autorizado e o estado do provedor selecionado.
- Se a interface indicar FFmpeg indisponível na execução pelo host, instale `ffmpeg` e `ffprobe`, confirme que ambos estão no `PATH` e reinicie o servidor.
- Se a análise semântica estiver indisponível, confira **Configurações → Provedor de análise** e confirme que a CLI escolhida está instalada e autenticada no host. Para Compose, confira também se o caminho do arquivo de autenticação no `.env` existe antes de iniciar o contêiner.
- Se a porta padrão estiver ocupada no Compose, escolha outra com `WEB_PORT` para iniciar e parar o serviço.
- Se o contêiner não iniciar, confirme que o daemon e o plugin Compose estão disponíveis com `docker compose version`; consulte a saída de `docker compose logs post-production`.

## Privacidade e publicação

O áudio é transcrito localmente. Para sugestões semânticas, o aplicativo envia a transcrição com tempos ao provedor escolhido. Com a validação visual habilitada, também envia até o limite de frames reduzidos configurado; nunca envia o vídeo completo. Modelos e pacotes de tradução são baixados para uso local. O upload do YouTube é opcional e exige OAuth e aprovação explícita; os vídeos são enviados como privados. Veja [como conectar o YouTube](connect-youtube.md) e a [referência de configuração local](../reference/configuration.md).
