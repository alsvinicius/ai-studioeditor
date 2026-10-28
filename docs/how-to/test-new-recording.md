# Verificar Nova gravação com Playwright

Este teste cobre REQ-006, BDD-JRN-003-06 e TASK-019: abrir o painel visível por clique real, cancelar sem criar projetos, ativar a ação da galeria vazia pelo teclado e importar um vídeo até a configuração da análise. Verifica também o campo nativo, erros recuperáveis e retorno do foco.

Com a aplicação iniciada e pelo menos um projeto existente, instale as dependências de teste e execute:

```sh
npm ci
npx playwright install chromium
npm run test:e2e
```

O endereço padrão é `http://localhost:30100`. Para outra porta ou outro vídeo:

```sh
PLAYWRIGHT_BASE_URL=http://localhost:8000 OBS_TEST_VIDEO=/caminho/gravação.mp4 npm run test:e2e
```

Para usar o Google Chrome instalado com janela visível, execute:

```sh
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e -- --headed
```

O vídeo padrão é `~/Videos/OBS/teste.mp4`. A importação usa o backend real e deixa um projeto chamado **Playwright - Nova gravacao** na galeria. Confirma idioma PT-BR, qualidade, botão de análise, limpeza do input e nova abertura do painel após importar. A análise com IA depende de uma ação posterior.

Os cenários de abertura/cancelamento rodam em desktop e viewport mobile. O upload real roda uma vez, em desktop. A listagem da biblioteca vazia e a resposta de falha de upload são simuladas nos respectivos testes; a importação bem-sucedida usa o backend real. Nenhum projeto existente é apagado.

As asserções confirmam que o diálogo fica visível mesmo com `HTMLInputElement.click()` programático bloqueado. Um teste separado espera `page.waitForEvent('filechooser')` ao clicar diretamente no input visível. A abertura do painel e a importação concluída geram screenshots em `test-results/`; falhas também guardam trace. Inspecionar somente o alvo do clique não comprova a resposta visual.
