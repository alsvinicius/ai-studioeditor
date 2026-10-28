# Tutorial: primeira execução

Este tutorial inicia o estúdio em uma máquina nova e importa um arquivo que você tem autorização para processar.

1. Prepare os pré-requisitos seguindo [Como instalar e executar localmente](how-to-run.md). Este tutorial usa Docker Compose.
2. Na raiz do clone, execute `make start` e abra <http://127.0.0.1:8000>.
3. Importe um vídeo OBS MKV ou MP4.
4. Escolha a qualidade da transcrição e inicie a análise. Para sugestões semânticas, configure e autentique OpenCode ou Codex no host conforme [como executar](how-to-run.md).
5. Revise transcrição e sugestões; aceite somente alterações desejadas e exporte. Upload YouTube é opcional e requer OAuth conforme [o guia](how-to-connect-youtube.md).
6. Encerre com `make stop`. Dados locais permanecem em `data/` e os modelos em `models/`.

A primeira execução pode baixar modelos grandes. A análise semântica envia o texto da transcrição ao executor selecionado; frames reduzidos dependem da configuração visual. Veja [privacidade e execução](how-to-run.md).
