# Revisão da interface instrument-design

- Data: 2026-10-17.
- Fontes: REQ-006/008, JRN-001/003/004, BDD-JRN-003-04, DEC-021, TASK-017.
- Aplicação: `http://localhost:30100/`, assets `20261017-audit-3`.

## Correções

A folha material passou a usar construções compartilhadas com valores de tema. Foram removidas cores Graphite fixas de visores, campos, métricas, opções de tradução e progresso. A tinta acompanha a superfície, incluindo placeholders e texto secundário. Isso corrige o aviso OAuth ilegível no Chalk e texto escuro sobre poços verdes no Workshop.

Teclas neutras são padrão; apenas ações principais de cada grupo usam sinal. As abas têm relevo próprio, seleção pressionada e quebra de linha, sem a antiga barra horizontal. Painéis de aba recebem foco. Rótulos de confiança/tempo ficaram com pelo menos 12 px; links de configuração e controles recebem alvos maiores. A busca preserva foco/cursor durante sua renderização; abrir Configurações diretamente também carrega a biblioteca lateral. O texto de legendas nas configurações reflete o idioma original e traduções selecionadas.

## Cobertura no navegador

MCP Playwright verificou 72 combinações: nove estados reais e três fixtures visuais, multiplicados por Graphite/Chalk/Workshop e larguras de 1440/360 px, com altura 1000 px.

| Área | Estados |
| --- | --- |
| Configurações | conexão ausente, ação desativada, visores/campos e seletor de tema |
| Galeria | biblioteca com 12 projetos, filtros/paginação |
| Revisão | Edição, Cortes verticais, YouTube horizontal, Imagem, Legendas |
| Publicação | ativos existentes, campos de metadados, ação desativada sem OAuth |
| Importado | escolha de idioma/modelo e opção multimodal |
| Fixtures somente no DOM | validação visual em andamento, sugestões em andamento, erro recuperável |

As fixtures identificavam o estado como demonstração local e não executaram análise nem persistiram alterações. Os projetos reais foram lidos pela API, sem salvar revisão ou exportar.

Estilos computados foram usados para verificar texto contra seu fundo efetivo, incluindo endpoints dos gradientes e composição de transparências. As 72 combinações passaram: menor contraste de texto observado 4,58:1; nenhum texto informativo visível abaixo de 12 px; nenhum botão/link/campo medido abaixo de 24 px; nenhum overflow horizontal de página. Checkboxes são avaliados pelo rótulo clicável, e a maioria das ações tem 44 px. Controles nativos do vídeo não entram no inventário de CSS da aplicação.

Capturas em `.playwright-mcp/audit-{settings,gallery,captions}-{theme}.png` e variantes móveis da aba Legendas permitiram revisar hierarquia, materiais e leitura dos três temas. Evidências são locais de trabalho e não assets da aplicação.

As bordas essenciais dos campos e o foco foram conferidos separadamente contra as superfícies que os cercam. Menores razões nos fundos body/panel (e key para foco):

| Tema | Borda do campo / fundo externo | Foco / fundo |
| --- | ---: | ---: |
| Graphite | 3,23:1 | 5,76:1 |
| Chalk | 3,06:1 | 5,07:1 |
| Workshop | 3,02:1 | 5,00:1 |

## Interação e limites

A seleção dos três temas permaneceu após reload e em navegações; Configurações carregou os 12 projetos. A busca por `teste` mostrou oito cartões e manteve foco/cursor; a consulta sem resultados mostrou o estado vazio e preservou o foco. Os eventos DOM End/ArrowRight/ArrowLeft/Home selecionaram a aba correta com wraparound, foco correspondente, um único tab stop e painel com `tabindex=0`. A emulação de movimento reduzido retornou duração de animação de `0.00001s`. O console retornou zero erros e avisos. Os handlers de teclado também são exercitados por eventos DOM; eventos de teclado nativos do MCP não chegaram à página nesta sessão, portanto não se declara uma auditoria completa de teclado físico ou leitor de tela. O contraste automatizado de texto não substitui a inspeção de bordas/indicadores essenciais nem certificação WCAG. Não foram executados upload, transcrição, tradução ou análise IA nesta auditoria.

## Melhoria reutilizável da skill

A skill instalada em `[caminho local redigido]` ganhou `references/application-review.md`, uma rota no `SKILL.md` e o cenário 12 em `evals/evals.json`. O guia cobre cascata host, tinta por superfície, hierarquia de ações, estados reais e fixtures, foco, reflow e limites das evidências. O JSON e os links novos foram verificados; não foi executado benchmark A/B da skill.

A consolidação posterior acrescentou as regras também ao corpo principal da skill para orientar novas implementações, ao contrato de tokens e aos guias de busca/abas. Inclui foco/cursor durante atualizações, inicialização por rota direta, resumos de configuração atualizados e prevenção de bordas duplas. As instruções sobre composição de texto por IME são preventivas; esse cenário não foi validado na aplicação nesta sessão.
