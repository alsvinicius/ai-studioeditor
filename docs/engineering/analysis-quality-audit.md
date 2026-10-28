# Diagnóstico da qualidade da análise de 26/10/2026

- Status: diagnóstico verificado em código, API e amostras locais; hipóteses identificadas abaixo.
- Revisão: 2; data: 2026-10-26.
- Histórico: [log](../revision-history.md#docsengineeringanalysis-quality-auditmd).
- Origem: relato do criador e projeto `[id de projeto local]`, consultado em `http://127.0.0.1:30100/api/projects/[id de projeto local]`.
- Execução: [plano de qualidade, revisão 3](../planning/analysis-quality-plan.md). O código e o processo local foram atualizados; este diagnóstico separa evidência original de validação pendente.

## O que explica o resultado

| Sintoma | Evidência verificada | Consequência |
|---|---|---|
| Ausência de cortes YouTube | `ai_analysis.models.opencode.status=unavailable`, erro `TimeoutExpired`; `youtube_cuts=[]` | A chamada semântica única falhou. Não existe gerador horizontal local; o resultado vazio não demonstra ausência de bons temas. |
| Falsos positivos | Cinco `possible-retake`, todos `low`, vindos de `rules`; `SequenceMatcher >= 0.88` entre segmentos vizinhos | A regra mede semelhança lexical sem confirmar repetição no áudio nem intenção editorial. |
| Silêncio final ausente | Duração 985,45 s; último segmento termina em 982,82 s; regra exige diferença estritamente maior que 3 s | A diferença de 2,63 s é descartada antes de ouvir o áudio. |
| Cor ausente na abertura e no fim | `scene_review.status=unavailable`, erro `ValueError`; política global `preserve`; sugestão neutra | O fallback protege os slides bloqueando o vídeo inteiro. Não há decisão por intervalo. |
| Resultado aparentemente pronto | API `review-ready` apesar das duas falhas de IA | O estado terminal permite revisar o resultado local, mas não comprova conclusão das capacidades solicitadas. |

A causa específica do timeout e a origem do `ValueError` não foram preservadas em detalhe suficiente para identificá-las. Não há evidência para atribuir a falha a limite de contexto, rate limit ou defeito do provedor. Não houve nova chamada ao modelo nesta investigação.

## Repetição real e erro de transcrição estão misturados

Na transcrição, a frase “e fazer 100% do seu trabalho de engenharia de software” aparece nos segmentos 91,22–91,30 s, 91,30–91,80 s e 91,80–91,94 s. Outra repetição aparece em 151,58–151,62 s. Esses tempos são incompatíveis com a duração normal dessas frases e justificam marcar a transcrição para conferência. A hipótese de duplicação do ASR ainda exige ouvir/retranscrever o trecho; não se pode remover vídeo com base nela.

Em 677,82–681,82 s aparecem “o Python resolve outro problema”, “o C resolve outro problema” e “o R resolve outro problema”. O candidato 678,82–679,82 s sinaliza justamente essa comparação. É um exemplo concreto em que semelhança textual confunde uma enumeração didática com retake. A audição ainda deve integrar a anotação de referência.

O próprio `large-v3` foi usado nesta análise. Trocar apenas o tamanho do Whisper não resolve os validadores, os fallbacks nem a dependência dos cortes da chamada semântica.

## Silêncio medido no áudio

Foi executado no container existente, sem alterar o projeto:

```sh
ffmpeg -hide_banner -ss 970 -i '<fonte local>' -vn \
  -af silencedetect=noise=-35dB:d=0.3 -f null -
```

O filtro informou início relativo em 12,524479 s e fim em 15,429333 s: intervalo absoluto 982,524479–985,429333 s, duração 2,904854 s. A mídia termina em 985,45 s. Isso confirma áudio abaixo do limiar nesse intervalo; não constitui anotação humana da última sílaba. Há diferença entre esse início e o fim do segmento ASR em 982,82 s: a fronteira final deve combinar áudio e fala, com margem conservadora, e ser ouvida na validação.

O limiar −35 dB foi uma sonda diagnóstica, não um parâmetro de produto aprovado. Detecção de energia baixa não equivale a ausência de fala em todos os ambientes.

## Cenas e cor

Uma folha de contato local em 5, 35, 90, 490, 955 e 980 s foi inspecionada. Os dois primeiros e os dois últimos frames mostram câmera; os dois centrais mostram slides com webcam sobreposta. As amostras confirmam mistura de layouts, sem estabelecer fronteiras exatas de troca. A fonte informa `yuv420p(tv, bt709)`.

As métricas atuais usam medianas do vídeo: luma 0,687, saturação 0,088 e clipping de sombras/luzes 0,002. Essas medianas não descrevem exclusivamente a imagem da câmera e não justificam aumentar saturação na pele. Uma aparência fria ou iluminação desigual é uma hipótese visual; não foi medida uma referência neutra para prescrever balanço de branco. O plano exige medir cada trecho e permitir “nenhum ajuste necessário”.

## Problemas adicionais de arquitetura

- `app/ai_analysis.py`: uma única chamada pede remoções, shorts e horizontais; falhar nela elimina todas as sugestões semânticas. Campos horizontais ausentes viram `[]`; candidatos inválidos desaparecem sem contabilidade de rejeição.
- `_quote_in_transcript` aceita evidência em qualquer posição inclusive para remoções comuns, embora só a intenção editorial explícita devesse permitir citação externa ao alvo.
- `merge_youtube_cuts` exclui qualquer candidato que intercepte qualquer sugestão de remoção, inclusive pendente ou falsa. Assim, corrigir apenas o timeout pode continuar deixando a lista vazia.
- `app/media.py`: shorts locais são janelas de até 45 s ordenadas por densidade de palavras, sem garantia semântica de começo e conclusão.
- `app/mimo_vision.py`: transições concorrem pelos oito frames; quando há muitas trocas de slide, abertura/encerramento podem não entrar. Um timestamp igual à duração também pode não produzir frame.
- `app/main.py`: nova análise repõe transcrição, cortes, cores e traduções. Repetir apenas a etapa defeituosa demanda contrato de preservação e invalidação explícito.
- `app/visual.py`, preview e render: decisão de grade global; folha atual em 12%, 50%, 88%; isso não garante inspecionar câmera no começo/fim. Preview usa um caminho de processamento diferente do filtro `eq` do export; paridade precisa de teste.
- `app/opencode_runner.py`: timeout efetivo padrão de 240 s. A constante `AI_TIMEOUT_SECONDS=180` em `ai_analysis.py` não é usada na chamada. Aumentar esse valor isolado seria ineficaz.

## Fundamentos técnicos consultados

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): oferece timestamps por palavra e integração VAD. Isso viabiliza evidência melhor, sem garantir alinhamento perfeito.
- [FFmpeg — silencedetect](https://ffmpeg.org/ffmpeg-filters.html#silencedetect): mede intervalos abaixo de um limiar; [signalstats](https://ffmpeg.org/ffmpeg-filters.html#signalstats) oferece estatísticas por quadro; [eq](https://ffmpeg.org/ffmpeg-filters.html#eq) permite correções parametrizadas. A implementação deverá conferir os filtros disponíveis na imagem instalada.
- [PySceneDetect — detectores](https://www.scenedetect.com/docs/latest/api/detectors.html): mudanças de cena podem ser detectadas por conteúdo e limiar adaptativo; isso não classifica slides versus câmera. Priorizar FFmpeg/OpenCV já instalados; nova dependência só se um experimento local justificar.

## Medição pós-implementação — leitura somente

Em 2026-10-26, FFmpeg leu a fonte original sem salvar alterações. A detecção local encontrou silêncio em `982.524–985.429 s` (2,905 s), após o último fim de transcrição `982.82 s`. A regra nova gera somente um candidato pendente `982.92–985.45 s`, preservando o intervalo transcrito e uma margem; o criador ainda deve ouvir a prévia. A busca em todos os frames encontrou duas transições em leitura local. Um teste a 1 fps criou 13 limites falsos e levou tempo semelhante; essa alteração foi descartada. A busca full-rate original foi mantida; o mapa de layouts ainda precisa de verificação visual.

A aplicação foi reconstruída e reiniciada em `127.0.0.1:30100`; health/configuração confirmam os dois CLIs e arquivos de autenticação presentes. CLI Codex `0.164.0` e opções foram inspecionados sem gerar resposta de modelo. Não houve chamada real a Codex/OpenCode. A suíte sintética e Playwright cobrem contratos/UI, não qualidade de geração.

## Limites da investigação

Não foi feita audição integral, anotação humana de todos os retakes, delimitação visual manual dos layouts nem avaliação antes/depois de cor. Nenhuma nova análise foi gravada e a fonte permanece intacta. A autenticação foi detectada pela presença do arquivo, não validada por geração; não há evidência ainda sobre saídas reais, cortes horizontais completos ou taxa geral de falsos positivos.
