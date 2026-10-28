# Validação de confiabilidade da análise

- Estado: pipeline integral concluído em clone; validação automatizada de UI aprovada. Qualidade editorial geral e precisão não são declaradas sem revisão humana.
- Fontes: REQ-002/006/011/012; BDD-JRN-001-20/27/28/29/30/31; DEC-024/025/027/028/030/033/034; TASK-023/025/027/029/030/034/035.
- Projeto original: `[id de projeto local]`; clone final: `[id de projeto local]`. Fonte de 1.443,016667 s; Whisper large-v3, Codex GPT-6 Luna Medium, 128 frames; nenhum upload.
- O clone usa a mesma fonte. A análise e decisões do original foram preservadas: 3 remoções aceitas e 1 rejeitada antes do teste; nova execução não escreveu no projeto original.

## Regressão TASK-035 — retake anunciado pelo apresentador

O caso informado no projeto `[id de projeto local]` foi reproduzido em clone `[id de projeto local]`. O clone preservou a transcrição e executou a retomada semântica integral com Codex `gpt-6-luna` / `medium`; o projeto original não foi alterado.

A etapa semântica terminou `complete` e sugeriu uma remoção pendente de **147,28 a 156,04 s**. A evidência registra a tentativa “E isso daqui não se deve só ao propósito probabilístico.” (147,28–154,20), o comentário “Vou refazer isso.” (154,78–156,04) e a frase completa a manter “E isso não se deve apenas ao modelo probabilístico que é como um LLM funciona.” (156,58–163,20). O início do corte não atravessa a fala explicativa anterior; o fim não alcança a retomada. Três execuções focadas e uma reanálise semântica integral do clone foram conferidas; quando a resposta não trouxe referências utilizáveis, o resultado foi retido para revisão em vez de apresentar apenas o comentário como edição resolvida.

O passe focado também encontrou “Repetindo” em outra parte da aula. O modelo classificou essa ocorrência como não editorial; a versão atual não a apresenta como alerta. Segmentos com alinhamento suspeito são substituídos por marcadores sem seu texto e não servem de evidência. Se um corte proposto cruzar a lacuna, ele é bloqueado e o comando parcial não é exibido como retake resolvido.

A interface mostra tentativa, comentário e retomada em um mesmo cartão, com uma decisão pendente. Um teste Playwright contra o clone real conferiu os três textos, os limites e o início/fim visíveis. A suíte Python tem 66 testes aprovados; a validação Playwright mais recente teve 10 casos aprovados na suíte de revisão e mais 2 desktop/mobile para o clone real; quatro casos específicos de outros clones foram ignorados por falta de configuração.

Esta execução demonstra o caso conhecido e a apresentação da evidência. Não mede taxas gerais de falsos positivos/negativos; a aprovação do corte e a conferência auditiva continuam com a pessoa revisora.

## Resultado da execução com a versão atual

- **Visual:** 128/128 frames classificados em uma prancha. A revisão identificou slides com pequeno inset de webcam nas extremidades amostradas. 127 intervalos sem amostra segura somam cerca de 172 s (11,9%); continuam desconhecidos. Não houve intervalo classificado com segurança como câmera, então não foi sugerida correção de cor. A ausência de ajuste é consistente com a cobertura observada, não uma falha reportada como sucesso.
- **Whisper:** 462 segmentos, 4.143 palavras. Duas anomalias de alinhamento foram sinalizadas, incluindo 501,14–503,04 s, o trecho do relato sobre o modelo para cibersegurança. A citação falsa sobre “Cloud” não apareceu como remoção na nova saída. Isso é evidência para este vídeo/execução, não garantia contra outros falsos positivos.
- **Áudio:** 11 intervalos medidos localmente. O silêncio final foi detectado entre 1.438,766 e 1.442,987 s (4,22 s); a sugestão de corte começa em 1.438,87 s, após a última fala transcrita em 1.438,51 s, e termina no fim da mídia.
- **Codex:** capacidade semântica completa, sem erro de provedor. Uma remoção semântica foi sugerida para a fala de retake em 154,90–156,04 s. Foram gerados 5 cortes verticais e 9 horizontais para YouTube; candidatos permanecem pendentes para aprovação humana.
- A resposta da API registra o executor/modelo, 128 frames e estado por capacidade. Os quatro passos terminaram em `review-ready` e `analysis_run=complete`.

## Proteções e situações adicionais descobertas

Uma tentativa anterior em outro clone, ainda no container que antecedeu esta publicação, produziu 1.998 segmentos (3.675 palavras), incluindo 1.529 segmentos curtos distribuídos em 50 faixas. Uma nova execução da mesma fonte com a versão implantada produziu 462 segmentos (4.143 palavras) e não acionou fragmentação. Essa diferença demonstra variabilidade e justifica mostrar faixas suspeitas sem classificar automaticamente cada palavra como errada. A UI agora agrega essas faixas e preserva a opção de conferir o áudio.

A análise visual também gerava 255 cartões por subdividir cobertura em pequenos intervalos alternados de slides e lacunas desconhecidas. A interface agora resume duração de slides/tela e cobertura incerta e mostra ajustes somente em intervalos de câmera seguros. Lacunas não são extrapoladas para preencher o mapa.

Outras barreiras verificadas no código e testes: citações sem alinhamento ao intervalo não aprovam cortes; pausa não transcrita não vira silêncio sem medida FFmpeg; etapas incompletas ficam parciais, retries registram a geração mais recente e preservam escolhas; falhas de upload não são repetidas sem confirmação; export não aplica grade a cenas incertas nem perde fragmentos curtos em fronteiras.

A primeira reprodução no container anterior também expôs divergência de estado depois de um retry semântico: os novos cortes haviam sido gerados, mas `provider_result` ainda mostrava o erro da chamada anterior. Corrigi a persistência de geração/estado no retry e acrescentei regressão automatizada. O clone diagnóstico foi reconciliado com a resposta concluída; nenhuma decisão do usuário existia nele.

## Verificações e limites

- 56 testes unitários passam na versão atual; 14 cenários Playwright passaram em temas Graphite, Chalk e Workshop, incluindo estado parcial, fragmentação ASR e a cópia real do projeto visual.
- Um trecho real de 10 s foi renderizado em horizontal 1920×1080 e FFprobe confirmou 10,0 s; o arquivo temporário foi removido. O teste sintético de 2 s com fronteira de cena em 0,1 s também produziu 2,0 s após o ajuste (a implementação anterior produziu 1,9 s). Não foi exportado o vídeo completo nem inspecionados todos os frames/áudio por uma pessoa.
- A cobertura visual é amostrada, não contínua; 11,9% permanece desconhecida. Não há anotação de referência que permita calcular precisão/recall. As 9 unidades horizontais e 5 verticais requerem revisão de contexto e prévia. Os resultados deste vídeo não representam uma taxa geral do produto.
