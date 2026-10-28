# Instrument Design · revisão de 2026-10-19

Fontes: REQ-006 · REQ-008 · DEC-021 · TASK-017.

Corrigidos o rótulo informativo de 10 para 12 px e o token de raio indefinido na barra do editor. Preservadas as tintas específicas dos poços Workshop.

A direção distingue espaço editorial calmo e controles/readouts táteis. A skill
`instrument-design` contém a receita, os tokens e critérios de revisão. Paletas
são adaptações originais; não são paletas oficiais Teenage Engineering.

A renderização da galeria agora preserva foco e seleção do campo ativo também
quando a lista é atualizada. A verificação usa o campo atual do DOM, evitando
confundir um elemento substituído com perda real de foco.

## Verificação

A revisão de 2026-10-20 está em `instrument-review.json`, com capturas sanitizadas em `instrument-review/` e hashes das fontes. Foram recapturados nove casos da biblioteca e nove de Configurações: três temas em 1440, 390 e 320 px. Busca, foco/seleção e filtros têm os casos registrados no JSON. Nenhuma gravação ou publicação foi iniciada. Os limites de contraste estimado e de cobertura de teclado estão explícitos no relatório.
