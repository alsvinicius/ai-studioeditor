# OBS Post Production

Aplicativo local para preparar gravações do OBS: transcrição, revisão de sugestões, cortes horizontais/verticais, legendas e upload aprovado ao YouTube como privado. A mídia é processada localmente; análises semânticas enviam transcrição ao provedor escolhido e, opcionalmente, até a quantidade configurada de frames reduzidos.

**Estado:** MVP em desenvolvimento. A revisão audiovisual humana e a validação de OAuth real ainda têm limites documentados.

## Começar

O [guia detalhado de instalação e execução local](docs/diataxis/how-to-run.md) explica os pré-requisitos, dependências, configuração dos provedores e os caminhos para executar no host ou com Docker Compose. Em resumo, a execução no host requer Python 3.12+, `uv` e FFmpeg/ffprobe; Compose requer Docker. Para Compose, use `make start` e `make stop`.

Os projetos, uploads, configurações e exports ficam em `data/` por padrão; configure outro caminho com `APP_DATA_DIR`. Modelos/cache ficam em `models/`. Esses diretórios são locais e ignorados pelo Git. Veja a [referência de configuração local](docs/diataxis/reference-configuration.md) para os diretórios e as variáveis. Os dados locais podem conter mídia, transcrições e credenciais: restrinja permissões e faça backups protegidos. Configure credenciais localmente conforme os guias de [execução](docs/diataxis/how-to-run.md) e [YouTube](docs/diataxis/how-to-connect-youtube.md).

## Documentação

[Índice](docs/README.md) | [guias de uso](docs/diataxis/README.md) | [arquitetura e decisões](docs/engineering/technical-definition.md) | [contribuir](CONTRIBUTING.md) | [licenças de terceiros](THIRD_PARTY_NOTICES.md)

## Licença

Este projeto está sob a licença [Apache-2.0](LICENSE). Verifique também termos de modelos, provedores e quaisquer materiais de terceiros antes de redistribuí-los.
