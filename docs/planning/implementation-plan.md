# OBS Post Production — Implementation plan

- Status: draft
- Revision: 49
- Revision history: [central log](../revision-history.md#docsplanningimplementation-planmd)
- Updated: 2026-10-27
- Sources and revisions: [PRD revision 36](../product/prd.md), [journeys revision 36](../product/user-journeys.md), [technical definition revision 44](../engineering/technical-definition.md)
- Related artifacts: [workflow state](../product/workflow-state.md)
- Language: Portuguese

## MVP outcome and release boundary

The creator can take one OBS recording through local transcription/translation, MiMo V2.6 Flash Free analysis via OpenCode and optional frame analysis, review, export, and OAuth-authorized private YouTube upload with source-language and selected translation caption tracks. Included: REQ-001 through REQ-011; JRN-001 through JRN-005. The full source video is never sent to AI; the configured 2–1024 frames (default 8) are sent as contact sheets of at most 128 timestamp-labeled frames, with at most eight sheets per call when visual review is on; public publishing and direct upload to other social platforms are excluded.

## Deferred scope and prioritization rationale

- Public/scheduled publication: excluded to preserve the confirmed private review boundary.
- Direct Instagram/TikTok publishing: excluded; vertical exports are provided for manual posting.
- Editing-time reduction target: defer until a pilot establishes a baseline; success is completion of a real end-to-end recording.

## Phases

### Phase 1 — MVP

- Delivered value and included IDs: reviewed local edit, multilingual captions, slide-aware visual framing/color review, vertical and contextual horizontal suggestions, export, and selected private YouTube uploads; REQ-001–REQ-011, JRN-001–JRN-003.
- Dependencies: user-configured YouTube OAuth app for live upload; user review before export.
- Current implementation checkpoint: TASK-001 through TASK-006 are partially implemented. Compose build/start, medium-model comparison, rounded-interval review save, isolated master/two vertical exports, and TASK-012 local sample/render checks succeeded on supplied OBS MP4s. On the original project, both previously selected silence edits were accepted and the master exported at 118.44 seconds with source-language and selected-translation SRT/VTT; two non-overlapping vertical suggestions remain pending user review. The visual preview route returned a decodable 1440×1110 contact sheet on the imported validation project. Live YouTube OAuth/upload remains blocked on client setup.
- Acceleration: implementation attempts Intel Quick Sync for video encoding and falls back to CPU encoding; speech recognition currently runs on CPU.
- Validation finding: the saved ending interval rounded beyond ffprobe duration, cut exports bypassed accepted removals, and the `small` model produced evident PT-BR technical-term errors. TASK-002 through TASK-004 now include interval clamping, cut exclusion/caption mapping, quality-oriented model selection (`tiny` through `large-v3`), and a `medium` default. A cloned project verified export fixes; isolated routing validation confirmed `large-v3` persistence and adapter handoff without downloading it.
- User corrected the exact model ID to `opencode/mimo-v2.6-flash-free`. TASK-010 and TASK-012 use OpenCode for both semantic text and optional image frames; Codex remains unused, and OpenCode auth is mounted read-only into the backend. Local transcribe/translation remain unchanged.
- Exit / release criteria: complete one real OBS recording to reviewed exports and private YouTube upload; all BDD scenarios, including visual review and render QC, have implementation evidence; local setup and OAuth guides are accurate.

#### TASK-001 — Initialize app and local project storage
- Description: create the Python web app, project manifest/state, local data layout, container configuration, and root setup files.
- Sources: REQ-001, REQ-006, DEC-001, DEC-004
- Dependencies: none
- Subtasks: app shell; manifest lifecycle; path validation; container wiring.
- Agent inputs and constraints: use linked product docs; store media/tokens under ignored local data paths; bind loopback by default; do not overwrite source.
- Definition of Ready: product scope and local-only constraint confirmed.
- BDD scenarios: BDD-JRN-001-01, BDD-JRN-001-03
- Validation: image built and started; `/api/health` reported FFmpeg/ffprobe available; importing the 10.6 MB source produced a project manifest while the original remained unchanged.
- Stop condition: if storage/path policy needs external access or destructive source changes.
- Definition of Done: app starts from documented command, project persists, invalid paths fail safely, root setup docs updated.
- Evidence: the real source imported with duration 142.316667 seconds, H.264 video and AAC audio; status `imported`.
- Expected results: a user can create/open a local project.
- Affected documentation: README, how-to-run, technical definition, workflow state.

#### TASK-002 — Analyze media, review transcript, and generate selected captions
- Description: probe MKV/MP4, let the creator select a supported local transcription model per project, transcribe in the selected source language (PT-BR default), allow correction, then translate only into explicitly selected languages; persist model, language, timestamps, progress, and errors.
- Sources: REQ-001, REQ-002, JRN-001, BDD-JRN-001-06, DEC-008
- Dependencies: TASK-001
- Subtasks: FFmpeg probe; per-project model selector (`tiny`, `base`, `small`, `medium`, `large-v3`); local model adapter; timestamp-preserving transcript correction; post-review local translation for selected languages; SRT/VTT artifacts; resumable job states.
- Agent inputs and constraints: source media stays local; transcript-only semantic review is defined by TASK-007; keep model adapters replaceable; no unsupported accuracy claims.
- Definition of Ready: TASK-001 project model and media paths exist.
- BDD scenarios: BDD-JRN-001-01, BDD-JRN-001-03, BDD-JRN-001-06
- Validation: select commands from installed toolchain; exercise valid media, missing audio, malformed input, and interrupted processing; compare PT-BR output from `small` and `medium` on the supplied OBS source; verify UI options, per-project persistence, adapter handoff, and invalid-model rejection without downloading `large-v3` solely for the routing check; record runtime and representative term changes without claiming a universal accuracy rate.
- Stop condition: if local models cannot run on this host without adding a paid service or expanding privacy scope.
- Definition of Done: selected model/source language are persisted; source transcript can be corrected without changing timestamps; only explicitly selected translations are generated from saved corrected text; SRT/VTT export and upload use the source and selected languages; model loading/download progress and errors are actionable; source is unchanged; setup/model docs updated.
- End-to-end evidence (2026-10-17): rebuilt the service and imported `[caminho local redigido]` as `legenda-e2e-teste` (142.316667 s). Selected PT-BR and `medium`; analysis generated 11 source segments and completed the OpenCode MiMo semantic stage. Corrected the first segment from “a generativa” to “IA generativa” through the transcript API; its 21.1–31.1 s boundaries remained unchanged and no translation existed. Requested English only; 11 English segments were generated locally from the saved correction. Export produced a 142.293 s master and only PT-BR/EN SRT+VTT. SRT first cues shared matching IDs/times, and English reflected “AI”. Project remains visible at localhost:30100 for user inspection. YouTube upload was not attempted because OAuth is not configured. The post-export project rendered the new captions tab in Chrome without JavaScript exceptions; saved correction and translation controls are locked for exported projects, and filenames/track labels showed PT-BR plus English only.
- End-to-end MCP Playwright evidence (2026-10-17): imported the supplied OBS MP4 through the real frontend file input as project `[id de projeto local]`; selected PT-BR, `tiny`, and default-on visual review. Analysis reached review-ready and the timeline disappeared. OpenCode timed out at semantic analysis, recorded as unavailable, while local suggestions remained available. Corrected transcript in UI without changing 21.1–27.98 s boundaries, generated English from saved text, accepted one removal and one vertical cut, saved decisions, and exported. Output has a 121.543 s master, 45 s vertical MP4, and PT/EN SRT+VTT for master and short (10 files total); the English SRT reflects the corrected phrase. The UI transitioned to `Exportado`, displayed the publication tab and all assets, and locked transcript/translation controls. No JavaScript exceptions. YouTube upload was not attempted because OAuth is not configured.
- Evidence: initial `small` run reached `review-ready` with 12 PT-BR/EN segments but misheard repeated “token” as “Tolkien.” A `medium` run completed with 11 segments, corrected several terms (including “token” and “ChatGPT”), and still misheard a proper name (“bogeyman brain”). No generalized accuracy target is claimed. The PyAV 19 incompatibility remains fixed by pinning `av<19`.
- Model-selection evidence: the rendered UI includes all five installed model options, `medium` is preselected, and isolated API/worker validation saved and forwarded `large-v3` to the transcription adapter; malformed model values return HTTP 422. No large model download was initiated for this routing check.
- Expected results: review-ready source transcript and edit suggestions; selected translation artifacts are produced only after corrected text is saved.
- Affected documentation: how-to guides, technical definition, workflow state.

#### TASK-003 — Review edits and vertical cut suggestions
- Description: build local preview UI for transcript, conservative edit candidates, and adjustable 9:16 cut suggestions.
- Sources: REQ-002, REQ-003, REQ-006, JRN-001
- Dependencies: TASK-001, TASK-002
- Subtasks: candidate edit representation; preview timeline; accept/reject/adjust persistence; crop preview.
- Agent inputs and constraints: no automatic final edit without approval; retain hesitations; rejected suggestions stay in source timeline.
- Definition of Ready: analysis artifacts exist.
- BDD scenarios: BDD-JRN-001-01, BDD-JRN-001-02
- Validation: verify decision persistence and resulting preview for accepted, rejected, adjusted, and no-short cases; accept the rounded 142.317-second suggestion against 142.316667-second media duration. Evidence: cloned project review API accepted the rounded end and both edit decisions.
- Stop condition: if crop selection requires a product decision beyond adjustable manual framing.
- Definition of Done: review decisions persist across restart and determine exact export segments; user guide updated.
- Expected results: a complete review-ready edit decision list.
- Affected documentation: how-to review guide, technical definition, workflow state.

#### TASK-007 — Generate semantic edit and vertical-cut suggestions
- Status: semantic prompt, validation and merge behavior remain in scope; original OpenCode/Codex CLI provider implementation is superseded by TASK-010 and DEC-018.
- Description: send local transcript and timestamps to the currently fixed MiMo model after transcription; merge transcript-based removal and vertical-cut suggestions with local heuristics.
- Sources: REQ-002, REQ-003, REQ-006, JRN-001, BDD-JRN-001-07, BDD-JRN-001-08, DEC-009/018
- Dependencies: TASK-001, TASK-002
- Subtasks: treat transcript content as untrusted data while recognizing clear spoken editorial intent (including relative time references resolvable from duration); permit an exact editorial-intent quote outside the target interval while independently validating bounded timestamps; parse constrained JSON; bound output, merge duplicates; exclude suggested-removal spans from cuts; persist model status; disclose transcript transfer and expose source/evidence in review.
- Agent inputs and constraints: never send source media; never accept model output as an automatic edit; do not persist raw provider responses; use fixed `opencode/mimo-v2.6-flash-free` via OpenCode CLI as specified by TASK-010.
- Definition of Ready: transcript semantic-analysis requirements and the selected generative model are confirmed by REQ-002/009 and DEC-018.
- BDD scenarios: BDD-JRN-001-07, BDD-JRN-001-08
- Validation: verify MiMo output on the supplied OBS transcript and worker-stage output, recording model outcome, interval bounds, review provenance, and vertical/removal non-overlap. Include a transcript phrase requesting removal of the last 30 seconds and verify candidate interval/evidence; include ambiguous and instruction-like transcript text to verify no invented cut and no prompt override. Simulate an unavailable API and confirm local fallback.
- Stop condition: live validation requires OpenCode host authentication; use mocked CLI responses until authentication is available.
- Definition of Done: OpenCode returns constrained suggestions; CLI failure is recoverable; source remains local; every candidate is reviewable and correctly bounded; setup/privacy guide, technical definition, workflow state, and task evidence are current.
- Expected results: semantic cut suggestions joined to local rule candidates with visible evidence and model provenance.
- Affected documentation: how-to run, technical definition, PRD/journey traceability, workflow state.

#### TASK-011 — Suggest and review contextual horizontal YouTube cuts
- Description: include transcript-based, individually reviewable landscape cut suggestions that preserve complete topic context without a maximum duration.
- Sources: REQ-002, REQ-004, REQ-005, REQ-006, REQ-010, JRN-001, BDD-JRN-001-11, DEC-013.
- Dependencies: TASK-002, TASK-003, TASK-007.
- Constraints: source stays immutable; exclude all suggested removals; do not invent cuts if MiMo fails; require human approval; retain 16:9 source framing; each accepted cut gets a distinct title.
- Definition of Ready: timestamped transcript and authenticated OpenCode CLI are available.
- Validation: verify schema/parser accepts long cuts; suggestions have literal in-range transcript evidence, include end-to-end explanation context, are bounded by media duration and avoid removals; review save accepts/rejects and interval edits; accepted export is 16:9 with correctly remapped source-language and selected-translation SRT/VTT and its own YouTube selection.
- Stop condition: if a candidate's contextual boundaries cannot be supported by transcript evidence, omit it rather than shorten or fabricate it.
- Definition of Done: candidates are reviewable, accepted cuts export individually and are eligible for private upload with bilingual captions; Diátaxis guide and traceability are current.
- Evidence so far: real OpenCode text and image requests with the fixed model succeeded; full app run remains pending after container rebuild.
- Evidence: MCP Playwright opened the review UI and rendered the two existing horizontal cut suggestions, each with preview, interval and title controls. The E2E analysis on the new clone hit an OpenCode timeout; local fallback did not fabricate horizontal suggestions.
- Affected documentation: PRD, journeys, technical definition, review/export guide, workflow state, revision history.

#### TASK-004 — Render publication assets and metadata
- Description: render horizontal master and selected vertical cuts; generate source-language and selected-translation SRT/VTT; collect editable YouTube metadata.
- Sources: REQ-002, REQ-003, REQ-004, REQ-006, JRN-001, JRN-002
- Dependencies: TASK-003
- Subtasks: FFmpeg edit rendering; subtitle sidecars and burn-in; output naming; metadata editor.
- Agent inputs and constraints: render only approved edits/cuts; source remains immutable; use safe temporary files and atomic completion markers.
- Definition of Ready: saved review decisions exist.
- BDD scenarios: BDD-JRN-001-02
- Validation: verify files are probeable/playable and subtitle timestamps align with edited output; prove accepted removed spans are absent from vertical video and its captions; discover suitable commands from FFmpeg configuration. Evidence: cloned export completed; master duration was 118.44 seconds; two vertical outputs were 1080×1920 with 45 and 43.44 seconds. The proposed vertical candidates did not intersect either suggested silence removal, and their PT-BR/EN caption clocks started at output time zero. The original project also successfully exported the master and selected-language captions after accepting the two edits whose save had originally failed.
- Stop condition: if output quality settings require unsupported product or compatibility tradeoffs.
- Definition of Done: package contains approved assets and metadata; failures preserve previous outputs; publishing guide updated.
- Expected results: review-approved local publication package.
- Affected documentation: how-to export guide, output reference, technical definition, workflow state.

#### TASK-005 — Upload selected videos and multilingual captions to YouTube
- Description: add OAuth authorization; upload selected videos with explicit private status; attach SRT tracks for the source and selected translation languages; track each result and ambiguous retry state.
- Sources: REQ-005, REQ-006, DEC-002, DEC-003, JRN-002
- Dependencies: TASK-004
- Subtasks: OAuth setup with `youtube.upload` and `youtube.force-ssl`; token storage; metadata mapping; resumable video upload; caption insertion; per-track progress/retry; success link state.
- Agent inputs and constraints: never commit credentials; never set public visibility; require explicit approval; don't retry in ways that silently duplicate an upload.
- Definition of Ready: YouTube OAuth client configuration is available locally, or implement connector/configuration flow without performing live upload.
- BDD scenarios: BDD-JRN-002-01, BDD-JRN-002-02, BDD-JRN-002-03, BDD-JRN-002-04
- Validation: inspect outbound resource for `privacyStatus=private`; exercise authorization failure and simulated network retry; live upload only with user's configured account authorization.
- Stop condition: if API verification, quota, or OAuth configuration requires account/project actions unavailable to the implementer.
- Definition of Done: selected videos can be uploaded privately after approval with the source and selected translation tracks attached; results and ambiguous states are tracked separately; OAuth how-to and data-safety docs updated.
- Expected results: each selected asset has a private YouTube URL or recoverable error state.
- Affected documentation: YouTube OAuth how-to, technical definition, workflow state.

#### TASK-006 — Reconcile documentation and MVP release evidence
- Description: finish Diátaxis user guides, repository navigation, task evidence, and release checklist after implementation is verified.
- Sources: REQ-001–REQ-007, JRN-001–JRN-003
- Dependencies: TASK-001 through TASK-005
- Subtasks: update index/map; remove placeholders; reconcile IDs and revisions; record pilot outcome.
- Agent inputs and constraints: document only behavior that has evidence; keep product artifacts separate from user guides.
- Definition of Ready: all preceding tasks implemented or explicitly blocked.
- BDD scenarios: all BDD-JRN scenarios above.
- Validation: inspect traceability, links, documentation types, and recorded task evidence.
- Stop condition: any unowned material product question or release criterion without evidence.
- Definition of Done: product workflow artifacts and user documentation are current; state records blockers and next action accurately.
- Expected results: reproducible handoff and reviewable MVP state.
- Affected documentation: docs index, Diátaxis map/guides, workflow state, revision history, README, CONTRIBUTING, AGENTS.

### TASK-008 — Modernizar revisão e globalizar configurações YouTube
- Fontes: REQ-005/006/007, JRN-001/002/003, DEC-010.
- Dependências: TASK-001/003/005; mantém ASR, IA e exportação existentes.
- Resultado: shell global responsivo, etapas claras, vídeo/revisão em paralelo, abas com rascunhos preservados, estados vazios e ações contextualizadas, página `/settings` para OAuth/conexão global.
- Limites: manter visibilidade privada e aprovação por projeto; não executar modelos nem publicar durante a validação visual; preservar projetos e credenciais reais.
- Subtarefas: reorganizar HTML/JS/CSS; novos endpoints globais; armazenamento OAuth restrito e validação; testes com credenciais sintéticas; verificação de revisão entre abas, navegação e telas menores; guias e rastreabilidade.
- Definition of Ready: o usuário confirmou modernização e configuração global.
- BDD: BDD-JRN-001-09, BDD-JRN-003-01/02/03.
- Verificação: `node --check app/static/app.js`; `python -m unittest discover -s tests`; build Compose; navegador desktop/mobile com dados de projeto existentes somente para leitura e clone descartável para salvar decisões.
- Definition of Done: configuração acessível sem projeto; JSON seguro e estado global; decisões persistem entre abas; layout sem overflow; testes passam; documentação reconciliada.
- Parada: configuração Google Cloud ou autorização real indisponível não impede validar UI/armazenamento; não iniciar OAuth/upload sem necessidade.
- Documentação: PRD/jornadas/definição/plano/estado/histórico, guias de revisão e YouTube.
- Evidência: cinco testes isolados de configuração global passaram; teste de navegador preservou seleções/títulos ao trocar abas e visitar configurações e confirmou persistência inclusive de controles ocultos em clone descartável. Inspeção desktop/mobile e verificações em 390/768/1512 px não apresentaram overflow; console sem exceções e sintaxe JS válida. Contrastes principais entre 7,75:1 e 16,49:1. A falha de “Nova gravação” vinha do `app.js` antigo em cache após atualização; o botão agora abre o seletor explicitamente e HTML versiona CSS/JS. Com projeto revisado aberto, o seletor MP4/MKV foi aberto e cancelado sem importar mídia; o handler foi confirmado no HTML atualizado. Gallery registrou a instância, reatribuiu a porta ocupada `30009` para `30100`, iniciou o serviço no contexto Docker `default` com saúde HTTP, e executou `stop`; `make stop` repetiu sem erro, `make start` repetiu no `8000` e `/api/health` confirmou FFmpeg/ffprobe disponíveis. Serviço final restaurado em `http://127.0.0.1:8000`. Nenhuma chamada de modelo ou upload real. Implementação concluída; autorização YouTube real continua dependente do cliente Google Cloud do usuário.
- Evidência adicional (2026-10-17): tela de análise usa a sequência real de `job.stage` para mostrar etapas concluídas, ativa e pendentes; oculta a validação de frames quando desativada e usa o progresso apenas como contagem de etapas concluídas. `node --check app/static/app.js` e parse do HTML passaram; o container foi reconstruído e `/api/health` confirmou FFmpeg, ffprobe e OpenCode disponíveis. Captura Chrome headless em 1440×1050, durante análise semântica real, confirmou os quatro passos concluídos, o passo atual, a contagem e a hierarquia visual da timeline. O navegador integrado da sessão não estava disponível; a captura headless serviu para revisar o layout desktop. A captura revelou que somente o JavaScript tinha cache-bust: o navegador reaproveitava CSS anterior, expondo a lista numerada e o texto de leitor de tela. Atualizei também a versão do CSS; nova captura Chrome em 1440×900 confirmou timeline estilizada, estados alinhados e texto acessível oculto. O rebuild encerrou uma nova tentativa de análise ativa; o projeto foi marcado como falho com retomada manual, preservando fonte e dados parciais.
- Correção do estado terminal (2026-10-17): reproduzido no projeto `[id de projeto local]`: API já informava `review-ready` e `job.stage=complete`, mas a tela permanecia em `analyzing`. O cliente agora busca sem cache, sincroniza também ao reabrir o mesmo projeto e protege o polling contra troca de projeto enquanto a requisição está em curso. O JS/CSS receberam nova versão de asset para invalidar a cópia anterior. Trace: REQ-006, JRN-001, BDD-JRN-001-13, DEC-019.
- Correção validada no Playwright (2026-10-17): defini `youtubeCutsHtml()` para renderizar cortes horizontais; a rota agora captura somente erro da API e deixa exceções de renderização visíveis, em vez de redirecionar à galeria. O botão de importação usa `input.click()`; o E2E importou a gravação pelo próprio input sem criar projeto vazio. Rebuild via `make start` serviu os assets corrigidos em 30100. Trace: REQ-001/002/004/006/010, JRN-001, BDD-JRN-001-11/13/15, DEC-013/019, TASK-002/004/008/011.

### TASK-009 — Criar galeria e renomear projetos
- Descrição: transformar Gravações em uma biblioteca ampla para encontrar e abrir projetos; permitir renomeação persistente por cartão e editor.
- Fontes: REQ-008, REQ-006, JRN-004, BDD-JRN-004-01/02/03, DEC-011.
- Dependências: TASK-001; reutiliza API completa de projetos.
- Restrições: preservar mídia, decisões, legendas, exportações e credenciais; nome limitado e sem separadores/caracteres de controle; conservar navegação global e layout responsivo.
- Critérios: galeria com todos os projetos, busca por nome, status, página 12/24/48, navegação anterior/próxima, estados vazios; rota estável por ID; nome renomeado persiste após recarga e atualiza em todo lugar.
- Verificação: rodar a suíte existente; usar armazenamento temporário para API de renomeação; confirmar persistência e fonte inalterada; verificar busca, status, página e abertura no navegador em desktop e celular, inclusive vazios e mais de uma página.
- Definition of Done: três BDDs REQ-008 demonstrados, nenhuma alteração na fonte, documentação de revisão e state/histórico atualizados.
- Evidência (2026-10-15): API com storage temporário renomeou projeto e preservou bytes do source; listagem summary omite transcrição; `GET /projects/{id}` serve o editor. Chrome headless em desktop/mobile mostrou a galeria responsiva com os quatro projetos reais. Em app isolado com 13 fixtures, navegador exibiu 12 na primeira página, 1 na segunda, pesquisa retornou 1 e status sem resultados mostrou estado vazio. Artefatos temporários removidos.
- Parada: se forem exigidas exclusão de projetos ou alteração de ativos, isso excede a tarefa e requer requisito novo.

### TASK-010 — Usar MiMo V2.6 Flash Free via OpenCode para texto e imagem
- Descrição: fixar a análise semântica no modelo `opencode/mimo-v2.6-flash-free` e disponibilizar a autenticação OpenCode do host ao backend.
- Fontes: REQ-009/011, REQ-002, JRN-005, BDD-JRN-005-01/02, DEC-018.
- Dependências: TASK-007, TASK-008, TASK-012.
- Restrições: OpenCode é o único CLI generativo utilizado; Codex nunca é invocado; transcrição e tradução locais; sem chave/provider selector configurável no estúdio; imagem opcional controlada por gravação; não enviar vídeo completo.
- Critérios: sem OpenCode ou autenticação montada, API não agenda análise e UI explica autenticação; texto é enviado via OpenCode ao ID fixo e o resultado grava modelo/status; falha mantém sugestões locais; settings mostram estado do CLI e modelo.
- Verificação: mocks do CLI validam ID e transcrição; chamada real de texto e chamada multimodal real com frame de `teste.mp4`; rodar testes existentes, compilação Python/JS, rebuild/start via Project Gallery e conferir `/api/health`, settings e UI.
- Definition of Done: BDDs REQ-009 demonstrados para texto/imagem; nenhuma execução de Codex; guias e rastreabilidade atualizados.
- Evidência (2026-10-17): `opencode models` lista `opencode/mimo-v2.6-flash-free`; chamada real de texto retornou JSON válido e chamada real com frame JPEG 768×432 de `teste.mp4` classificou apresentação dominante com confiança alta; 13 testes passaram após adaptação do CLI. O projeto criado em `http://localhost:30100/` completou a análise ponta a ponta: semantic model complete, sete frames multimodais completos, política de cor `preserve`, projeto `review-ready`; a inspeção humana da interface fica pendente.

### Acabamento — favicon do estúdio
- Descrição: adicionar favicon SVG alinhado ao símbolo circular e à paleta visual do aplicativo.
- Verificação: confirmar referência no HTML e resposta da rota `/static/favicon.svg` após rebuild.
- Evidência: favicon vetorial criado e referenciado no documento principal.
- Documentação afetada: estado do workflow.

## Full scope coverage

| Requirement / journey | Phase/tasks, deferral, or retirement | Rationale |
|---|---|---|
| REQ-001 / JRN-001 | Phase 1, TASK-001/002 | Necessary input and local processing |
| REQ-002 / JRN-001 | Phase 1, TASK-002/003/004 | Core editing and captions |
| REQ-003 / JRN-001 | Phase 1, TASK-003/004 | Vertical outputs |
| REQ-004 / JRN-001/JRN-002 | Phase 1, TASK-004 | YouTube-ready package |
| REQ-005 / JRN-002 | Phase 1, TASK-005 | Private automated upload |
| REQ-006 / JRN-001/JRN-002/JRN-003 | Phase 1, TASK-001/003/005/008/018/019 | Revisão, navegação, importação e aprovação |
| REQ-007 / JRN-003 | Phase 1, TASK-008 | Configuração global YouTube |
| REQ-008 / JRN-004 | Phase 1, TASK-009 | Galeria e organização de projetos |
| REQ-009 / JRN-005 | Phase 1, TASK-010 | Modelo fixo OpenCode `opencode/mimo-v2.6-flash-free` |
| REQ-010 / JRN-001 | Phase 1, TASK-007/011 | Cortes horizontais com contexto completo |
| REQ-011 / JRN-001 | Phase 1, TASK-012 | Rastreamento de crop, correção neutra e checagem visual local |
| REQ-002/003/006 / JRN-001 | Phase 1, TASK-007/010 | Transcript-only MiMo suggestions and resilient local fallback |
| REQ-006 / JRN-001/JRN-003/JRN-004 | TASK-014, DEC-021 | Instrument-design visual language across the studio |
| REQ-006 / JRN-003 | TASK-016/017, DEC-021, BDD-JRN-003-04 | Selectable and persisted Chalk, Graphite and Workshop themes |

## Confirmed decisions, assumptions, and open questions

- Confirmed: MVP success is one real end-to-end recording through private upload.
- Assumption: no direct posting outside YouTube; Shorts/Reels/TikTok files are exported for manual posting.
- Open prerequisite: OAuth client configuration is user-owned; implementation may be completed without live upload if unavailable.

#### TASK-012 — Analyze scenes, protect slide colors, and verify visual quality
- Description: analyze sampled frames locally for framing, exposure/color, and screen-like scenes; expose MiMo-V2.6-Flash-Free judgment via OpenCode enabled by default, switchable per analysis, of the globally configured 2–1024 sampled frames (default 8), arranged in grids of up to 128 labeled frames, editable vertical tracking/stable crop, and an explicitly approved neutral grade that is blocked for presentation-dominant scenes; verify every rendered video.
- Sources: REQ-001, REQ-003, REQ-004, REQ-006, REQ-011, JRN-001, BDD-JRN-001-12, DEC-015, DEC-016, DEC-017.
- Dependencies: TASK-001, TASK-003, TASK-004, TASK-011.
- Constraints: never upload source media; attach at most eight reduced JPEG grids containing up to 128 of the configured 2–1024 timestamp-labeled frames when OpenCode authentication exists, with a per-analysis opt-out toggle; use the same OpenCode model for transcript and image analysis; auth file is mounted read-only and never returned; keep grade disabled by default and block it if slides dominate or classification is uncertain/unavailable; bound correction strength; no render replaces the source; allow stable framing on low detection confidence.
- Definition of Ready: local video source and review project exist; user confirmed human review and requested default-on MiMo multimodal frame judgment when OpenCode authentication is available, a per-analysis opt-out, and reduced-frame limits.
- Validation: cases include a centered/side-positioned face, movement between sampled positions, slide-dominant video with a small webcam overlay, screen-like heuristic, MiMo positive/negative/low-confidence/error responses, default-on when configured and explicit opt-out, no image request when visual toggle is off, scene-transition selection with uniform fill, grade block on review API and FFmpeg renderer, no face, multiple faces, low-confidence detection, and accepted edit joins. Confirm the local three-moment contact sheet compares source, suggested grade and 9:16 crop; crop position and intensity refresh it; `track` and `steady` preview/export behavior, grade off/on and intensity endpoints, persistence, no source mutation, expected 1080×1920 / 1920×1080 / source dimensions, expected durations, and visible QC warnings for deliberately abnormal samples.
- Stop condition: if local dependencies fail to provide a usable frame detector on the supported Python/runtime target, retain stable crop and report the capability gap. If OpenCode is unavailable, keep local result and preserve slide colors; never silently retry or use a different model.
- Definition of Done: projects persist visual metrics, crop trajectory, scene review, grade policy, crop mode and grade approval; the Image tab locally previews original, suggested grade and vertical crop at three moments; a slide-dominant scene visibly preserves original colors and cannot receive global grading through UI, API, or render; MiMo runs by default only by default and can be switched off per analysis; auth is private, no auth/frame data leaks into responses/logs; actual-frame QC records dimensions/duration/sample warnings on each video asset; how-to guide and workflow state are reconciled.
- Evidence: Python/JavaScript syntax checks passed and the rebuilt Docker image includes OpenCV. On a disposable copy of `[caminho local redigido]`, local analysis sampled 240 frames and detected no face (`low` confidence), correctly leaving stable crop available; measured median luma 0.712 and suggested bounded brightness -0.0302 / contrast 1.0302 / saturation 1.0. Ten-second vertical and horizontal renders using the crop trajectory expression completed at 1080×1920 and 1920×1080, each 9.983 s. QC flagged dark opening frames. The render initially exposed an unsupported `crop:eval` option, which was removed; trajectory rendering then succeeded. The preview endpoint now returned a decodable 1440×1110 JPEG comparing original, suggested grade, and vertical crop at 00:17, 01:11, and 02:05 for the validation project. No source was modified and no AI CLI or YouTube API was called. Face-positive/multi-face tracking and review in the application browser remain pending. The repository-wide pytest collection previously encountered a permission error while scanning `models/cache`, so that cache was not changed. Isolated visual policy, mocked MiMo payload, key storage, default-on/opt-out routing, scene sampling, and YouTube settings tests pass (12 total). Running the local detector in the supported container on the supplied `teste.mp4` produced `stable_scene_ratio=0.987`, edge density `0.116`, and `grade_policy=preserve`; it did not depend on face detection (face ratio 0). A validação final em container enviou sete frames reduzidos ao OpenCode; o modelo classificou slides como dominantes com confiança alta e a política preservou as cores. O primeiro build exibiu um JSONDecodeError para a resposta em bloco Markdown; após aceitar esse formato e reconstruir, a chamada multimodal concluiu. O projeto visível de teste também completou a análise semântica. A revisão visual humana continua pendente. UI/API configuration, default-on behavior when configured, and a per-analysis opt-out are implemented; FFmpeg scene sampling was exercised on the supplied source and returned 4.45s plus uniform coverage through 142.32s, capped at 8 frames; browser interaction review remains pending.
- Expected results: reviewer can correct vertical framing and approve a restrained image correction before export.
- Affected documentation: how-to-review, technical definition, PRD/journey traceability, workflow state.

### TASK-014 — Aplicar instrument-design a todas as telas
- Description: aplicar a linguagem material original Graphite à galeria, shell, análise, revisão, publicação e configurações sem mudar stack, identidade funcional ou fluxos existentes.
- Sources: REQ-006, JRN-001, JRN-003, JRN-004, DEC-021; skill `instrument-design`.
- Dependencies: TASK-008, TASK-009, TASK-012.
- Constraints: superfícies foscas, módulos/teclas elevados, áreas de trabalho rebaixadas, uma direção de luz, contraste adequado, texto informativo ≥12 px, foco/estado visíveis, alvos de ação preferencialmente 44 px, responsividade e movimento reduzido; sem imitar produto ou controles proprietários.
- Validation: inspeção MCP Playwright das rotas `/`, `/projects/{id}` e `/settings` em desktop e mobile; verificar tokens carregados, hierarquia/superfícies, ausência de scroll horizontal móvel, foco, estados principais e console. Capturas Chrome headless para galeria, projeto e configurações.
- Definition of Done: stylesheet global aplicada por todas as rotas; navegação, galerias, módulos de análise/revisão e configurações usam os mesmos papéis de material; documentação Diátaxis explica a direção; app rebuild/restart conforme Project Gallery. Atendido em 2026-10-17.
- Affected documentation: PRD REQ-006, journey criteria, DEC-021, workflow state e `docs/diataxis/explanation-interface-design.md`.
- Evidence (2026-10-17): `make start` rebuilt/restarted port 30100. Chrome headless screenshots inspected the gallery, review editor and settings at desktop and mobile widths. MCP Playwright confirmed 12 gallery cards, loaded Graphite CSS, responsive settings grid, no page-level horizontal overflow at 312 CSS px, no visible informative text below 12 px in the review editor, 44 px settings action targets, and zero console errors/warnings. Initial 4-column project stepper overflow was fixed by a 2×2 mobile layout; rerun reported `scrollWidth=300` against `innerWidth=312`. Foreground/background pairs checked against the skill minimum: primary/canvas 15.86:1, primary/panel 9.83:1, muted/inset 9.77:1, amber/body 7.21:1, success 7.28:1, warning 8.23:1, error 8.12:1, primary-key text 6.50:1 minimum; the raised panel rim is 3.23:1 against the lightest panel surface. YouTube upload and processing workflows were not invoked.

### TASK-015 — Expandir traduções de legendas para dez idiomas
- Status: multi-language translation path validated; SRT/VTT export and YouTube publishing validation remain open.
- Description: allow requesting multiple caption translations together from the corrected source transcript; support a broad-reach list of ten destinations and propagate completed tracks to export and YouTube upload.
- Sources: REQ-002/004/005/006, JRN-001, BDD-JRN-001-14/16, DEC-020/022; official YouTube and Udemy language-reach pages.
- Dependencies: TASK-002 and existing transcript correction/translation workflow.
- Constraints: do not translate before saved transcript corrections; preserve source captions and timestamps; translation remains local via Argos; try direct pairs then a local English pivot; preserve successful languages if a later translation fails; never claim these ten are a statistically ranked top ten because platform figures are not comparable.
- Validation: inspect multi-select UI; check API accepts multiple valid destinations and rejects source/unsupported IDs; verify successful language IDs persist into SRT/VTT names, selected YouTube caption locales, and state after partial failure; confirm source is untouched and prior translations clear on edited transcript. Use existing app validation tooling only; do not trigger a live upload without OAuth setup.
- Definition of Done: the UI shows ten selectable destination languages (excluding the source track where applicable), several can be requested at once, output/export/upload recognize each supported language ID, and localized errors retain previously completed translation tracks. Update user how-to, PRD/journey/technical decisions, and workflow state.
- Stop condition: if an Argos pair has neither direct nor English-pivot package, report the missing model pair clearly and keep other completed tracks.
- Affected documentation: PRD, user journeys, DEC-022, how-to-review, workflow state, revision history.
- Evidence (2026-10-17): tested all ten targets from one PT-BR sample individually and in a single `/translate` job on a disposable project. `en`, `es`, `fr`, `de`, `hi`, `ar`, `id`, `ja`, `ru`, and `tr` each returned nonempty output; all selected codes persisted, and every translated segment retained the source ID and `1.25–7.5 s` timing. Catalog inspection showed no direct PT pair for `fr`, `de`, `hi`, `ar`, `id`, `ja`, `ru`, or `tr`, so the English pivot was exercised. The API rejected `xx` with HTTP 422. The service accepted the job and reached `review-ready`; all disposable project data was removed afterward. Translation outputs were inspected for basic readability, but this is not a professional native-speaker quality review. YouTube upload and SRT/VTT export were not exercised in this run.

### TASK-016 — Oferecer temas Chalk, Graphite e Workshop
- Status: concluída; revisão no navegador, contraste e responsividade passaram.
- Description: expandir o sistema `instrument-design` com Chalk claro e Workshop junto ao Graphite; disponibilizar seleção nas configurações globais e lembrar a escolha neste navegador.
- Sources: REQ-006, JRN-003, BDD-JRN-003-04, DEC-021; pedido do usuário em 2026-10-17; referências de temas e contrato de tokens da skill `instrument-design`.
- Dependencies: TASK-014 e shell global de configurações.
- Constraints: preservar HTML/CSS/JS, rotas e hierarquia; verde Workshop define superfícies de trabalho/visores; Chalk segue quente; preferência não vai ao backend; manter contraste, foco/seleção visíveis, alvos 44 px, movimento reduzido e adaptação móvel.
- Validation: inspecionar configurações, galeria e revisão de projeto nos três temas em desktop/mobile; persistência entre rotas/reload; contraste de textos, controles, bordas e ação primária; console e overflow horizontal.
- Definition of Ready: pedido explícito por tema claro e Workshop, mantendo `instrument-design`.
- Definition of Done: três temas selecionáveis e persistentes em todas as rotas; evidência de navegador, contraste e responsividade; documentos de produto e Diátaxis reconciliados.
- Stop condition: ajustar tokens se qualquer superfície funcional falhar legibilidade ou contraste.
- Affected documentation: PRD REQ-006, journey JRN-003/BDD-JRN-003-04, DEC-021, explicação Diátaxis, workflow state e histórico.
- Evidence (2026-10-17): `make start` rebuilt the local app and served `instrument-theme.css?v=20261017-themes-4`. MCP Playwright exercised settings, project `[id de projeto local]` and gallery; theme selection persisted through route navigation and page reload. Gallery displayed 12 cards. At the narrow 312 px viewport, document width was 300 px. Browser console returned zero errors/warnings. Theme contrast measured: Graphite ink/canvas 15.86:1, ink/panel 9.83:1, signal/body 7.21:1; Chalk ink/canvas 12.03:1, muted/canvas 5.88:1, muted/body 5.04:1 and primary action minimum 4.85:1; Workshop ink/canvas 8.59:1, muted/canvas 5.67:1, muted/body 5.00:1, orange signal/body 5.06:1 and primary action minimum 4.85:1. Inspected project review screenshots in Chalk and Workshop and confirmed selected states/navigation remain neutral and legible. No project review or export data was changed. Remaining review is normal creator visual acceptance.


### TASK-017 — Auditar a aplicação de instrument-design
- Status: concluída.
- Description: revisar a linguagem material existente, corrigir legibilidade/hierarquia/responsividade e extrair orientações reutilizáveis para a skill instalada, conforme pedido explícito do usuário.
- Sources: REQ-006/008, JRN-001/003/004, BDD-JRN-003-04, DEC-021; skill `instrument-design` e pedido de revisão em 2026-10-17.
- Dependencies: TASK-014/016 e shell existente.
- Inputs / Ready: três temas existentes, projetos locais importados/revisados/exportados e referências material-study, token-contract e application-shell da skill.
- Constraints: manter stack e conteúdo; nenhuma alteração em mídia/decisões salvas; nenhum processamento IA ou publicação externa; estados pendentes/de falha podem usar fixtures explicitamente identificadas, só no DOM.
- Validation: MCP Playwright sobre configurações, galeria, importação, cinco abas de revisão e publicação; comparar temas nas mesmas larguras de 1440 e 360 px; estilos computados para texto/superfície e gradientes; inventário tipográfico, alvos, overflow, seleção/foco, persistência e console. Verificar sintaxe JS e iniciar pelo `make start` existente.
- Definition of Done: cores fixas não vazam entre temas; poços/visores e campos usam tintas adequadas; abas refluem com estado pressionado; ações neutras e primárias mantêm hierarquia e relevo; rótulos ≥12 px; busca preserva foco e configurações carregam biblioteca; docs reconciliadas. Atendido.
- Stop condition: se uma superfície falhar contraste/reflow, corrigir e repetir sua verificação; não iniciar jobs ou upload para produzir estado visual.
- Evidence: [auditoria de interface](../engineering/interface-review.md) registra 72 combinações sem falhas de texto/overflow/tamanho mínimo, contraste mínimo 4,58:1, capturas e limites. A skill recebeu um guia de auditoria de aplicações e o cenário de avaliação 12; não foi executado benchmark comparativo entre versões da skill.
- Affected documentation: DEC-021, explicação Diátaxis, relatório de auditoria, workflow state e histórico central. REQ-006 e JRN-003 continuam válidos sem mudança de escopo.


### TASK-018 — Manter navegação superior em todas as rotas
- Status: concluída.
- Sources: REQ-006/007/008, JRN-003/004, BDD-JRN-003-05, DEC-010/021; correção solicitada pelo usuário em 2026-10-17.
- Dependencies / inputs: TASK-008/009/016/017, shell e rotas existentes.
- Scope: substituir o shell lateral por cabeçalho superior compartilhado; remover alternância `gallery-mode` e lista lateral; manter galeria, links, destino atual, importação e configurações.
- Constraints: preservar stack, temas e decisões de revisão; no celular manter links no topo com reflow; sem processamento, exportação ou publicação externa.
- Validation: MCP Playwright alterna galeria→configurações, histórico, projeto→configurações e reload direto em 1440/360 px; verifica geometria do menu, `aria-current`, ausência de sidebar/overflow. Inspecionar os três temas, sintaxe JS, console e capturas; reiniciar por `make start`.
- Definition of Done: navegação com geometria constante entre rotas na mesma largura; galeria é o acesso aos projetos; documentação atualizada. Atendido.
- Evidence: seis estados de navegação em cada largura passaram. Em 1440 px, menu em x=1047/y=14, 321×52 px em todas as rotas; em 360 px, x=16/y=71, 272×46 px. Não há sidebar nem overflow horizontal. `node --check app/static/app.js` passou; 18 combinações adicionais (3 rotas × 3 temas × 2 larguras) mantiveram geometria estável, sem sidebar/overflow e com um destino atual; console sem erros/avisos. Capturas desktop/mobile em `.playwright-mcp/topnav-project-{1440,360}.png` inspecionadas.
- Stop condition: corrigir qualquer salto de geometria, perda de destino atual, erro de renderização ou overflow antes de encerrar.
- Affected documentation: PRD, journeys, DEC-010/011, explicação Diátaxis, workflow state e histórico.

### TASK-019 — Restaurar a ação Nova gravação
- Status: concluída.
- Sources: REQ-006, JRN-003, BDD-JRN-003-06, DEC-010; solicitação do usuário em 2026-10-17.
- Scope: Nova gravação abre um painel visível a partir do cabeçalho ou biblioteca vazia, com seletor de arquivo e arrastar e soltar. Cancelar preserva a rota e o projeto.
- Implementation: `<dialog>` nativo com input visível, dropzone, feedback local de importação/erro, Escape/Fechar e restauração explícita de foco. Não há ativação programática de seletor oculto. Erros permitem nova seleção. Assets `20261017-import-dialog-5`, HTML das três rotas com `Cache-Control: no-store` para evitar shell antigo em cache, serviço reconstruído em `30100`.
- Validation: `PLAYWRIGHT_CHANNEL=chrome npm run test:e2e -- --headed`: 9 testes passaram e 1 upload duplicado mobile omitido. Google Chrome real com janela visível, desktop/mobile: painel abre mesmo com `HTMLInputElement.click()` programático bloqueado, cancelamento mantém rota e lista, Enter/Espaço, Escape/Fechar, foco restaurado, input visível abre `filechooser`, validação e falha de upload recuperáveis. Upload real de `~/Videos/OBS/teste.mp4` chega às opções de análise; painel reabre depois. Screenshots de painel na galeria/projeto e importação concluída inspecionadas, incluindo mobile; prévias Graphite/Chalk/Workshop em `.playwright-mcp/new-recording-*.png`.
- Definition of Done: resposta visual observável ao clique, campo de arquivo diretamente utilizável, cancelamento e erro recuperáveis, importação real e screenshots comprovados no Chrome. As validações anteriores não explicavam o relato do usuário; o fluxo não depende mais do acionamento invisível do seletor.
- Affected documentation: REQ-006, BDD-JRN-003-06, DEC-010, workflow state e histórico.


### TASK-020 — Redimensionar ou recolher a prévia do vídeo
- Status: concluída; comportamento e responsividade validados no Playwright.
- Sources: REQ-006, JRN-003, BDD-JRN-003-07, DEC-023; solicitação do usuário em 2026-10-17.
- Scope: devolver espaço à revisão com opções compacta/equilibrada/ampla e controle para recolher/mostrar o vídeo.
- Constraints: manter controles disponíveis quando o vídeo estiver oculto; persistir preferências neste navegador; em uma coluna, adaptar altura sem overflow; preservar Graphite, Chalk e Workshop.
- Validation: abrir projeto em desktop e mobile no Playwright, exercitar os quatro estados, confirmar preferência após recarregar/navegar, medir grid/overflow e inspecionar screenshots.
- Evidence: projeto `[id de projeto local]`, viewport desktop 1680 px: prévia compacta 514 px/revisão 999 px, equilibrada 757/757 px, ampla 908/605 px e recolhida 0/1537 px. Mobile 390 px: alturas de vídeo 150/220/300 px nas três opções, largura do documento 375 px; em 360 px, documento 345 px (sem overflow). Recarregar restaurou compacto/recolhido e `aria-expanded=false`; depois a preferência foi restaurada para equilibrada/visível. Console: zero erros/avisos. Screenshots inspecionadas: `.playwright-mcp/preview-space-compact-desktop-final.png`, `.playwright-mcp/preview-space-mobile-expanded-final.png` e `.playwright-mcp/preview-space-mobile-collapsed-final.png`.
- Definition of Done: revisão ocupa a largura restante ao recolher; as três larguras mudam a proporção em desktop e a altura em telas estreitas; estado pode ser restaurado; documentação Diátaxis alinhada. Atendido.
- Affected documentation: PRD REQ-006, BDD-JRN-003-07, DEC-023, how-to review, explicação de interface, workflow state e histórico.


### TASK-021 — Definir prévia compacta como padrão
- Status: concluída; padrão inicial e preferências persistidas validados no Playwright.
- Sources: REQ-006, JRN-003, BDD-JRN-003-07, DEC-023; solicitação do usuário em 2026-10-17.
- Scope: quando ainda não houver preferência salva, iniciar o editor com a prévia compacta; escolhas anteriores continuam valendo.
- Validation: Playwright em contexto limpo confirmou compacto inicialmente; ampla/recolhida persistiu após recarga; capturas e console inspecionados.
- Evidence: após remover as duas chaves do `localStorage`, projeto `[id de projeto local]` abriu compacto/visível no desktop (viewport 1440 px; colunas 437/849 px) e sem overflow (documento 1425 px). Selecionar ampla e recolher, seguido de reload, restaurou `wide`, oculto e `aria-expanded=false`. Preferências limpas depois da validação; console sem erros/avisos. Screenshot: `.playwright-mcp/preview-space-compact-default-desktop.png`.
- Definition of Done: padrão compacto em navegador novo, preferências existentes não sobrescritas e app atualizado em `30100`. Atendido.
- Affected documentation: PRD REQ-006, BDD-JRN-003-07, DEC-023, how-to review, explicação de interface, workflow state e histórico.

## Extensão de qualidade da análise — TASK-022–035

Pedido de 2026-10-26: reduzir falsos positivos, gerar cortes YouTube, detectar silêncio final, avaliar cor da câmera por cena e selecionar Codex GPT-6 Luna Medium. O [plano de qualidade, revisão 10](analysis-quality-plan.md) registra as onze tarefas e a evidência por tarefa; o [diagnóstico, revisão 2](../engineering/analysis-quality-audit.md) separa causas confirmadas de hipóteses.

A implementação parcial foi autorizada pelo usuário e executada no root app. A reanálise integral Codex no clone `[id de projeto local]` e relatório foram concluídos; revisão humana/ground truth e export comparativo seguem pendentes em TASK-030. TASK-034 resume fragmentação ASR e cobertura visual na UI. O projeto original e suas decisões não foram alterados. Fontes: REQ-002/003/004/006/009/010/011/012, JRN-001/005, DEC-024–033, BDD-JRN-001-17–30 e BDD-JRN-005-01–03. Pendências de OAuth permanecem separadas.

Em 2026-10-27, após o caso `[id de projeto local]` mostrar novamente que o comentário era sugerido sem a tentativa anterior, TASK-035 acrescentou um passe focado com evidências de palavras para tentativa, comentário e retomada. Três chamadas focadas e a reanálise semântica integral no clone `[id de projeto local]` produziram o corte completo; 66 testes Python e 12 Playwright passaram. A revisão audiovisual humana geral de TASK-030 segue pendente.

## Checkpoint de execução — TASK-022–034

Em 2026-10-27, o serviço `30100` foi atualizado depois de confirmar que não havia jobs ativos. O clone `[id de projeto local]` completou análise visual, transcrição large-v3, medição local de silêncio e geração Codex GPT-6 Luna Medium. 56 testes Python e 14 execuções Playwright passaram. Resultado e limitações estão em [relatório de confiabilidade](../engineering/analysis-reliability-validation.md); revisão audiovisual humana e comparação de render continuam pendentes.

## Checkpoint TASK-025 — comentário editorial

BDD-JRN-001-26, REQ-002 e DEC-025: comentários editoriais próximos ao retake podem gerar remoção pendente delimitada pelas palavras do ASR; sugestões existentes dos projetos `[id de projeto local]` e `[id de projeto local]` foram ajustadas. A audição e aprovação final continuam com o usuário.

## Checkpoint TASK-025 — anomalia de ASR

REQ-002, DEC-025, BDD-JRN-001-27: indícios de colapso dos tempos de palavras são exibidos para revisão e bloqueiam novas remoções dependentes. No projeto `[id de projeto local]`, nova inferência local da janela 483–511 s foi comparada com a transcrição longa; conferência humana continua necessária.

## Checkpoint TASK-023/025/027/029 — revisão defensiva

BDD-JRN-001-28/29/30: detecção de lacuna requer áudio medido; cobertura parcial e falha semântica são visíveis; reinício sinaliza trabalho órfão; export preserva subdivisões curtas; UI resume segmentação ASR e cobertura visual. A execução integral mais recente está no clone `[id de projeto local]`; resultados e limites em [relatório](../engineering/analysis-reliability-validation.md). A revisão humana permanece pendente.
