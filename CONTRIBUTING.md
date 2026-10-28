# Contribuindo

## Preparação

Requisitos: Python 3.12+, `uv`, FFmpeg e ffprobe. Para Compose, instale Docker. Clone o repositório, configure `.env` a partir de `.env.example` se usar provedores autenticados e inicie com `make start`; encerre com `make stop`. O serviço fica em loopback. Consulte [como executar](docs/diataxis/how-to-run.md) e [configuração do YouTube](docs/diataxis/how-to-connect-youtube.md).

## Mudanças

Leia o [plano de implementação](docs/planning/implementation-plan.md) e os requisitos, jornadas e decisões vinculados à tarefa. Mantenha mudanças focadas; atualize requisitos e documentação Diátaxis quando alterar comportamento, instalação ou interface. Pull requests/issues: o host remoto e o processo de revisão ainda não foram definidos; confirme com os mantenedores quando forem escolhidos.

## Validação

- `uv run --extra test python -m unittest discover -s tests`
- `node --check app/static/app.js`
- Para E2E, siga [o guia Playwright](docs/diataxis/how-to-test-new-recording.md).

Não declare integrações com YouTube, OpenCode ou Codex validadas sem execução autorizada e evidência reproduzível.

## Privacidade e segurança

Nunca versione mídia, transcrições, tokens OAuth, arquivos de autenticação, `.env`, dados em `data/` nem caches/modelos. Use dados sintéticos nos testes e redija identificadores e caminhos pessoais em documentação. Não envie arquivos reais para provedores externos sem consentimento explícito; a aplicação pode enviar texto e, se habilitado, frames reduzidos ao executor escolhido. Reporte vulnerabilidades em canal privado a ser definido pelos mantenedores; não publique segredos em issues.

## Licença

Contribuições serão distribuídas sob Apache-2.0, conforme `LICENSE`. Dependências e modelos mantêm suas próprias licenças; consulte `THIRD_PARTY_NOTICES.md` e os avisos das versões efetivamente resolvidas.
