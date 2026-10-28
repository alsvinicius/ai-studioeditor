# Linguagem visual do estúdio

O estúdio usa a linguagem material `instrument-design`, com três temas selecionáveis em **Configurações → Aparência do estúdio**. A escolha é salva no navegador atual e se aplica à galeria, aos projetos e às configurações.

- **Graphite** combina corpo carvão, painéis em cinza escalonado e sinal âmbar para trabalho em baixa luz.
- **Chalk** usa papel mineral quente, tinta escura e sinal vermelhão para leitura clara.
- **Workshop** combina corpo de papel quente, áreas de trabalho e leitura em verde pinho, com um pequeno sinal laranja.

Os três temas compartilham a mesma hierarquia e resposta física: superfícies foscas, módulos elevados e áreas informativas rebaixadas. A intenção é distinguir navegação, ações, leitura e áreas de trabalho durante sessões longas de edição.

## Como ler as superfícies

- O cabeçalho superior fosco sustenta a navegação global e mantém os mesmos links e posição em todas as telas; sua cor varia pelo tema escolhido. **Nova gravação** fica acessível na galeria e nos projetos; cancelar o seletor preserva a tela atual. A ação abre um painel de importação visível com campo de arquivo e arrastar e soltar; sua abertura independe de acionar um seletor oculto. Erros ficam dentro do painel, e Fechar/Escape devolvem o foco à ação de origem. A galeria reúne os projetos.
- Painéis têm borda definida, realce superior e sombra curta de contato. Eles agrupam tarefas que pertencem juntas.
- Campos, prévias e áreas densas de revisão ficam visualmente rebaixados, como áreas de trabalho; vídeos mantêm a aparência da própria mídia. Cada poço/visor tem tinta própria para texto e metadados: no verde escuro do Workshop a tinta fica clara.
- Controles de ação são teclas elevadas. O botão principal de cada grupo recebe a cor de sinal; navegação e ações secundárias usam teclas neutras. Abas selecionadas têm face pressionada e estado acessível explícito. Hover, pressão, foco, indisponibilidade e carregamento têm sinais próprios.

## Cor e hierarquia

O sinal do tema escolhido destaca ações principais e a etapa ativa. Estados de sucesso, erro e aviso mantêm cores e texto explícitos; nenhuma informação depende só da cor. Workshop usa o verde pinho também em superfícies de trabalho, sem confundi-lo com o estado de sucesso. Rótulos informativos e metadados mantêm tamanho legível, e valores temporais usam números tabulares para facilitar comparação.

## Responsividade e acessibilidade

O menu permanece no topo em galeria, configurações e projetos. No celular, seus elementos quebram em linhas no próprio cabeçalho. Em telas largas, prévia e revisão podem ocupar áreas paralelas. No editor, o vídeo começa na opção compacta; o seletor permite ampliar a coluna ou escolher o equilíbrio, e recolher a prévia libera toda a largura para revisão. A opção fica salva neste navegador. Em telas estreitas, as áreas se empilham e o seletor limita a altura do vídeo; filtros e abas refluem para manter os destinos visíveis. A ordem do teclado segue a leitura visual; o foco recebe contorno visível. Animações respeitam `prefers-reduced-motion`.

## Limites

A direção visual não muda o comportamento de processamento nem aplica estilo ao vídeo exportado. O acabamento usa CSS e pode variar levemente entre navegadores; contraste e legibilidade do conteúdo permanecem prioritários sobre efeitos de relevo.
