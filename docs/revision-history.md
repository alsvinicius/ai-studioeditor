# Revision history

## `docs/product/prd.md`

- Revision 36: exige que retake sugerido cubra tentativa e comentário e mostre retomada mantida.
- Revision 35: especifica avisos resumidos para transcrição ASR fragmentada e cobertura visual incerta.

- Revision 34: adiciona tratamento defensivo de evidências e alertas.

- Revision 33: adiciona alerta e proteção para transcrição com alinhamento inconsistente.

- Revision 32: inclui sugestão revisável para comentário editorial associado a retake.

- Revision 31: configura 2–1024 frames de análise visual e compõe até 128 frames rotulados por imagem, no máximo oito grades por chamada.
- Revision 30: tornou configurável entre 2 e 32 o limite de frames visuais por execução, padrão 8, conforme pedido do usuário.

## `docs/product/user-journeys.md`

- Revision 36: adiciona BDD-JRN-001-31 para remoção completa de retake.
- Revision 35: adiciona BDD-JRN-001-30 para resumo de ASR fragmentado e cobertura visual.

- Revision 34: adiciona BDD-JRN-001-28/29.

- Revision 33: adiciona BDD-JRN-001-27 para anomalia nos tempos de palavras.

- Revision 32: adiciona BDD-JRN-001-26 para comentário e retomada.

- Revision 31: atualiza BDD-JRN-001-25 para grades de até 128 frames com timestamp e limite total de 1024.
- Revision 30: adicionou BDD-JRN-001-25 para persistência, snapshot e limite selecionável de frames visuais.

## `docs/engineering/technical-definition.md`

- Revision 44: DEC-034 define resolução por evidências de palavras para tentativa, comentário e retomada.
- Revision 43: atualiza DEC-030 com execução real e inspeção humana pendente.
- Revision 42: registra execução real Codex e DEC-033 para faixa ASR e cobertura visual compacta.

- Revision 41: registra limites visuais, áudio medido, reinício e export.

- Revision 40: especifica detecção de colapso e filtro de remoção semântica.

- Revision 39: documenta alinhamento único das palavras para o comentário editorial.

- Revision 38: amplia o limite visual configurável para 1024 e especifica composição das pranchas e quota por chamada.
- Revision 37: DEC-031 permite selecionar o limite de frames entre 2 e 32 e define snapshot por execução.

## `docs/planning/implementation-plan.md`

- Revision 49: registra TASK-035, implementação do retake completo e estado da reanálise clone.
- Revision 48: atualiza evidência de render curto real e estado da TASK-030.
- Revision 47: documenta TASK-034 e execução integral da pipeline no clone com limitações humanas restantes.

- Revision 46: registra revisão defensiva e análise integral do clone.

- Revision 45: registra diagnóstico e proteção TASK-025.

- Revision 44: registra correção TASK-025 e sugestões atualizadas nos projetos.

- Revision 43: incorpora frames em grades de até 128 tiles com timestamps e até oito imagens por chamada.
- Revision 42: integrou a ampliação configurável da amostragem visual à execução incremental.

## `docs/product/workflow-state.md`

- Revision 49: registra TASK-035 concluída e mantém revisão audiovisual humana de TASK-030 como próximo passo.
- Revision 48: registra render curto verificado e revisão humana pendente.
- Revision 47: registra a execução completa do clone e o próximo passo de revisão humana.

- Revision 46: checkpoint de validação e revisão defensiva.

- Revision 45: checkpoint de ASR e proteção de remoções.

- Revision 44: registra checkpoint de comentário editorial.

- Revision 43: checkpoint da revisão de TASK-033 para limite 1024 e compositor de pranchas com timestamps.
- Revision 42: checkpoint TASK-033 concluída localmente; atualização da implementação e da documentação.

## `docs/planning/analysis-quality-plan.md`

- Revision 11: inclui TASK-035 e validação do retake anunciado pelo apresentador.
- Revision 10: registra render real curto, correção do estado de retry e evidência final da TASK-030.
- Revision 9: registra execução integral Codex, fragmentação ASR observada e TASK-034.

- Revision 8: registra execução integral e proteções adicionais.

- Revision 7: registra caso real e rechecagem local da janela suspeita.

- Revision 6: detalha alinhamento de comentário editorial em TASK-025.

- Revision 5: atualiza TASK-033 para amostrar até 1024 frames e organizá-los em até oito pranchas por chamada, 128 tiles por prancha.
- Revision 4: TASK-033 registra seletor global de 2–32 frames, default 8, snapshot por projeto e efeito no volume enviado.

## `docs/product/prd.md`

- Revision 26: set compact preview as the initial default while preserving the creator’s saved choice.

- Revision 25: let the creator choose compact/balanced/wide video preview or collapse it, with persisted preference and responsive sizing.

- Revision 24: visible import dialog with native file field, drag/drop, recoverable errors and focus restoration; headed Google Chrome verification and screenshot evidence for TASK-019.

- Revision 23: specify that New recording opens the picker in the gallery/project and cancel preserves state.

- Revision 22: require consistent top navigation across all routes and narrow layouts.

- Revision 21: make Chalk, Graphite and Workshop selectable global themes under REQ-006.

- Revision 20: allow multiple selected caption translations from a broad-reach ten-language list; preserve the source track and describe local Argos direct/pivot translation.

- Revision 19: extend REQ-006 with the system-wide Graphite material language and accessible visual states.

- Revision 18: clarify rendering/error recovery and horizontal-cut review controls under REQ-006.

- Revision 17: support selectable source language, transcript correction before selected translations, and dynamic caption export/upload.

- Revision 16: require analysis progress to show completed, current, and pending stages without fabricated continuous percentages.

- Revision 15: correct the generative model to OpenCode ID `opencode/mimo-v2.6-flash-free`, with OpenCode host authentication for text and optional images.


- Revision 14: replace selectable OpenCode/Codex text analysis and optional MiMo image provider with fixed MiMo V2.6 Flash for both modalities and one global key.

- Revision 13: make MiMo validation default-on when configured, keep a per-analysis opt-out, and prioritize scene-transition frames.

- Revision 12: require slide/screen-aware grading protection and optional, per-analysis MiMo review of up to 8 reduced frames.

- Revision 11: require a local three-moment comparison of original, suggested grade, and vertical crop with adjustable preview controls.

- Revision 10: add REQ-011 for local visual analysis, reviewable vertical framing and conservative approved grading/quality checks.

- Revision 9: add REQ-010 for contextual, unbounded horizontal YouTube cuts with review, bilingual captions, and independent publishing.

- Revision 8: adicionar REQ-008 para galeria/pesquisa/filtros/paginação e renomeação; adicionar REQ-009 para escolha global exclusiva do provedor de IA.
- Revision 7: permitir que comentários falados com intenção editorial informem sugestões, com proteção contra instruções embutidas e tempos ambíguos; citação editorial literal pode estar fora do intervalo alvo.
- Revision 6: adicionar configuração global YouTube e critérios de hierarquia, responsividade e preservação de rascunhos (REQ-007).

- Revision 1: initial product requirements from the conversation on 2026-10-14.
- Revision 2: require automatic PT-BR/EN YouTube caption-track attachment after approval.
- Revision 3: require the quality-oriented PT-BR model default, tolerate rounded review intervals, and keep removed spans out of vertical candidates and exports.
- Revision 4: add per-analysis transcription quality selection up to `large-v3` and persist the chosen model per project.
- Revision 5: add transcript-only semantic edit and cut suggestions through backend-managed OpenCode and Codex CLIs, with human review and provider fallback.

## `docs/product/user-journeys.md`

- Revision 26: specify compact preview on first visit and retain later saved sizing/collapse choices.

- Revision 25: add BDD-JRN-003-07 for reclaiming review workspace by resizing/collapsing preview.

- Revision 24: visible import dialog with native file field, drag/drop, recoverable errors and focus restoration; headed Google Chrome verification and screenshot evidence for TASK-019.

- Revision 23: add BDD-JRN-003-06 for starting a recording and safely cancelling its picker.

- Revision 22: add BDD-JRN-003-05 for persistent top navigation through route changes, history and reload.

- Revision 21: add BDD-JRN-003-04 for choosing and retaining a theme across routes and reloads.

- Revision 20: add BDD-JRN-001-16 for multi-language translation, partial success retention, export, and YouTube tracks.

- Revision 19: add shared visual language, legibility, focus and control hierarchy criteria across main journeys.

- Revision 18: add an E2E import-to-export scenario and terminal-state transition after export.

- Revision 17: add source-language choice, transcript correction, explicit translation, and BDD-JRN-001-14.

- Revision 16: add BDD-JRN-001-13 for a backend-stage-driven analysis timeline and optional image-review visibility.

- Revision 15: replace MiMo API-key setup with OpenCode authentication and verify the fixed model for text and frames.


- Revision 14: replace provider selection with MiMo key setup and BDD coverage for text plus optional image calls.

- Revision 13: set configured MiMo review default-on with a per-analysis toggle and scene-aware sample selection.

- Revision 12: cover the optional MiMo frame opt-in and preserve slide colors during visual review.

- Revision 11: add three-moment source/grade/crop comparison to the visual review scenario.

- Revision 10: add local visual review and BDD-JRN-001-12 for crop tracking, grade approval and export QC.

- Revision 9: extend JRN-001 with contextual 16:9 cuts and BDD-JRN-001-11.

- Revision 8: adicionar JRN-004 para biblioteca/renomeação e JRN-005 para seleção exclusiva do provedor.
- Revision 7: explicitar detecção revisável de intenção editorial falada durante análise semântica.
- Revision 6: incluir configuração global JRN-003 e cenário de preservação de controles entre abas/configurações.

- Revision 1: initial user journeys from the conversation on 2026-10-14.
- Revision 2: include bilingual caption tracks and ambiguity recovery in private upload journey.
- Revision 3: cover millisecond-rounded interval saving and exclusion of removed spans from vertical video and captions.
- Revision 4: include model choice in the local analysis journey and add a BDD scenario for using the selected model.
- Revision 5: add provider progress, transcript-transfer disclosure, source/evidence review, and partial CLI failure scenarios.

## `docs/engineering/technical-definition.md`

- Revision 33: DEC-023 sets compact preview as the default when no browser preference exists.

- Revision 32: DEC-023 defines persistent preview sizing/collapse and narrow-screen height behavior.

- Revision 31: visible import dialog with native file field, drag/drop, recoverable errors and focus restoration; headed Google Chrome verification and screenshot evidence for TASK-019.

- Revision 30: document native picker activation and cancellation behavior in DEC-010.

- Revision 29: update DEC-010/011 to a shared top header and gallery-based project access.

- Revision 28: strengthen DEC-021 with shared constructions, per-surface ink and computed-cascade review; link TASK-017 audit evidence.

- Revision 27: record Playwright persistence/route checks and contrast measurements for all three global themes.

- Revision 26: extend DEC-021 from Graphite-only styling to persistent Chalk, Graphite and Workshop themes.

- Revision 25: record successful individual and multi-language Argos translation validation, pivot coverage, timestamps, and API rejection evidence in DEC-022.

- Revision 24: add DEC-022 for ten broad-reach caption destinations, multiple local translations, and English-pivot fallback.

- Revision 23: add DEC-021 for the global instrument-design Graphite system and responsive/accessibility contracts.

- Revision 22: record Playwright evidence for terminal export state and the horizontal-cut renderer.

- Revision 21: align source-language/translations architecture and include DEC-020.

- Revision 20: DEC-020 separates editable source transcription from explicitly requested local translations.

- Revision 19: define the accessible analysis timeline contract and retain existing render/upload progress indicators.

- Revision 18: route text and frame inputs through OpenCode model `opencode/mimo-v2.6-flash-free`; mount auth read-only; record live text/image validation.


- Revision 17: define MiMo V2.6 Flash Chat Completions for text and frames, one key, and retire CLI orchestration.

- Revision 16: record default-on MiMo behavior and selective adoption of scene sampling from video-frames-skill (DEC-017).

- Revision 15: specify local screen heuristics, secure MiMo frame/key contract, fail-safe scene policy, and DEC-016.

- Revision 14: define the local visual-preview contact sheet endpoint and adjustable preview inputs.

- Revision 13: define local OpenCV analysis, crop trajectory and grade review contracts, render quality metadata, and DEC-015.

- Revision 12: atualizar o ID OpenCode/Muse para o alias listado no CLI instalado; registrar que falta resolver autenticação/provedor.

- Revision 11: add the horizontal cut schema, validation, review/export/upload contract, and DEC-013.

- Revision 10: atualizar DEC-009 para execução exclusiva; definir contratos DEC-011 da galeria e DEC-012 da configuração de IA.
- Revision 9: reconhecer intenção editorial falada sem tratar transcrição como comandos executáveis; validar a citação literal independentemente do intervalo alvo.
- Revision 8: registrar shell de estúdio e contratos seguros de configuração global em DEC-010.

- Revision 1: initial architecture proposal from environment inspection and the conversation on 2026-10-14.
- Revision 2: recorded implemented runtime choices and Intel Quick Sync fallback.
- Revision 3: confirmed automatic bilingual caption insertion and documented the required OAuth scope and per-track state.
- Revision 4: recorded local runtime findings, the PyAV compatibility pin, and the real OBS analysis evidence.
- Revision 5: specify medium/beam-5 transcription defaults and document interval clamping plus safe vertical-cut timeline mapping.
- Revision 6: define the per-project model selector, supported model allowlist, API request, and persistence contract.
- Revision 7: specify isolated transcript-only OpenCode/Codex CLI orchestration, validated merge/fallback behavior, auth mounts, and DEC-009.

## `docs/planning/implementation-plan.md`

- Revision 38: implement and verify compact preview as the first-visit default; existing saved preferences persist.

- Revision 37: implement and validate TASK-020 preview sizing/collapse in desktop and mobile; screenshots and reload persistence recorded.

- Revision 36: visible import dialog with native file field, drag/drop, recoverable errors and focus restoration; headed Google Chrome verification and screenshot evidence for TASK-019.

- Revision 35: replace the invisible picker overlay with real buttons; verify actual filechooser events, cancellation and real upload through reproducible Playwright tests.

- Revision 34: correct TASK-019 after tracing the click target to a CSS-clipped input; use direct native picker targeting.

- Revision 33: complete TASK-019 with a cache-busted picker update and server rebuild evidence.

- Revision 32: complete TASK-018 removing the route-dependent sidebar shell.

- Revision 31: complete TASK-017 instrument-design audit, corrections and installed skill improvements with bounded browser evidence.

- Revision 30: record TASK-016 as complete with browser, contrast and narrow viewport evidence, including final route-state visual inspection.

- Revision 29: add TASK-016 to implement and validate selectable Chalk/Graphite/Workshop themes.

- Revision 28: record ten-language individual and single-request API validation plus remaining export/upload evidence limits for TASK-015.

- Revision 27: add TASK-015 for multi-language captions and document pending runtime validation.

- Revision 26: add TASK-014 for the global instrument-design implementation and browser visual review.

- Revision 25: record Playwright E2E import, fallback analysis, caption translation, review, and export evidence; fix missing horizontal-cut renderer.

- Revision 24: add final browser evidence for the rendered captions tab after fixing the exported-project quality-check renderer.

- Revision 23: capture OBS end-to-end evidence for selected-language transcription, saved correction, local translation, and caption export.

- Revision 22: revise TASK-002 for source-language selection, correction, and selected translation workflow.

- Revision 21: record the analysis timeline implementation, accessibility behavior, documentation updates, and Chrome headless/runtime validation and recovery of an analysis interrupted by the required container rebuild.

- Revision 20: restore the exact OpenCode model requested; update implementation, test evidence, and runtime auth plan.


- Revision 19: replace TASK-010 CLI/provider work with one MiMo text/image model and record mocked contract evidence plus missing-key blocker.

- Revision 18: update TASK-012 for configured default-on MiMo review, opt-out, and scene-aware frames.

- Revision 17: expand TASK-012 for slide-safe grading, MiMo opt-in, API/render enforcement, and validation.

- Revision 16: extend TASK-012 with three-moment visual comparison and interactive preview validation.

- Revision 15: add TASK-012 for local framing analysis, approved conservative grading and post-render checks.

- Revision 14: alinhar o ID OpenCode/Muse ao modelo listado e registrar a falha auth/provedor observada na validação.

- Revision 13: add TASK-011 for contextual, unbounded horizontal YouTube cuts and their bilingual publication assets.

- Revision 12: adicionar favicon SVG alinhado à marca e validar seu serviço pela rota estática.
- Revision 11: adicionar TASK-009 para galeria/renomeação e TASK-010 para escolha e execução de um único CLI.
- Revision 10: atualizar TASK-007 com interpretação segura de pedidos editoriais falados, citações fora do intervalo alvo e referências relativas de tempo.
- Revision 9: corrigir o seletor de nova gravação após abrir projeto e validar os alvos Make/porta do Project Gallery.

- Revision 8: adicionar TASK-008 com evidências de testes de configuração e navegação responsiva.

- Revision 1: initial MVP plan from the conversation on 2026-10-14.
- Revision 2: recorded implementation checkpoint and runtime validation limits.
- Revision 3: added automatic caption upload to TASK-005 and recorded the supplied real recording for pilot validation.
- Revision 4: updated task evidence after the supplied video reached review-ready, fixed PyAV compatibility, and verified local model persistence on the rebuilt image.
- Revision 5: add validation of the rounded-duration failure, overlap-safe vertical export, and direct comparison of the small/medium transcripts on the OBS sample.
- Revision 6: add the transcription-quality selector and model-specific validation to TASK-002.
- Revision 7: add TASK-007 for OpenCode/Codex semantic suggestions, provider fallback, privacy disclosure, and sample-flow validation.

## `docs/product/workflow-state.md`

- Revision 38: checkpoint TASK-021 compact default, persisted-choice verification and screenshot evidence.

- Revision 37: checkpoint TASK-020 implementation, responsive browser evidence and screenshots.

- Revision 36: visible import dialog with native file field, drag/drop, recoverable errors and focus restoration; headed Google Chrome verification and screenshot evidence for TASK-019.

- Revision 35: record five passing browser checks and real OBS import evidence for TASK-019; supersede the earlier hit-test-only verification.

- Revision 34: checkpoint the CSS hit-target fix and rebuild evidence for TASK-019.

- Revision 33: checkpoint TASK-019 and refresh PRD, journey and technical source revisions.

- Revision 32: checkpoint consistent top navigation and reconciled source revisions.

- Revision 31: checkpoint TASK-017 completion, technical revision 28 and plan revision 31; retain OAuth pilot as next release work.

- Revision 30: close TASK-016 theme browser/contrast validation and restore YouTube OAuth pilot as the recommended next step.

- Revision 29: checkpoint selectable global themes and pending browser/contrast review.

- Revision 28: checkpoint 10/10 destination translation validation and remaining export/YouTube evidence boundary.

- Revision 27: checkpoint TASK-015 implementation and documentation; record app rebuild/runtime validation as the next action.

- Revision 26: checkpoint global instrument-design implementation and completed desktop/mobile MCP Playwright review.

- Revision 25: record `youtubeCutsHtml` fix, MCP Playwright E2E result, export artifacts, and OpenCode timeout fallback.

- Revision 24: fix stale analysis progress synchronization, redeploy on port 30100, and record terminal-state evidence.

- Revision 23: record completed end-to-end caption validation, final rebuild, and browser confirmation.

- Revision 22: record successful OBS caption workflow validation and the final UI helper fix pending rebuild.

- Revision 21: checkpoint transcript workflow implementation and pending OBS end-to-end validation.

- Revision 20: checkpoint the analysis timeline UI, CSS/JS cache bust, documentation reconciliation, Chrome headless review, and recovery state for the analysis interrupted by rebuilds; integrated browser unavailable.

- Revision 19: record the corrected OpenCode model, successful real text/frame requests, passing focused tests, and pending container/UI validation.


- Revision 18: checkpoint MiMo-only generative analysis, completed mocked tests, and live-key blocker.

- Revision 17: checkpoint default-on MiMo toggle and scene-aware frame selection evaluation/implementation.

- Revision 16: checkpoint screen-aware analysis, MiMo opt-in implementation, local test results, and pending container/sample validation.

- Revision 15: checkpoint the local contact-sheet implementation and successful JPEG response on the validation project; browser review remains pending.

- Revision 14: checkpoint TASK-012 local frame/render validation, review-route persistence, and remaining in-app verification.

- Revision 13: registrar alias de modelo Muse atualmente listado e validação OpenCode bloqueada por auth/provedor.

- Revision 12: checkpoint TASK-011 implementation and the outstanding static/runtime validation.

- Revision 11: registrar o favicon e a validação da interface atualizada.
- Revision 10: checkpoint de REQ-008/009, galeria, renomeação e exclusividade do provedor, com evidência de teste isolado.
- Revision 9: checkpoint da regra de intenção editorial falada para sugestões semânticas.
- Revision 8: checkpoint da interface modernizada e configuração global validada sem executar modelos.

- Revision 1: initialized workflow checkpoint on 2026-10-14.
- Revision 2: recorded implementation status, static checks, and open OAuth/caption decisions.
- Revision 3: captured user approval for bilingual caption upload and the pilot recording path.
- Revision 4: recorded analysis results, the PyAV fix, model persistence, and remaining human-review/export/OAuth steps.
- Revision 5: record the reproduced defects, implemented fixes, medium-model comparison, and export validation evidence/status.
- Revision 6: checkpoint implementation and validation of per-project transcription model selection.
- Revision 7: checkpoint the user-requested AI CLI feature, source artifacts, implementation changes, and pending runtime validation.


## Atualização de 2026-10-26 — qualidade da análise

- `docs/product/prd.md`, revisão 27: complementos propostos em REQ-002/003/010/011 e REQ-012; quatro objetivos do criador preservados.
- `docs/product/user-journeys.md`, revisão 27: fonte PRD 27 reconciliada e novos BDD-JRN-001-17–24.
- `docs/engineering/technical-definition.md`, revisão 34: DEC-024–028 propostas e fontes 27; substituições do comportamento anterior explícitas.
- `docs/planning/implementation-plan.md`, revisão 39: extensão canônica TASK-022–030 vinculada, fontes 27/27/34.
- `docs/product/workflow-state.md`, revisão 39: escopo voltou a planejamento solicitado; corrigidas revisões defasadas, próximo passo TASK-022 sem iniciar implementação.

## docs/engineering/analysis-quality-audit.md

- Revisão 2 (2026-10-26): medição local somente leitura confirma silêncio final de 2,905 s e limite do detector de transições; build/API/UI foram conferidos, sem chamada generativa.
- Revisão 1 (2026-10-26): API/código, cinco retakes locais, timeout semântico, erro visual, frames de câmera/slides e cauda final medida; limites e hipóteses separados.

## docs/planning/analysis-quality-plan.md

- Revisão 1 (2026-10-26): nove tarefas em duas fases com contratos, restrições, fontes, cenários, dependências, critérios de aceite e parada. Sem alteração do app ou execução externa de IA.

## `docs/engineering/analysis-reliability-validation.md`

- 2026-10-27: registra TASK-035, três passes focados, reanálise semântica em clone e limites da evidência editorial.

## `docs/diataxis/how-to-review.md`

- 2026-10-27: explica como conferir tentativa, comentário, retomada e avisos de retake inconclusivo.


## Atualização de 2026-10-26 — seleção de Codex

- `docs/product/prd.md`, revisão 28: REQ-009 permite OpenCode ou Codex `gpt-6-luna`/`medium`, com proveniência e sem fallback implícito.
- `docs/product/user-journeys.md`, revisão 28: JRN-005 ampliada e BDD-JRN-005-01–03; fonte PRD 28.
- `docs/engineering/technical-definition.md`, revisão 35: DEC-029 e substituição explícita da exclusividade anterior; fontes 28/28.
- `docs/planning/implementation-plan.md`, revisão 40: extensão agora TASK-022–032; fontes 28/28/35.
- `docs/product/workflow-state.md`, revisão 40: pedido de seleção Codex registrado, revisões reconciliadas.
- `docs/planning/analysis-quality-plan.md`, revisão 2: TASK-031/032, snapshot de executor/modelo/esforço, dependências e validação atualizadas; inspeção local e fontes oficiais, sem execução de modelo.


## Atualização de 2026-10-26 — execução TASK-022–032

- PRD revisão 29: implementação parcial dos complementos de análise e seletor de provedor.
- Jornadas revisão 29: critérios novos marcados como implementação parcial, testes sintéticos e validação real pendente.
- Definição técnica revisão 36: DEC-024–029 atualizadas para estado implementado/parcial; DEC-030 registra limite da validação audiovisual.
- Plano de implementação revisão 41 e plano de qualidade revisão 3: evidência, limites por tarefa e TASK-030 em aberto.
- Estado do workflow revisão 41: usuário autorizou a execução; trabalho passou para `/mvp`.
- Guias Diátaxis, README e `.env.example`: seleção OpenCode/Codex, autenticação e revisão por cena atualizadas.
