# Orientações do projeto

- Leia [workflow state](docs/product/workflow-state.md), PRD, jornadas, definição técnica e plano de implementação. Antes de mudar comportamento, siga os IDs de requisito/jornada/decisão da tarefa.
- Aplicação FastAPI em `app/`; interface estática em `app/static/`; testes Python em `tests/` e Playwright em `tests/e2e/`.
- Requisitos e comandos: Python 3.12+, `uv`, FFmpeg/ffprobe; `make start`/`make stop` para Compose. Validação disponível: `uv run --extra test python -m unittest discover -s tests`, `node --check app/static/app.js`; E2E conforme `playwright.config.cjs`.
- Dados pessoais, vídeos, exports, credenciais e modelos devem permanecer em `data/`, `models/` ou caminhos locais configurados; nunca incluir conteúdo real em exemplos, fixtures ou commits. Use dados sintéticos nos testes.
- Atualize os artefatos de produto e documentação Diátaxis afetados. Não declare integração externa validada sem evidência.
