# Product workflow state

- Product / repository: OBS Post Production / `[caminho local redigido]`
- Updated: 2026-10-27
- Revision: 49
- Revision history: [central log](../revision-history.md#docsproductworkflow-statemd)
- Language used by the user for this workflow: Portuguese
- Current step: `/mvp` — implementação incremental autorizada de TASK-022–035; pipeline integral anterior concluído em clone.
- Requested scope: reduzir falsos positivos, detectar silêncio, gerar cortes horizontais, avaliar cor por cena, selecionar Codex `gpt-6-luna`/`medium`, personalizar frames e mostrar sinais de falha/baixa cobertura com clareza.
- Current activity: TASK-035 implementada, implantada e validada. Três execuções focadas e uma reanálise semântica integral com Codex GPT-6 Luna no clone concluíram; a revisão audiovisual humana de TASK-030 continua pendente.
- Last completed action: uma remoção pendente cobre 147,28–156,04 s, mostra tentativa/comentário e frase inteira mantida; 66 testes Python e 12 testes Playwright passaram.
- Next action: revisar manualmente a transcrição, cortes e qualidade audiovisual no clone de TASK-030; comparar preview/export antes de fechar qualidade geral.
- Recommended next workflow step: TASK-030, com corpus/clones e revisão humana; não fechar qualidade geral com base nos testes sintéticos ou numa gravação.
- MVP implementation progress: progresso anterior preservado no plano principal e histórico; este plano não conclui nem reabre tarefas antigas. Piloto OAuth permanece separado.

## Interview checkpoint

- Completed topics: local processing; conservative edits; browser review; PT-BR to EN; vertical cut suggestions; private upload after review; end-to-end success criterion. See PRD and DEC-002/003.
- Pending questions: OAuth client setup for live upload. The initial PT-BR/EN caption attachment decision was expanded on 2026-10-17 to multiple selected languages; the broader OAuth scope remains accepted.
- Checkpoint saved: 2026-10-26, America/Sao_Paulo; implementação parcial executada, suíte sintética validada.
- Interrupted or pending writes: none.

## Artifacts

| Artifact | Actual path | Revision | Status | Source revisions | Blockers |
|---|---|---|---|---|---|
| Brownfield assessment | not applicable (greenfield) | n/a | not applicable | empty repository inspection | none |
| PRD | [docs/product/prd.md](prd.md) | 36 | draft | REQ-002 com critério explícito para retake completo | piloto OAuth anterior; qualidade humana parcial |
| Journeys | [docs/product/user-journeys.md](user-journeys.md) | 36 | draft | PRD revision 36; BDD-001-31 | qualidade humana pendente |
| Technical definition | [docs/engineering/technical-definition.md](../engineering/technical-definition.md) | 44 | draft | PRD/Journeys revision 36; DEC-034 | validação com modelo e revisão humana pendentes |
| Implementation plan | [docs/planning/implementation-plan.md](../planning/implementation-plan.md) | 49 | draft | PRD/Journeys 36; Technical 44 | TASK-030 requer avaliação humana |
| Quality audit | [diagnóstico](../engineering/analysis-quality-audit.md) | 2 | diagnóstico + medição local somente leitura | API/código/áudio/frames em 2026-10-26 | anotação/audição integral não executada |
| Quality plan | [plano de qualidade](../planning/analysis-quality-plan.md) | 11 | TASK-035 concluída; TASK-030 segue parcial | PRD/Journeys 36; Technical 44; diagnóstico 2 | revisão editorial/audiovisual humana |
| MVP implementation | root app | deploy local nesta sessão | partial | TASK-022–035 | avaliação editorial/audiovisual humana de TASK-030 |

## Confirmed decisions and sources

- Solicitação UI/UX: navegação global, uso equilibrado do espaço, hierarquia de informação e configuração YouTube em página global. REQ-007, JRN-003, DEC-010 e TASK-008 registram os contratos; a revisão preserva decisões entre abas e visitas à configuração. O pedido mais recente acrescenta uma linha do tempo de análise especificada em REQ-006, JRN-001/BDD-JRN-001-13 e DEC-019. Nenhum modelo foi executado nesta mudança.

- Local processing, PT-BR source, conservative editing, browser review, vertical cut suggestions, private YouTube upload after approval, and end-to-end success criterion: user messages 2026-10-14. Medium Whisper with beam size 5 is default; model choice is per project up to `large-v3`.
- Creator can choose transcription quality per project from `tiny`, `base`, `small`, `medium`, and `large-v3`; `medium` is the default and the chosen model is stored with the project.
- User corrected the exact provider/model to OpenCode `opencode/mimo-v2.6-flash-free`. Both transcript semantics and optional frame review use that fixed ID; host authentication is mounted read-only. Transcript text always leaves the device for semantic analysis; image frames leave only when the per-run toggle is on. Full video is never sent; Codex is not invoked and suggestions require human review.
- Confirmed, 2026-10-15: spoken editorial comments about this recording can guide semantic suggestions when their intent and interval are locatable; relative times use media duration; transcript text is untrusted data and cannot change model instructions or output format.
- The latest 2026-10-17 correction restores OpenCode but fixes its model ID to `opencode/mimo-v2.6-flash-free`; see DEC-018.
- Confirmed, 2026-10-15: the Gravações view is a full-width gallery with name search, status filter, and 12/24/48 pagination; projects can be renamed from gallery cards or the editor without changing source media.
- Confirmed, 2026-10-17: caption translation accepts multiple selected destinations after transcript correction. The initial broad-reach list is English, Spanish, French, German, Hindi, Arabic, Indonesian, Japanese, Russian and Turkish; the source track is always retained. Platform references do not support a comparable numerical top-ten ranking, so list is curated, not statistically ordered. See REQ-002/004/005, BDD-JRN-001-16 and DEC-022.
- Live validation: the rebuilt container reports OpenCode authenticated; the `teste.mp4` project reached `review-ready`, its semantic model result is complete for `opencode/mimo-v2.6-flash-free`, and seven reduced frames were classified as presentation-dominant with high confidence. Global grade is correctly blocked with `preserve`.
- Host is Ubuntu Linux; Intel Iris Xe; the system Docker daemon is running for this pilot. Host FFmpeg is absent; the container image provides FFmpeg.
- Implementation: Compose rebuilt and started locally. On an isolated clone of `[caminho local redigido]`, small vs medium comparison corrected repeated “Tolkien” to “token” in context and improved other terms, but names still need review. Review API accepted the rounded ending interval. The isolated export produced a 118.44-second master and two 1080×1920 cuts (45 and 43.44 seconds) with captions mapped to the retained timeline; the clone and its outputs were removed. The original project was reanalyzed with medium (11 PT-BR/EN segments, 2 edits, 2 non-overlapping vertical suggestions), both previously selected edits were accepted, and the 118.44-second master plus PT-BR/EN SRT/VTT were exported. The source remains unchanged.

## Assumptions and thread dispositions

- Single local creator and one YouTube channel at a time: assumption in PRD/technical definition.
- Public/scheduled YouTube release: excluded from MVP by confirmed private visibility selection.
- OAuth client setup: external prerequisite; no credential is stored in repository.
- Automatic YouTube caption tracks: confirmed; code requests `youtube.upload` and `youtube.force-ssl`, and uploads the source SRT plus generated destination tracks for selected videos. Live OAuth/API behavior is unverified; the user must configure a client and authorize the expanded scopes. The final image was rebuilt with the PyAV pin and persistent local PT→EN package; an isolated re-run confirmed 12 PT and 12 EN segments.
- OpenCode runtime: model ID is fixed to `opencode/mimo-v2.6-flash-free`; host auth file is mounted read-only and not returned. Transcription/translation stay local. Text is always sent when analysis runs; images are controlled by the toggle (on by default). CLI failures preserve local heuristic suggestions.

## Deferred technical preferences

- None; implementation uses reversible stack choices proposed in technical definition.

## Pending downstream updates

| Source change | Affected artifact / IDs | Reason | Required action or decision |
|---|---|---|---|
| Caption workflow end-to-end | REQ-002, REQ-004/005/006; JRN-001; BDD-JRN-001-14; DEC-020; TASK-002 | Medium Whisper + OpenCode MiMo, edited transcript preserved timestamps, local English translation, SRT/VTT export passed on project [id de projeto local] | Confirmed after the rebuild; inspect project in browser |
| Analysis terminal-state synchronization | REQ-006; JRN-001; BDD-JRN-001-13; DEC-019; TASK-008 | API reported `review-ready` while browser retained `analyzing`; no-cache polling, same-project refresh, retry on temporary failures, and new asset versions deployed | Reload project `[id de projeto local]` and confirm visually |
| E2E frontend review/export | REQ-001/002/004/006/010; JRN-001; BDD-JRN-001-15; DEC-013/019; TASK-002/004/008/011 | Missing `youtubeCutsHtml()` caused route render failure; function and route error scope fixed. Playwright imported, analyzed with local fallback after OpenCode timeout, edited, translated, saved, exported and confirmed 10 assets | Clone remains available at `[id de projeto local]`; inspect in browser |
| Ten-language caption translation | REQ-002/004/005/006; JRN-001; BDD-JRN-001-14/16; DEC-020/022; TASK-015 | Ten individual translations and one multi-language API job passed; source segment IDs/timestamps persisted, invalid code rejected, disposable data removed. Export/YouTube integration was not exercised | If release evidence needs it, exercise SRT/VTT export with selected languages; live upload waits on OAuth setup |
| User review pending | REQ-002–006, JRN-001, TASK-003/004 | PT-BR still has residual technical-term/name errors; vertical candidates remain pending | Review transcript and vertical suggestions; accept/reject shorts before their export |
| YouTube OAuth client not configured | REQ-005, JRN-002, TASK-005 | Live upload requires user OAuth setup | Implemented integration; live pilot waits for OAuth client and account authorization |
| Creator review of OpenCode validation project | REQ-009/011, JRN-005, DEC-018, TASK-010/012 | Full test flow passed; human inspection of suggestions/preview remains | Review project `[id de projeto local]` at localhost:30100 |

## Recommended next step

Revisar o [plano de qualidade](../planning/analysis-quality-plan.md) e, ao solicitar implementação, iniciar TASK-022. Nenhum modelo externo ou reanálise do projeto original foi executado nesta sessão. O diagnóstico mediu a cauda abaixo de −35 dB a partir de 982,524479 s; a anotação editorial/visual humana integra a primeira tarefa.

## Reconciliação da extensão

REQ-002/003/010/011 receberam complementos propostos e REQ-012 foi adicionado. JRN-001 ganhou BDD-JRN-001-17–25; DEC-024–031 e TASK-022–033 definem a execução. Mecanismos anteriores permanecem documentados como implementados, com substituições futuras explícitas. Mapa Diátaxis preservado; guias atualizados para grades com timestamp e limite configurável. Revisões antigas na tabela deste estado estavam defasadas; foram alinhadas às revisões reais antes desta atualização.


- Transcript workflow decision (2026-10-17): choose source language at analysis (PT-BR default), edit/save recognized text without changing timestamps, then generate only selected local translations. DEC-020.

- Visual direction (2026-10-17): user explicitly requested the `instrument-design` language across the entire system and later requested light and Workshop themes; DEC-021/TASK-016 record Graphite, Chalk and Workshop plus shared accessibility/material constraints. Browser validation passed; see TASK-016.

- Visual audit (2026-10-17): TASK-017 corrects existing REQ-006/008 compliance without expanding product scope. Skill improvement is user-authorized; benchmark A/B was not run. Evidence and keyboard-tool limits are recorded in the engineering review.

- Navigation correction (2026-10-17): always use the same top menu for gallery, settings and project routes, including direct entry/reload and mobile reflow. REQ-006, BDD-JRN-003-05, DEC-010, TASK-018.
- Import action correction (2026-10-17): call the native picker from a user gesture, fall back when needed, and serve cache-busted assets after rebuild. REQ-006, BDD-JRN-003-06, DEC-010, TASK-019.

## Configuração Codex solicitada em 2026-10-26

O usuário acrescentou seleção global entre OpenCode/MiMo e Codex `gpt-6-luna` com esforço `medium`. REQ-009, DEC-029, TASK-031/032 e BDD-JRN-005-01–03 foram implementados parcialmente. Testes sintéticos cobrem contrato/isolamento; build e presença de autenticação no container foram conferidos, geração real não executada. O plano de qualidade está na revisão 3.


## Registro de execução — 2026-10-26

- Estado: 26 testes sintéticos e 4 execuções Playwright desktop/mobile passam; compilação Python e verificação de sintaxe JS passam. Build/imagem e reinício do serviço local realizados.
- Proteções: projeto original e respectivos resultados não foram modificados; sem chamada real a Codex; nenhum upload/publicação.
- Pendências: geração Codex real; análise de clone com anotação humana; classificação visual real; comparação de preview/export e relatório TASK-030. O original só foi lido por FFmpeg e não foi modificado.

## Registro de execução — 2026-10-27

- TASK-030: reanálise integral do clone `[id de projeto local]` com `large-v3`, Codex `gpt-6-luna` Medium, 128 frames. Visual 128/128, Whisper 462 segmentos, 11 pausas medidas e semântica completa; 5 verticais e 9 horizontais aguardam aprovação humana. Fonte e decisões do projeto original permaneceram intactas.
- O caso “Cloud” (501,14–503,04 s) foi sinalizado por alinhamento ASR suspeito e não gerou remoção semântica. Cauda silenciosa de 4,22 s detectada. Execução e limites: [relatório](../engineering/analysis-reliability-validation.md).
- TASK-034: UI agrega faixas de segmentação Whisper curta e cobertura de slides/unknown; não inventa cobertura nem exibe centenas de cartões. 56 testes Python e 14 casos Playwright passam.
- Próximo: revisão humana dos cortes/transcrição e checagem de preview/export; nenhuma publicação ou upload foi feito.
