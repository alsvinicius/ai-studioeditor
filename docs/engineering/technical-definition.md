# OBS Post Production — Technical definition

- Status: draft
- Revision: 44
- Revision history: [central log](../revision-history.md#docsengineeringtechnical-definitionmd)
- Updated: 2026-10-27
- Sources and revisions: [PRD revision 36](../product/prd.md), [journeys revision 36](../product/user-journeys.md), [YouTube multi-language audio guidance](https://blog.youtube/news-and-events/multi-language-audio/), [Udemy Business Multi-Language Collection](https://business.udemy.com/multi-language-collection/), environment inspection 2026-10-14, official [OpenCode model docs](https://docs.opencode.ai/docs/models/) and [OpenCode CLI docs](https://docs.opencode.ai/docs/cli/), [MiMo V2.6 Flash model page](https://mimo.mi.com/models/en-US/mimo-v2.6-flash), scene-aware extraction concepts from [video-frames-skill](https://github.com/mugnimaestra/video-frames-skill), [faster-whisper decoding options and supported models](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py), [YouTube upload documentation](https://developers.google.com/youtube/v3/docs/videos/insert), [caption upload documentation](https://developers.google.com/youtube/v3/docs/captions/insert)
- Related artifacts: [workflow state](../product/workflow-state.md), [implementation plan](../planning/implementation-plan.md)
- Language: Portuguese

## Constraints and preferences

- Confirmed product constraints: local media processing, transcription and caption translation; Portuguese (Brazil) default source, with English/Spanish/French options; one or multiple explicitly selected destination subtitles from English, Spanish, French, German, Hindi, Arabic, Indonesian, Japanese, Russian, and Turkish; global selection between OpenCode/MiMo and Codex GPT-6 Luna Medium for semantic text analysis and optional image review; review before rendering/upload; private-only YouTube uploads. Transcript text is editable before local translation, and editing clears stale translations.
- Environment: Ubuntu 24.04 family, Python 3.12, Node 24, Docker CLI/Compose installed, Docker daemon unavailable during inspection, Intel Iris Xe via `/dev/dri`, 19 GiB RAM, 8 GiB available memory, no host FFmpeg.
- The 2026-10-26 user request adds Codex `gpt-6-luna`/`medium` as a selectable alternative; OpenCode remains the migration default. Live Codex authentication/model integration remains unverified.

## Architecture and project boundaries

One root project with a local web application. Python service owns project state and orchestrates local media tools and OpenCode CLI calls. Browser UI provides review. FFmpeg performs media probing and rendering. Speech recognition and translation run locally. MiMo V2.6 Flash Free through OpenCode analyzes transcript text and optionally sampled images; the backend validates and consolidates suggestions with deterministic rules. A background job runner tracks stages and model outcome. YouTube integration is isolated behind an OAuth/API adapter.

## Data, interfaces, and integrations

- A project record stores source path, media metadata, transcript and translations, candidate edits, vertical shorts, contextual horizontal YouTube cuts, local visual-analysis metrics and crop trajectory, approved grade settings, reviewer decisions, exports, and per-asset upload state.
- Each project stores its selected transcription model. The analysis request accepts one allowlisted model (`tiny`, `base`, `small`, `medium`, `large-v3`); this choice overrides the configured default for that analysis.
- Semantic analysis sends the timestamped transcript in the selected source language to the globally selected provider. When visual review is enabled, it attaches up to eight contact-sheet JPEGs with up to 128 timestamp-labeled frames each; the global target is 2–1024 frames (default 8). Suggestions contain intervals, reason, evidence quote, confidence, and model source. The backend rejects invalid intervals, consolidates overlaps, excludes suggested removals from vertical/horizontal candidates, records provider success/failure, and falls back to local heuristic suggestions. The review UI requires manual accept/reject/adjust before export.
- `GET/PUT /api/settings/ai` reports provider availability and persists provider plus the visual frame target. New analyses snapshot provider/model/effort, frame target and image toggle. Codex and OpenCode use separate read-only auth mounts; credentials are not returned by the app.

- Project data and generated media live under a local data directory excluded from Git. Source media is never overwritten. Visual inspection uses local OpenCV face detection and image statistics, plus a conservative screen-like heuristic based on temporal stability, edge density, and small face area. Visual judgment through the selected provider is enabled by default and can be switched off in the UI; from 2 to 1024 reduced frames (default 8) are sampled, resized to 768 px maximum dimension, and composed into JPEG contact sheets of up to 128 tiles with index and timestamp above each frame. At most eight sheets are attached per call. The complete video is never sent, and auth files remain mounted read-only and are never returned. The selected model classifies presentation-dominant content; a positive, low-confidence, or failed scene classification sets `grade_policy=preserve`, neutralizes preview suggestions, disables grade controls, rejects attempts to enable global grading, and prevents FFmpeg `eq` filters even if persisted state is stale. This fail-safe protects slide colors. Accepted crop trajectories are interpolated into FFmpeg frame-evaluated crop expressions after mapping source times through removed intervals. A conservative `eq` correction uses bounded brightness/contrast/saturation suggestions and is disabled until explicitly approved and allowed by the scene policy. Each master/cut render is sampled at start, middle, end, and around edit joins; checks retain dimensions, duration, exposure metrics, and warnings in that export asset.
- YouTube uses OAuth 2.0 for the selected account with `youtube.upload` for videos and `youtube.force-ssl` for native caption insertion. Each approved video is uploaded with `status.privacyStatus=private`, then receives the source-language and all selected destination SRT tracks through `captions.insert`. VTT files remain downloadable sidecars. OAuth tokens remain local and excluded from Git.
- Network use: acquisition of Whisper/Argos packages; the selected provider receives transcript text and, when enabled, up to eight composed contact sheets with up to 128 frames each; YouTube OAuth/upload.

### DEC-018 — Unificar análise generativa em MiMo V2.6 Flash Free via OpenCode
- Status: corrigido pelo usuário em 2026-10-17 para usar o ID completo do catálogo OpenCode.
- Sources: REQ-009, REQ-011, JRN-005, TASK-010/012.
- Decision: usar exclusivamente `opencode/mimo-v2.6-flash-free` via `opencode run` para análise semântica do texto e classificação dos frames. Manter transcrição e tradução local. O OpenCode do host fornece autenticação ao container por arquivo montado somente leitura; o toggle por análise decide somente se frames são anexados. Codex não é chamado.
- Consequences: texto e imagens seguem as condições do provedor configurado no OpenCode; sem CLI/autenticação, a análise não inicia. Erros são registrados sem armazenar resposta bruta/segredos, e as regras locais continuam oferecendo sugestões revisáveis.
- Evidence: modelo listado por `opencode models`; chamadas reais de texto e imagem via OpenCode concluídas com sucesso usando `teste.mp4`; [OpenCode model docs](https://docs.opencode.ai/docs/models/) e [CLI docs](https://docs.opencode.ai/docs/cli/).

### DEC-019 — Exibir progresso da análise por etapas reais
- Status: confirmado pela solicitação do usuário, 2026-10-17.
- Sources: REQ-006, JRN-001, BDD-JRN-001-13, TASK-008, DEC-010.
- Decision: durante `analyzing`, renderizar uma linha do tempo com etapas concluídas, atual e pendentes, derivada de `job.stage`; incluir validação de frames só quando solicitada. Exibir a mensagem atual do backend junto à etapa ativa. A barra resume somente etapas concluídas, sem converter uma etapa longa em porcentagem inventada.
- Consequences: rótulos da interface devem acompanhar os estágios existentes (`visual-analysis`, `visual-review`, `transcribing`, `translating`, `semantic-analysis`); mudanças de etapa são anunciadas para leitores de tela. A consulta periódica deve ignorar cache HTTP e encerrar ao receber estado terminal; reabrir o mesmo projeto deve buscar estado novo. Exportação e upload mantêm seu indicador existente.
- Evidence: API do projeto `[id de projeto local]` retornou `review-ready`/`complete` enquanto a interface mantinha `analyzing`; polling, navegação e cache dos assets corrigidos em 2026-10-17.
- Evidence: fluxo MCP Playwright confirmou a transição de `rendering` para `export-ready`, mostrando 10 ativos e sem exceções JavaScript no clone `[id de projeto local]`.

### DEC-016 — Multimodal scene review and slide-safe grading
- Status: superseded in provider choice by DEC-018; local visual policy remains confirmed, 2026-10-17.
- Sources: REQ-011, BDD-JRN-001-12, TASK-012.
- Decision: local slide/screen heuristics always run. Per-analysis visual review of the globally selected 2–1024 frames (default 8), grouped into contact sheets of up to 128 timestamp-labeled frames, sends at most eight sheets per call by default and can be disabled with a UI toggle; it shares the selected provider with transcript analysis. Frames are sampled around scene transitions with uniform coverage. Presentation-dominant, uncertain, or failed scene classification preserves original colors by disabling global grade. The full recording is never sent.
- Consequences: OpenCode must be installed and authenticated on the host. The project records model/status and decision, but not key or Base64 images.
- Evidence: user request; official [MiMo V2.6 Flash model page](https://mimo.mi.com/models/en-US/mimo-v2.6-flash) and [image-understanding API guide](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/multimodal-understanding/image-understanding).

### DEC-017 — Scene-aware frame extraction based on video-frames-skill
- Status: adopted as an implementation pattern, 2026-10-17.
- Sources: REQ-011, DEC-016, user-provided [video-frames-skill](https://github.com/mugnimaestra/video-frames-skill).
- Decision: use FFmpeg scene-change timestamps when selecting the configured 2–1024 frames (default 8), filling coverage across the video. Keep source frames reduced to 768 px before composing grids of up to 128 timestamp-labeled frames; send up to eight original-color JPEG grids per call.
- Rationale and limits: scene-based sampling helps capture slide changes while a hard frame cap bounds payload and cost. The skill's OCR preset applies grayscale, contrast, and sharpening, which would distort color judgment; its token estimates target Claude/OpenAI/Gemini, not MiMo. Therefore adopt scene selection/resizing principles without installing its CLI as a runtime dependency, and do not apply OCR transforms to frames used for grading decisions.

## Security and quality requirements

- Bind the local service to loopback by default; do not expose it on the LAN.
- Keep OAuth secrets and OpenCode authentication outside tracked files; redact them from logs. Do not log image payloads. The visual review checkbox must disclose frame transfer.
- Require explicit approval before upload. Never set public visibility.
- Disclose transcript and optional frame transfer before analysis. Never send the source video or persist raw provider responses that may contain sensitive content. Mount the OpenCode auth file read-only and keep it outside tracked files. Validate AI output as untrusted data and keep human review mandatory.
- Make processing resumable and track each video/caption upload independently. If the API result is ambiguous, block retries until the user checks YouTube Studio. Preserve source and intermediate outputs on failure.
- Review is the quality gate for ASR, translation, edits, and cuts; no objective accuracy target was established.

## Development and verification

- Proposed MVP stack: Python/FastAPI local backend, vanilla browser UI, FFmpeg/ffprobe, local speech and translation adapters, Docker Compose packaging.
- Current ASR and translation implementation use local CPU inference. The container installs the official CPU-only PyTorch wheel required by the translation stack, avoiding CUDA downloads. Export attempts Intel Quick Sync H.264 encoding when `/dev/dri/renderD128` is available and falls back to libx264; actual device acceleration remains unverified.
- Whisper defaults to the multilingual `medium` model with beam size 5 and prior-text conditioning. `WHISPER_MODEL=small` remains an explicit faster/lower-quality option. The model is downloaded on first run; processing is slower, and terminology/proper names still require human review. A comparison on the 142-second OBS sample corrected repeated “Tolkien” errors to “token” and “chat IPT” to “ChatGPT” in context, but retained errors such as “bogeyman brain”; this is sample evidence, not a general accuracy metric.
- Host execution without Docker may be offered for development; container runtime is the intended packaged path.
- Compose image build and local startup succeeded. Review API accepted the rounded 142.317-second edit against the 142.316667-second source. A medium-model analysis completed with 11 PT-BR/EN segments and regenerated cuts that avoid proposed edit ranges. Export completed with an 118.44-second 1920×1080 master and vertical cuts of 45 and 43.44 seconds at 1080×1920; subtitle timing was mapped to each rendered timeline. YouTube OAuth/API remains unverified.
- Add automated tests for media manifests, edit decisions, caption timing, private upload request construction, OAuth error handling, and retry behavior as part of implementation.

## Delivery and operations

- Single root application; no separate frontend/backend project boundaries unless implementation evidence requires them.
- Local run guide and YouTube OAuth setup guide belong in Diátaxis how-to docs; project data and credentials must be excluded from Git.
- Future observable stages: queued, analyzing, review-ready, rendering, upload-pending, uploading, uploaded, and failed.

## Decisions and rationale

### DEC-001 — Local-first pipeline
- Status: confirmed, with the transcript-only GenAI exception defined in DEC-009
- Sources: REQ-001, REQ-002, JRN-001
- Decision and alternatives: keep source video, transcription, translation, and rendering local; do not send source media to cloud processing. The timestamped transcript is sent to MiMo for semantic review under DEC-018; reduced sampled frames are optional.
- Rationale and consequences: the recording remains private while the creator gets text-aware suggestions; transcript text leaves the local machine for the configured AI services.
- Evidence: user preference and environment inspection.
- MVP implementation and future extension: local adapters, replaceable behind interfaces.

### DEC-002 — Human review gates editorial changes and upload
- Status: confirmed
- Sources: REQ-002, REQ-003, REQ-005, REQ-006, JRN-001, JRN-002
- Decision and alternatives: user reviews suggestions; explicit final action triggers selected uploads.
- Rationale and consequences: human controls content while upload remains automated.
- Evidence: user-selected review flow and private-upload behavior, 2026-10-14.
- MVP implementation and future extension: never make an upload request before approval.

### DEC-003 — YouTube uploads are explicitly private
- Status: confirmed
- Sources: REQ-005, JRN-002
- Decision and alternatives: upload selected assets as private; user later publishes in Studio.
- Rationale and consequences: supports automated upload without unreviewed public release.
- Evidence: user-selected private-for-review behavior; official YouTube Data API allows privacy status in upload resource.
- MVP implementation and future extension: always submit `private`; public visibility feature is excluded.

### DEC-004 — Single local application boundary
- Status: proposed
- Sources: REQ-001 through REQ-006
- Decision and alternatives: one root project, with service, UI, and worker modules rather than separate deployable subprojects.
- Rationale and consequences: keeps local setup simple; boundaries can be revisited if implementation requires it.
- Evidence: empty repository and local single-user workflow.
- MVP implementation and future extension: one root `AGENTS.md` and four mandatory repository files.

### DEC-005 — Best-effort Intel video encoding with CPU fallback
- Status: proposed
- Sources: REQ-001, REQ-004, JRN-001
- Decision and alternatives: try FFmpeg `h264_qsv` when the Intel render device exists; fall back to software `libx264`. Speech recognition remains CPU-based in this MVP.
- Rationale and consequences: uses available Intel Quick Sync for rendering where supported while retaining a portable path. The actual QSV path remains to be validated in the container.
- Evidence: environment inspection and [OpenVINO device deployment guidance](https://docs.openvino.ai/2026/model-server/ovms_demos_audio.html).
- MVP implementation and future extension: Compose maps `/dev/dri`; verify encoder support on the host before claiming acceleration. OpenVINO Whisper remains a future option because the selected segment-based ASR adapter currently uses faster-whisper CPU.

### DEC-006 — Attach caption tracks automatically (superseded by DEC-020/022)
- Status: confirmed
- Sources: REQ-004, REQ-005, JRN-002
- Decision and alternatives: originally attach PT-BR and EN SRT tracks to each selected YouTube video after the approved private video upload; retain VTT files as local downloads. DEC-020 and DEC-022 generalize this to the source language plus all selected destinations.
- Rationale and consequences: automatic caption insertion completes the multilingual publishing package but requires the broader `youtube.force-ssl` scope in addition to `youtube.upload`.
- Evidence: user confirmation on 2026-10-14; [captions.insert API](https://developers.google.com/youtube/v3/docs/captions/insert).
- MVP implementation and future extension: track status and ambiguous outcomes separately per caption language; check YouTube Studio before retrying an unknown result.

### DEC-007 — Prefer transcription quality over speed
- Status: confirmed implementation choice within the local-processing constraint
- Sources: REQ-002, JRN-001, TASK-002; observed PT-BR errors in the supplied OBS recording; [faster-whisper options](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py)
- Decision and alternatives: default to multilingual `medium`, `beam_size=5`, and previous-text conditioning; allow `WHISPER_MODEL=small` for faster CPU processing.
- Rationale and consequences: `medium` is a larger model and takes longer/resources; the transcription remains locally processed and its result still needs review, especially technical terms and names.
- Evidence: comparative small/medium run completed on the supplied 142-second recording; the medium output improved several technical terms but still needs review.
- MVP implementation and future extension: use `WHISPER_MODEL` as the initial default; per-project selection is defined by DEC-008.

### DEC-008 — Select transcription model per project
- Status: confirmed
- Sources: REQ-002, JRN-001, BDD-JRN-001-06; [faster-whisper supported models](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py)
- Decision and alternatives: present `tiny`, `base`, `small`, `medium`, and `large-v3` in the analysis UI; default to `medium`, with `large-v3` as the largest full multilingual model offered.
- Rationale and consequences: creator chooses the time/resource/quality tradeoff when starting analysis. Larger models can require substantially more memory, download bandwidth/storage, and processing time; model downloads persist locally.
- Evidence: new projects store `analysis_model`; all five UI options exist in the installed faster-whisper model list. An isolated route/worker check selected `large-v3`, verified it persisted and reached the transcriber adapter, and confirmed malformed choices return HTTP 422. The real model was not downloaded as part of this routing check.
- MVP implementation and future extension: allow the environment default to preselect a model for new projects; per-project UI selection takes precedence.

### DEC-009 — Orchestrate transcript suggestions with OpenCode and Codex CLIs
- Status: superseded by DEC-018, 2026-10-17
- Sources: REQ-002, REQ-003, REQ-006, JRN-001, BDD-JRN-001-07/08
- Decision and alternatives: the creator selects one semantic provider globally: OpenCode with `openrouter/meta/muse-spark-1.3-contributor` (default) or Codex with `gpt-6-luna` at low reasoning effort. Each analysis captures and invokes exactly one CLI, then backend validates/merges its suggestions with local heuristics. Prompt instructs the selected model to use clearly spoken editorial intent (including relative time references resolvable from total duration) as evidence, but treats transcript content as untrusted data rather than executable instructions; an editorial evidence quote may occur outside its target interval but must match the transcript literally; timestamps remain independently bounded and unresolved intent must not yield invented cuts. No video is sent.
- Evidence: container CLI/model calls returned constrained suggestions for the saved OBS transcript; the worker pipeline also reached `review-ready` with validated intervals and no vertical/removal overlap. The current validation profile is OpenCode only; do not invoke Codex again until the user requests the later test.
- MVP implementation and future extension: install both CLIs in the service image; mount only auth files read-only; execute only the selected CLI in a temporary empty/read-only workspace with a timeout; save only validated structured results and selected-provider status. `GET/PUT /api/settings/ai` reads/writes `ai_provider` in local app settings; the analyze request snapshots this value on the project before the worker starts.

### DEC-010 — Interface de estúdio e configurações globais
- Status: confirmado pela solicitação do usuário, 2026-10-14.
- Fontes: REQ-005/006/007, JRN-001/002/003, TASK-008.
- Decisão: manter FastAPI/JS/CSS e adotar shell global com cabeçalho superior único em todas as rotas. Os links Gravações/Configurações mantêm posição e geometria entre galeria, configurações e projetos; no mobile refluem no topo. A galeria concentra a lista de projetos, sem sidebar. **Nova gravação** abre um `<dialog>` de importação a partir da galeria, projeto ou estado vazio, com input de arquivo visível e dropzone. A abertura do painel independe de `input.click()`/`showPicker()`. Fechar/Escape restauram o foco na ação de origem; cancelar não modifica nem cria projetos. Falhas de upload permanecem visíveis no painel e permitem tentar novamente. Etapas, prévia e abas são montadas simultaneamente no editor. Alternar abas usa `hidden`, preservando os controles e decisões não salvas; configurar YouTube usa `/settings` e não depende de projeto. Há prévia da edição exportada e transcrição editável no idioma de origem, com traduções escolhidas após correções. Durante análise, a linha do tempo informa quais etapas terminaram e qual está em andamento (DEC-019). No editor, uma barra de layout recolhe/mostra a prévia e escolhe largura compacta, equilibrada ou ampla; estado salvo em localStorage, com a largura convertida em limite de altura em telas estreitas (DEC-023).
- Contratos: `GET /api/settings/youtube` retorna apenas estado, URI, visibilidade privada e idiomas; `PUT /api/settings/youtube/client` valida JSON Web Google e URI, limita a 64 KB e salva atomicamente `data/youtube-client-secret.json` com modo 0600; `DELETE /api/settings/youtube/connection` remove somente autorização/estado OAuth locais. As duas mutações bloqueiam durante upload. Cliente salvo pela UI prevalece sobre a configuração por ambiente; token continua global.
- Segurança: respostas nunca incluem client secret/token; URLs de OAuth/token são restritas aos endpoints Google esperados; cliente novo remove autorização antiga. A configuração global não inicia upload nem altera a política privada.
- Verificação: testes isolados com credenciais sintéticas, navegação real em navegador, preservação de campos entre abas e configurações, inspeção visual desktop/mobile e contraste dos tokens. Nenhum modelo de IA é necessário para esta alteração.

### DEC-011 — Biblioteca ampla e organização de projetos
- Status: confirmado pela solicitação do usuário, 2026-10-15.
- Fontes: REQ-008, JRN-004, BDD-JRN-004-01/02/03.
- Decisão: `/` abre uma galeria sem a lista lateral de projetos, mantendo a navegação global; a grade mostra todos os projetos com pesquisa por nome, filtro por status e paginação client-side em 12/24/48 cartões. `/projects/{id}` é a rota do editor. `PUT /api/projects/{id}/name` valida e persiste nomes de até 120 caracteres sem alterar fonte, exportações ou decisões.
- Consequências: a lista completa continua disponível em `GET /api/projects`; página/termo/filtro são estado de apresentação do navegador. Nome atualizado aparece em cartões e editor.

### DEC-012 — Provedor semântico exclusivo
- Status: superseded by DEC-018, 2026-10-17.
- Fontes: REQ-009, JRN-005, BDD-JRN-005-01/02, DEC-009.
- Decisão: persistir `ai_provider` (um enum entre `opencode` e `codex`) em `data/app-settings.json`; OpenCode é padrão. O endpoint `/api/settings/ai` expõe leitura/gravação. A rota de análise captura o valor no início e o worker recebe uma única string de provedor, nunca uma lista.
- Consequências: alterações de configuração valem para novas análises; seletores antigos por ambiente foram removidos para manter uma única fonte de configuração e nunca disparar ambos.

## Scope coverage

| Requirement / journey | Approach / decisions | MVP or future | Gaps |
|---|---|---|---|
| REQ-001 / JRN-001 | local ingestion and FFmpeg validation | MVP | None |
| REQ-002 / JRN-001 | local ASR/translation, deterministic edit rules, OpenCode `opencode/mimo-v2.6-flash-free` semantic analysis, reviewable edit list | MVP | Human review of model suggestions |
| REQ-003 / JRN-001 | reviewable vertical crop candidates | MVP | Exact crop behavior must be configurable |
| REQ-004 / JRN-001/JRN-002 | local export and metadata form | MVP | YouTube metadata limits validated during implementation |
| REQ-005 / JRN-002 | OAuth private video upload and selected-language caption insert | MVP | User must configure OAuth client; live API call still needs validation |
| REQ-006 / JRN-001/JRN-002/JRN-003 | interface responsiva com abas e navegação global | MVP | None |
| REQ-007 / JRN-003 | configurações globais OAuth e token compartilhado, DEC-010 | MVP | Cliente Google Cloud deve ser fornecido pelo usuário |
| REQ-008 / JRN-004 | galeria ampla, filtros/pesquisa/paginação e renomeação, DEC-011 | MVP | None |
| REQ-009 / JRN-005 | modelo fixo OpenCode `opencode/mimo-v2.6-flash-free` para texto/imagem, DEC-018 | MVP | None for model routing; human review remains |
| REQ-010 / JRN-001 | Cortes horizontais completos e exportáveis, DEC-013 | MVP | Human review of candidates |
| REQ-011 / JRN-001 | Análise local de tela/cor, revisão multimodal via OpenCode, crop revisável, grade segura e QC de render, DEC-015/016 | MVP | Human review of visual preview |

## Confirmed decisions, assumptions, and open questions

- Confirmed: local processing, review gate, PT-BR to EN, private YouTube uploads; medium is the accuracy-oriented local transcription default.
- Proposed reversible choices: Python/FastAPI, vanilla JS, FFmpeg, Docker Compose.
- Open prerequisite: user-provided OAuth client setup; app must not include a secret or token.
- Confirmed: automatically upload the source and selected destination caption tracks after video upload; use `youtube.force-ssl` with `youtube.upload`.

### DEC-013 — Cortes horizontais com contexto integral para YouTube
- Status: confirmado pela solicitação do usuário, 2026-10-16.
- Fontes: REQ-010, REQ-002/004/005/006, JRN-001, BDD-JRN-001-11.
- Decisão: a análise semântica retorna até 10 candidatos `youtube_cuts` além dos cortes verticais. Cortes horizontais não têm duração máxima; devem preservar uma explicação completa, da introdução necessária até sua conclusão. A UI permite prévia, ajuste de intervalo/título e aprovação. O backend rejeita intervalos fora da mídia e sobreposição com qualquer remoção sugerida.
- Exportação: cada corte aceito gera MP4 16:9, SRT/VTT no idioma de origem e nos idiomas traduzidos selecionados com timeline relativa ao início do corte e ativo YouTube individualmente selecionável; o título do ativo identifica o vídeo. Upload segue o fluxo privado e requer aprovação existente.
- Consequências: a resposta semântica/schema inclui `youtube_cuts`; projetos armazenam a coleção separadamente de `shorts`; falha MiMo mantém a gravação completa e cortes verticais locais, sem fabricar cortes horizontais.
- Evidência de interface: `youtubeCutsHtml()` renderiza título, intervalo, prévia e controles dos candidatos; sem candidatos, informa que o master permanece disponível. Playwright confirmou dois cartões, duas prévias e controles de intervalo/título no projeto `[id de projeto local]`.

### DEC-015 — Análise visual local e acabamento revisável
- Status: confirmado pela solicitação de adaptar os princípios da skill `video-use`, 2026-10-16.
- Fontes: REQ-011, JRN-001, BDD-JRN-001-12; confirmação de rastreamento com revisão, correção neutra revisável e aplicação em todos os exports.
- Decisão: a análise visual roda localmente com OpenCV e frames amostrados. Detecta rostos para sugerir keyframes de crop horizontal, suaviza/interpola a trajetória durante o render e oferece crop estável como opção; usa também sinais de estabilidade de cena, densidade de arestas e tamanho relativo de rosto para suspeitar de slides/tela compartilhada. O provedor selecionado classifica de 2 a 1024 frames (padrão 8) em pranchas de até 128 quadros, com índice e timestamp acima de cada tile e até oito imagens por chamada; a opção inicia ligada e o toggle pode desligar esse envio sem desligar a análise textual. Mede luminosidade, clipping e saturação; a correção global fica desligada até aprovação e fica bloqueada quando conteúdo de tela domina ou a classificação é incerta. A aba Imagem mostra uma folha local em três momentos, com original preservado quando a política bloqueia a grade. A mesma correção permitida vale para master e cortes. Após cada render, registra dimensão, duração e amostras de exposição em início/meio/fim e em torno de junções.
- Contrato: `GET /api/projects/{id}/visual-preview?intensity=0..1&crop_x=0..1` retorna JPEG derivado localmente dos quadros em 12%, 50% e 88% da fonte. `PUT /api/projects/{id}/review` aceita `shorts[].crop_mode` (`track` ou `steady`), `shorts[].crop_x` e `visual: {grade_enabled: boolean, intensity: number}` em `0..1`; API, controles e render reforçam `grade_policy`. `GET /api/settings/ai` informa estado de CLI/autenticação e modelo fixo; `POST /api/projects/{id}/analyze` aceita `visual_review`, que por padrão é `true`. OpenCode é necessário para iniciar análise generativa mesmo quando o toggle visual está desligado. O estado guarda `visual_analysis` (`metrics`, `framing_confidence`, `crop_track`, `scene_analysis`, `scene_review`, `grade_policy`, `grade_suggestion`) e `color_grade`; cada ativo de vídeo guarda `quality_check`.
- Segurança e limite: a fonte nunca é enviada; transcrição com timestamps sempre é enviada via OpenCode ao modelo fixo; até oito imagens de grade, cada uma com no máximo 128 frames, são anexadas adicionalmente quando o toggle visual está ligado. O arquivo de autenticação OpenCode é montado somente leitura e nunca retornado. A detecção baseada em rosto funciona melhor em talking-head; baixa confiança oferece crop estável e revisão manual. Métricas/classificação automática não substituem inspeção humana de cor, foco ou composição.

### DEC-014 — Usar o ID Muse Spark listado pelo OpenCode instalado
- Status: implementação corrigida após inspeção do CLI, 2026-10-16.
- Fontes: REQ-002/010, DEC-009, inspeção de `opencode models` no container e tentativa autorizada de análise em transcrição OBS.
- Decisão: configurar `openrouter/meta/muse-spark-1.3-contributor`, ID listado pelo OpenCode disponível neste ambiente. O ID anterior `opencode/muse-spark-1.3-contributor-free` não aparece na lista atual.
- Verificação e limitação: o ID listado ainda encerrou com erro categorizado como autenticação/provedor; autenticação precisa ser resolvida antes de confirmar uma execução bem-sucedida. Nenhum conteúdo da credencial foi lido ou registrado.
### DEC-020 — Review source transcript before translating selected languages
- Status: confirmed by user request, 2026-10-17
- Sources: REQ-002, REQ-004, REQ-005, REQ-006, JRN-001, BDD-JRN-001-14, TASK-002
- Decision: analysis stores one transcript in the chosen source language (Portuguese/Brazil by default; English, Spanish, or French can be selected). The creator edits segment text while timestamps and IDs are immutable. Saving edits clears prior translations. Only an explicit translation action generates the chosen destination languages locally from the saved transcript. Export and YouTube attach the source track plus selected destination tracks.
- Consequences: the analysis worker no longer performs translation; translation is a separate background job. Transcript edits do not modify the source recording or segment timing. Missing local Argos language pairs return an actionable error.
- Evidence: implementation and end-to-end OBS validation recorded in TASK-002.

### DEC-021 — Aplicar temas materiais selecionáveis ao estúdio
- Status: confirmado pela solicitação explícita de aplicar `instrument-design` ao sistema e posterior pedido por tema claro e Workshop, 2026-10-17.
- Sources: REQ-006, JRN-001, JRN-003, JRN-004, BDD-JRN-003-04; skill `instrument-design`.
- Decision: manter a stack HTML/CSS/JS e os tokens semânticos globais, oferecendo Graphite (carvão e âmbar), Chalk (papel mineral e vermelhão) e Workshop (papel quente com verde pinho definindo áreas de trabalho). Os três temas mantêm os mesmos componentes e gramática material: corpo fosco, painéis/controles elevados e áreas de leitura rebaixadas. A escolha é global ao app e persistida no `localStorage` deste navegador; nenhuma preferência ou dado de tema é enviada ao backend.
- Implementation contract: construções compartilhadas consomem tokens de superfície e tinta; poços/visores definem tinta principal e secundária próprias, inclusive campos, placeholders, métricas e opções de tradução. Teclas neutras são padrão; sinal fica na ação principal de cada grupo. Abas refluem, expõem estado pressionado e têm painéis alcançáveis pelo teclado. A cascata do CSS original é verificada por estilos computados, sem depender só da declaração de tokens.
- Consequences: todos os estados interativos e contraste precisam funcionar nos três temas; texto informativo segue ≥12 px e controles priorizam alvos de 44 px. `prefers-reduced-motion` reduz animações. A folha global e a seleção em Configurações aplicam o tema antes da primeira pintura quando há preferência salva.
- Evidence: implementation in `app/static/instrument-theme.css`, `app/static/index.html` and `app/static/app.js`; TASK-016 browser checks confirmed theme persistence across settings→project→gallery, active `themes-4` stylesheet, 12 gallery cards, no horizontal overflow at a 312 px viewport (300 px document width), and no console messages. Measured Graphite primary/canvas 15.86:1, ink/panel 9.83:1, signal/body 7.21:1; Chalk ink/canvas 12.03:1, muted/canvas 5.88:1, muted/body 5.04:1, light-theme primary button text at least 4.85:1; Workshop ink/canvas 8.59:1, muted/canvas 5.67:1, muted/body 5.00:1, orange signal/body 5.06:1, primary button text at least 4.85:1. Project review screenshots in Chalk and Workshop were inspected for component hierarchy and selected states. Relevo CSS pode variar entre navegadores e não altera fluxos funcionais. A auditoria TASK-017 corrigiu vazamentos entre temas e registrou a cobertura e os limites em [revisão de interface](interface-review.md).

### DEC-022 — Traduzir legendas em múltiplos idiomas de amplo alcance
- Status: confirmado pela solicitação do usuário, 2026-10-17.
- Sources: REQ-002/004/005/006, JRN-001, BDD-JRN-001-14/16, DEC-020, TASK-015; [YouTube](https://blog.youtube/news-and-events/multi-language-audio/) e [Udemy Business](https://business.udemy.com/multi-language-collection/).
- Decision: após corrigir e salvar a transcrição, permitir selecionar várias faixas de destino na mesma solicitação. A lista inicial de dez idiomas de destino é inglês, espanhol, francês, alemão, hindi, árabe, indonésio, japonês, russo e turco; a faixa de origem permanece sempre incluída e não exige tradução. Esta é uma seleção de cobertura ampla baseada nos idiomas que as plataformas destacam, não um ranking comparável de consumo: elas não publicam uma tabela unificada de visualizações/estudantes por idioma.
- Implementation: tradução continua local via Argos; procurar par direto e, quando não existir, compor uma rota fonte→inglês→destino se ambos os modelos estiverem disponíveis. Gravar cada faixa concluída imediatamente para que uma falha posterior não descarte traduções anteriores. Export SRT/VTT, nomes/códigos de faixas e YouTube `captions.insert` recebem dinamicamente a fonte e todos os destinos concluídos/selecionados.
- Consequences: o download de modelos Argos pode aumentar o tempo e o espaço usados, e disponibilidade/qualidade varia entre pares. Sem rota local, mostrar erro acionável sem perder traduções já concluídas. Adicionar outras línguas ou um ranking quantitativo requer fontes comparáveis e revisão desta decisão.
- Validation evidence (2026-10-17): all ten destination languages completed on the same Portuguese sample through `media.translate_segments` and through one `/translate` request against a disposable project. The live container initially had only PT/EN installed; catalog inspection confirmed PT→EN plus EN→each non-English destination, and the missing packages downloaded on demand. The multi-target job ended `review-ready`, stored all ten codes, returned nonempty text for all, and preserved segment IDs/timestamps. Invalid code `xx` was rejected with HTTP 422. Disposable project removed. This validates package routing and translation job persistence; YouTube upload and professional linguistic review were not performed.


### DEC-023 — Adaptar o espaço entre vídeo e revisão
- Status: confirmado pela solicitação do usuário, 2026-10-17.
- Fontes: REQ-006, JRN-003, BDD-JRN-003-07, TASK-020/021.
- Decisão: oferecer na área do projeto uma ação explícita para recolher/mostrar o vídeo e um seletor de largura compacta, equilibrada ou ampla. Sem preferência salva, a prévia abre compacta. A preferência fica no `localStorage` do navegador. Em telas estreitas o editor continua em coluna única e o seletor controla a altura máxima da prévia; ao recolher o vídeo, a área de trabalho ocupa toda a largura.
- Consequências: a revisão recupera espaço sem perder acesso ao preview; os controles permanecem no topo da área de trabalho, mesmo quando o vídeo está recolhido.

## Extensão técnica para qualidade da análise — 2026-10-26

Fonte: PRD/jornadas rev. 29; [diagnóstico rev. 2](analysis-quality-audit.md); contratos e tarefas no [plano de qualidade rev. 10](../planning/analysis-quality-plan.md). Implementação parcial; execução integral em clone concluída, revisão audiovisual humana do material permanece pendente. DEC-013/015/016/017/019 descrevem o histórico, com substituição limitada aos comportamentos explicitados abaixo.

### DEC-024 — Versionar capacidades e permitir recuperação seletiva
- Status: implementação parcial. Fontes: REQ-006/009/012, JRN-001, BDD-JRN-001-17/21, TASK-022/023.
- Proposta: resultado versionado por etapa/unidade, estados de cobertura, erro tipado, contadores de descartes, orçamento de tentativas, invalidação por revisão e proteção de geração. Compatibilidade aditiva em JSON local; sem novo serviço. Substitui o sucesso agregado como indicação de completude das capacidades.
- BDD-JRN-001-29: na inicialização do servidor único, trabalhos interrompidos saem do estado ocupado, preservam os dados e exibem o motivo; envio de vídeo ou faixa com resultado incerto exige confirmação da ausência no Studio para liberar nova tentativa.

### DEC-025 — Separar áudio, qualidade do ASR e edição editorial
- Status: implementação parcial. Fontes: REQ-002/012, JRN-001, BDD-JRN-001-18/19/20, TASK-024/025.
- Proposta: energia/VAD local para silêncio, palavras/sinais de qualidade para localizar fala, rechecagem local de anomalias e evidência contextual para retake. Similaridade lexical não promove remoção sozinha; citação externa ao alvo somente para intenção editorial explícita. Manter revisão e fonte preservada; parâmetros selecionados em casos anotados.
- Complemento BDD-JRN-001-26 / TASK-025: para comentário editorial explícito posterior e próximo ao alvo, localizar uma única ocorrência literal nas palavras do ASR, desde que a transcrição dos segmentos ainda corresponda a essas palavras. Sugerir o comentário separadamente, ou ampliar o intervalo sobreposto até o fim da citação, sem atravessar a retomada; sem alinhamento único, manter a sugestão original para revisão.
- Complemento BDD-JRN-001-27: sinalizar segmentos de cinco ou mais palavras quando pelo menos 40% dos tempos de palavras são nulos ou negativos; também sinalizar texto com oito ou mais palavras acima de dez palavras por segundo, mesmo sem tempos por palavra. Esses sinais bloqueiam novas remoções semânticas que cruzem o segmento ou citem seu texto. Projetos anteriores recebem aviso calculado na leitura, sem apagar sugestões ou texto. Não inferir que os demais segmentos estão corretos.
- BDD-JRN-001-28: sugestões de silêncio dependem de medições FFmpeg; a cauda começa após o fim reconhecido da fala e o início do silêncio medido, com margem. Ausência de ASR não indica silêncio. Alertas listam falhas por etapa e anomalias; sugestões antigas que cruzem ou citem anomalias recebem aviso.
- Evidência literal comum exige alinhamento temporal: com palavras disponíveis e texto compatível, ao menos metade da citação e três palavras devem sobrepor o intervalo; sem alinhamento confiável, apenas segmentos inteiramente contidos podem comprovar a citação. A exceção de comentário editorial continua sujeita às regras próprias e à revisão.
- Se a transcrição emitir 30 segmentos consecutivos sem avançar ou 100 segmentos em menos de um segundo de áudio, interromper com erro visível em vez de permanecer executando indefinidamente. Essa salvaguarda detecta apenas estagnação temporal extrema.

### DEC-026 — Separar geração de cortes e resolver conflitos na revisão
- Status: implementação parcial. Fontes: REQ-002/003/010/012, JRN-001, BDD-JRN-001-21/22, TASK-026.
- Proposta: mapa global de temas, geração por unidades com contexto, contratos específicos para horizontais/verticais/remoções e validação independente por etapa. Schema horizontal obrigatório. Conflito com remoção pendente é visível; rejeitada não bloqueia; aceita é subtraída e exige integridade do corte. Substitui o descarte por qualquer sobreposição de DEC-013. Não altera modelo fixo ou promete fallback semântico equivalente.

### DEC-027 — Classificar layouts por intervalo e preservar regiões incertas
- Complemento BDD-JRN-001-28: classificações ausentes ou duplicadas são desconhecidas, com estado parcial e cores preservadas. Cada amostra cobre no máximo cinco segundos para cada lado dentro da cena; a UI sinaliza regiões incertas e esclarece quando o limite da execução impede nova tentativa.
- Compatibilidade: quando uma revisão antiga informa menos classificações do que frames enviados e não registra quais faltaram, a UI alerta e o render preserva as cores em todo o vídeo; as escolhas anteriores não são apagadas. Uma nova análise em projeto separado recupera a evidência.
- Status: implementação parcial. Fontes: REQ-011/012, JRN-001, BDD-JRN-001-23, TASK-027/028.
- Proposta: mapa local de layouts, refinamento de transições e frames internos representativos de câmera inicial/final; classificação multimodal por amostra, com cobertura explicitada e propagação apenas em intervalos homogêneos. Quantidade global selecionável de 2–1024 frames por execução (padrão 8), em pranchas de até 128 quadros com timestamp e máximo de oito pranchas por chamada; retomadas descontam frames usados e toggle é preservado. `slides/screen/mixed/unknown` não recebem grade; classificação manual explícita é alternativa local. Substitui booleano e bloqueio globais de DEC-015/016, sem ampliar quota de DEC-017.

### DEC-028 — Compor ajuste de cor em tempo da fonte
- BDD-JRN-001-29: fronteiras de cena não descartam trechos curtos e a renderização só aplica cor a uma única cena de câmera revisável e aprovada. Cenas sem ajustes aprovados não dividem desnecessariamente o export. Em amostra sintética de 2 s com ajuste ativo, o render após a correção manteve 2,0 s; a implementação anterior gerou 1,9 s ao perder uma subdivisão de 0,1 s.
- Status: implementação parcial. Fontes: REQ-004/006/010/011, JRN-001, BDD-JRN-001-24, TASK-028/029/030.
- Proposta: medir e propor exposição/contraste/saturação em câmera por segmento; aprovação individual; mesmos parâmetros/transformação no preview FFmpeg e em todos os exports; interseção em tempo da fonte e remapeamento após remoção. Manter BT.709/faixa quando suportado, validar clipping e transições. Balanço de branco automático, LUT/HDR e correção localizada não incluídos. A avaliação neutra é resultado válido. Converter legado sem habilitar correção automaticamente.

### DEC-029 — Adaptadores OpenCode/Codex e preferência global por execução
- Status: seleção/configuração e uma execução Codex real validadas no container em 2026-10-27; precisão editorial geral segue aberta.
- Fontes: REQ-009/012, JRN-005, BDD-JRN-005-01/02/03, TASK-031/032; [plano de qualidade rev. 10](../planning/analysis-quality-plan.md).
- Decisão implementada: configurações permitem OpenCode `opencode/mimo-v2.6-flash-free` ou Codex CLI `gpt-6-luna` com `model_reasoning_effort="medium"` para texto e imagem. O projeto registra o snapshot do executor; a seleção não troca execuções em andamento e não há fallback implícito.
- Implementação: registro de providers, settings atômicos, parser próprio de eventos JSONL Codex e OpenCode, workspace temporário `read-only`, config/telemetria/perfis pessoais desativados e autenticação copiada temporariamente a partir do arquivo selecionado. Retry usa o provedor original. O container ainda requer build e teste de autenticação real para fechar integração.
- Evidência: testes com runner falso e execução real `gpt-6-luna`/`medium` no clone `[id de projeto local]`; detalhes e limites em [relatório de validação](analysis-reliability-validation.md). Não alterar modelo/esforço ou contratar consumo automaticamente.


### DEC-030 — Entrega incremental e limite da validação audiovisual
- Status: execução integral Codex e UI automatizada validadas em clone em 2026-10-27; anotação/inspeção humana pendentes.
- Fontes: pedido de execução TASK-022–034; REQ-002/003/006/009/010/011/012; BDD-JRN-001-17–30 e BDD-JRN-005-01–03.
- Decisão: manter a fonte original intacta e aplicar correções em código/configuração do serviço; persistir capability status/provider/model/effort; usar silêncio do FFmpeg e citação/estrutura para limitar sugestões; manter cortes YouTube quando cruzam remoções pendentes, com aprovação bloqueada até resolver conflito; classificar cor e aplicar só em trechos de câmera revisáveis; configurar OpenCode ou Codex globalmente.
- Evidência/limite: pipeline integral e resultados estão no [relatório do clone](analysis-reliability-validation.md). A reanálise não alterou o projeto original. A ocorrência “Cloud” não virou remoção, e a cauda de 4,22 s foi detectada. Taxas gerais de falso-positivo/recall, exatidão das câmeras não amostradas, revisão dos 14 cortes candidatos e equivalência preview/export seguem pendentes de avaliação humana.

### DEC-031 — Limite de amostras visuais configurável

- Status: implementado localmente após solicitação do usuário em 2026-10-26.
- Fontes: REQ-011, JRN-001/BDD-JRN-001-25, TASK-033; substitui o teto fixo de oito frames em DEC-017/027.
- Decisão: Configurações persiste uma quantidade-alvo global de 2 a 1024 frames JPEG reduzidos, padrão 8. Cada análise captura seu próprio valor no projeto; seleção e retomada respeitam esse snapshot e limitam o total de frames fonte usados. O serviço os agrupa em mosaicos de até 128 quadros, com índice e timestamp acima de cada tile. Uma chamada envia até oito imagens compostas; toggle desligado mantém zero anexos. Se a mídia tiver menos frames decodificáveis que o alvo, usa os disponíveis.
- Consequências: aumentar o limite envia mais imagens ao provedor e pode alterar consumo/latência; a pessoa escolhe explicitamente o valor. O vídeo integral permanece local.

### DEC-033 — Apresentação compacta de cobertura e alerta de segmentação ASR
- Status: implementado e validado em execução real e Playwright, 2026-10-27.
- Fontes: REQ-002/006/011/012; JRN-001/BDD-JRN-001-27/28/30; TASK-025/030/034.
- Decisão: agregar sequências contíguas de ao menos 12 segmentos com até duas palavras, duração de até 0,65 s e lacunas de até 0,6 s em uma faixa temporal para revisão, sem inferir que o texto esteja errado ou bloqueá-lo automaticamente. Resumir segundos cobertos por slides/tela e áreas desconhecidas, mostrando cartões apenas para intervalos de câmera seguros e ajustáveis.
- Razão: uma execução de `large-v3` gerou 1.998 segmentos, 1.529 em 50 faixas curtas; outra execução da mesma fonte gerou 462 segmentos sem essas faixas. A interface deve expor a variação e manter a revisão navegável sem transformar incerteza amostral em correção de cor.
- Limite: a heurística detecta fragmentação estrutural, não mede precisão da transcrição; o aviso pede conferência humana. Lacunas visuais continuam desconhecidas e não são preenchidas com rótulos extrapolados.

### DEC-034 — Resolver retake com evidência de tentativa, comentário e retomada

- Status: implementada, implantada localmente e validada no caso real; métricas gerais continuam pendentes.
- Fontes: REQ-002/006/012; JRN-001/BDD-JRN-001-26/31; TASK-025/035; caso real do projeto `[id de projeto local]`.
- Decisão: uma chamada semântica focada só é executada quando há indício de comentário editorial. O modelo seleciona IDs de palavras para tentativa descartada, comentário completo e retomada preservada; o backend valida alinhamento, ordem, cobertura das falas no intervalo e anomalias, e calcula os limites. A UI mostra as três evidências em um único cartão pendente.
- Segurança de revisão: ambiguidade, fala intercalada, falta de palavras ou anomalia não geram remoção completa; mostram aviso para revisão. Uma decisão anterior que cobria apenas o comentário é guardada no histórico, enquanto o intervalo ampliado volta a pendente.
- Consequências: schema aditivo em sugestões antigas; sem migração ou alteração de endpoints. O modelo auxiliar usa o mesmo provedor configurado e não substitui a análise/transcrição.
