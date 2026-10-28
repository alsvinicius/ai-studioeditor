# OBS Post Production — PRD

- Status: draft
- Revision: 36
- Revision history: [central log](../revision-history.md#docsproductprdmd)
- Updated: 2026-10-27
- Sources and revisions: conversation decisions on 2026-10-14 through 2026-10-17, including multi-language captions and selectable Chalk/Graphite/Workshop themes; platform language-reach references from [YouTube](https://blog.youtube/news-and-events/multi-language-audio/) and [Udemy Business](https://business.udemy.com/multi-language-collection/); `instrument-design` skill; backend-managed AI analysis (latest model choice: OpenCode `opencode/mimo-v2.6-flash-free`), studio UI/global YouTube configuration, contextual horizontal cuts, local frame previews, screen-aware grading, default-on multimodal review, and scene-aware frame sampling inspired by [video-frames-skill](https://github.com/mugnimaestra/video-frames-skill); [technical environment](../engineering/technical-definition.md)
- Related artifacts: [workflow state](workflow-state.md), [journeys](user-journeys.md), [technical definition](../engineering/technical-definition.md), [implementation plan](../planning/implementation-plan.md)
- Language: Portuguese

## Vision and business need

The user records lessons and video content with OBS and wants to reduce the manual work required to prepare recordings for YouTube and vertical social video. The product turns a local OBS recording into a reviewed edit, multilingual captions, vertical cut suggestions, and a private YouTube upload.

## Users and stakeholders

- Primary user and operator: the creator recording lessons and video content with OBS.
- External service: the user's authorized YouTube channel.

## Expected deliverables and success measures

- A local app that takes a recording through review, export, and approved private YouTube upload.
- Success criterion: complete one real recording from OBS input through reviewed output and private upload.
- Editing-time reduction is not yet measured; collect a baseline during the first pilot before setting a target.

## Scope, exclusions, and provisional MVP

- Include local ingestion of MKV/MP4, selectable source-language transcription, corrected transcript review, and explicitly selected subtitle translations, conservative rule-based and GenAI edit suggestions, review UI, vertical and contextual horizontal YouTube cut suggestions, export, YouTube metadata suggestions, approved private upload, and global YouTube configuration.
- Exclude automatic public publication, sending the full source video for cloud processing, and direct posting to non-YouTube social platforms. Text analysis sends the timestamped transcript to the selected provider; optional visual review may additionally send the globally configured number of sampled, reduced JPEG frames when enabled for an analysis.

## Requirements

### REQ-001 — Process an OBS recording locally
- Need and desired behavior: import an MKV or MP4 recording and analyze it without uploading source media to a processing service.
- Priority and rationale: MVP; privacy and core input.
- Acceptance criteria: source is preserved; invalid media and missing audio are surfaced with actionable errors.
- Source: user request and local-processing selection, 2026-10-14.

### REQ-002 — Prepare conservative edits and multilingual captions
- Need and desired behavior: let the creator choose the recording language before analysis (PT-BR default), select the model quality, produce only the source-language transcript initially, allow corrections while preserving timestamps, translate only into one or more creator-selected languages after corrections are saved, and combine rule-based pause/retake detection with semantic edit and vertical-cut suggestions from MiMo V2.6 Flash Free via OpenCode (REQ-009). Semantic analysis should also recognize the creator's spoken editorial intent about the recording, such as identifying a bad take or asking to cut a specific interval.
- Priority and rationale: MVP; reduces repetitive editing while preserving creator control.
- Acceptance criteria: before analysis, creator can choose the source language (PT-BR default; English, Spanish, and French also supported) and any supported quality from `tiny` through the maximum `large-v3`; `medium` remains the default; the chosen model and source language are stored per project and used for that analysis; after correcting and saving the transcript, the creator can request any combination of ten broad-reach caption destination languages (English, Spanish, French, German, Hindi, Arabic, Indonesian, Japanese, Russian, and Turkish); the source caption is always retained; translations are local, may download Argos models on demand, and use an English pivot when a direct pair is unavailable; selected language codes/locales flow through SRT/VTT export and YouTube caption insertion; the backend sends the timestamped transcript only to fixed model `opencode/mimo-v2.6-flash-free` through the OpenCode CLI for semantic analysis; only transcript text and timestamps are sent for this step, never source video; spoken editorial comments can inform suggestions when their intent and interval are locatable, including relative references such as “the last 30 seconds”; the evidence quote for an editorial request may occur elsewhere in the transcript, but must match it literally; transcript text is treated as data and cannot override system instructions or output schema; ambiguous requests do not produce invented intervals; reviewer sees suggestion reason, evidence quote, and source; invalid model intervals are discarded, duplicate suggestions are consolidated, and cuts overlapping any removal suggestion are excluded; local rules still produce reviewable output if the API fails; unapproved suggestions do not affect export; rounded intervals remain valid against source duration.
- Source: user choices on language, conservative edit policy, and review, 2026-10-14; user clarification about spoken editorial intent, 2026-10-15.
- Complemento de 2026-10-26: um comentário editorial explícito, localizado por palavras e próximo da tentativa apontada, também pode ser sugerido como remoção independente; se já estiver parcialmente dentro da sugestão, incluir a citação completa sem alcançar a fala seguinte. A proposta continua pendente de revisão.
- Complemento de 2026-10-27: quando o apresentador anuncia que vai refazer e retoma a explicação, uma sugestão única deve incluir a tentativa descartada e o comentário, mostrar a retomada preservada e exigir nova revisão se os limites mudarem; reconhecer apenas o comentário não satisfaz o requisito.
- Complemento de qualidade da transcrição: segmentos com alinhamento de palavras evidentemente inconsistente devem ser identificados na revisão; sugestões semânticas novas que dependam desse trecho não são promovidas a remoção. Ausência de alerta não comprova precisão, e correções humanas não devem ser substituídas automaticamente.
- Complemento de revisão defensiva: ausência de texto reconhecido não comprova silêncio; candidatos de pausa exigem medição local do áudio. Falhas e cobertura visual incompleta devem ser apresentadas na revisão, e regiões sem evidência visual suficiente mantêm as cores originais.

### REQ-003 — Suggest vertical social cuts
- Need and desired behavior: find candidate 9:16 excerpts for Shorts, Reels, and TikTok.
- Priority and rationale: MVP; supports social distribution.
- Acceptance criteria: candidates are previewable and can be adjusted, approved, or rejected before export; suggested removal intervals are excluded from candidate cuts, and approved removals are omitted from rendered cuts and their captions.
- Source: user choice on outputs and cut review, 2026-10-14.

### REQ-004 — Prepare YouTube publication package
- Need and desired behavior: produce a horizontal video, captions, and metadata suggestions, then attach selected-language subtitle tracks to each selected YouTube video.
- Priority and rationale: MVP; complete YouTube preparation.
- Acceptance criteria: export includes video, source-language plus every selected-translation SRT/VTT file, and editable title/description/chapters; after approval, selected videos receive native caption tracks for the source language and each selected translation.
- Source: user request, 2026-10-14.

### REQ-005 — Upload approved YouTube assets privately
- Need and desired behavior: after explicit review approval, upload selected YouTube assets automatically as private.
- Priority and rationale: MVP; avoids repetitive manual upload while preserving a private review boundary.
- Acceptance criteria: no upload occurs before the approval action; every video upload request sets `privacyStatus=private`; each selected video receives the source-language track and all selected translation tracks; app reports per-video and per-caption success/failure; public release remains manual in YouTube Studio.
- Source: user request and visibility selection, 2026-10-14; official YouTube upload docs.

### REQ-006 — Review locally before export and upload
- Need and desired behavior: review video, transcript, translations, edit suggestions, and cuts in a local browser UI.
- Priority and rationale: MVP; editorial control and explicit upload approval.
- Acceptance criteria: accepted/rejected/adjusted decisions are persisted with the project and drive export/upload. A interface usa um menu superior global consistente em galeria, configurações e projetos, sem converter a navegação em barra lateral ao mudar de rota. Em telas estreitas o menu reflui no topo. A ação **Nova gravação** abre um painel visível de importação na galeria e no projeto, com input de arquivo visível e arrastar e soltar; na biblioteca vazia, a ação equivalente usa o mesmo seletor. Cancelar não altera o projeto atual nem cria um projeto vazio. A interface usa etapas visíveis e abas de edição, cortes, legendas e publicação; cortes horizontais têm prévia, ajuste de título/intervalo e decisão. A prévia fica ao lado da revisão em telas amplas e o conteúdo se adapta a celulares. No editor, a pessoa pode recolher/mostrar a prévia e escolher largura compacta (padrão inicial), equilibrada ou ampla; a preferência permanece neste navegador. Em telas estreitas, a escolha controla a altura do vídeo e a revisão mantém a largura disponível. Durante análise e exportação, a pessoa vê o estado em andamento e a tela muda para revisão/publicação ao receber estado terminal atualizado. Erros de renderização não são tratados como projeto inexistente. Trocar abas ou visitar configurações preserva alterações ainda não salvas. Todas as rotas oferecem três temas materiais com a mesma hierarquia e componentes: Graphite (carvão e âmbar), Chalk claro (papel mineral e vermelhão) e Workshop (papel quente com verde pinho em superfícies de trabalho). O tema escolhido permanece neste navegador. Cada tema mantém contraste legível, superfícies foscas, módulos/teclas elevados, áreas de leitura rebaixadas e estados acessíveis de foco, seleção, processamento e desativação. Tipografia informativa permanece legível em desktop e mobile.
- Source: user choice on review interface, 2026-10-14.

### REQ-007 — Configurar o YouTube globalmente
- Necessidade: configurar a credencial OAuth e a conexão do canal em uma página global, acessível sem abrir um projeto.
- Prioridade: MVP; elimina a repetição da configuração por gravação.
- Critérios de aceite: `/settings` permite importar um JSON OAuth Web, visualizar URI e estado de conexão, conectar/reconectar e desconectar; configuração e autorização valem para todos os projetos. Credenciais ficam apenas no armazenamento local com permissão restrita e nunca são retornadas pela API. Trocar o cliente invalida a autorização anterior. Alterações na conexão são bloqueadas durante um upload. Metadados e seleção de ativos continuam por projeto; envio depende da aprovação do projeto.
- Fonte: solicitação do usuário para modernizar UI/UX e globalizar a configuração YouTube, 2026-10-14.

### REQ-008 — Organizar a biblioteca de gravações
- Necessidade: ver todos os projetos numa galeria ampla, localizar gravações e renomear projetos.
- Prioridade: MVP; facilita a navegação à medida que a biblioteca cresce.
- Critérios de aceite: clicar em **Gravações** abre uma galeria em toda a área de conteúdo com todos os projetos; pesquisa por nome, filtro por status e paginação (12/24/48) funcionam; abrir um cartão leva ao projeto; renomear persiste e atualiza o nome mostrado na biblioteca e no editor sem alterar a mídia fonte.
- Fonte: solicitação do usuário, 2026-10-15.

### REQ-009 — Selecionar OpenCode ou Codex para as análises
- Status: requisito confirmado e seletor/persistência implementados; integração real do Codex pendente de validação.
- Necessidade: escolher nas configurações globais entre OpenCode com `opencode/mimo-v2.6-flash-free` e Codex CLI com `gpt-6-luna`, esforço `medium`, para texto e revisão multimodal.
- Prioridade: extensão do processo de análise; remove a exclusividade anterior do OpenCode.
- Critérios de aceite: escolha persiste; instalação existente mantém OpenCode como padrão de migração; modelo/esforço explícitos por opção; análise registra snapshot do executor/modelo/esforço e usa-o em texto e imagens. Selecionar Codex não exige OpenCode. Alteração global não muda execução ativa ou histórico; retomada mantém snapshot, troca exige nova execução explícita. Sem fallback silencioso. Mostrar disponibilidade e orientação de autenticação do executor escolhido, sem expor credenciais; preservar limite visual ajustável de 2–1024 frames (padrão 8) com toggle, processamento local de áudio/vídeo/transcrição/tradução e revisão humana. Consumo segue a conta configurada, sem compra automática.
- Fonte: pedido do usuário em 2026-10-26; substitui a exclusão de Codex confirmada em 2026-10-17. DEC-029, JRN-005, TASK-031/032.

## Business constraints and risks

- Source media, transcription and caption translation remain local; semantic review sends the source-language transcript and timestamps to the selected OpenCode/MiMo or Codex/GPT-6 Luna executor. If enabled, visual review additionally sends up to eight contact sheets with up to 128 timestamp-labeled frames each (global frame target 2–1024, default 8). Network access also supports provider requests, local-model acquisition and YouTube upload/authentication.
- YouTube OAuth client setup and account authorization are required before upload can work. Caption insertion additionally requires the `youtube.force-ssl` OAuth scope, alongside `youtube.upload`.
- The inspected host is Ubuntu Linux with Intel Iris Xe, 19 GiB RAM, Docker CLI installed and an active Docker daemon for the pilot. FFmpeg is not installed on the host.
- Automated transcript translation and edit suggestions require human review for quality.

### REQ-010 — Suggest contextual horizontal YouTube cuts
- Need and desired behavior: suggest separate 16:9 videos for YouTube from the recording transcript, preserving each explanation's full context from its necessary introduction through its conclusion.
- Priority and rationale: MVP; turns long lessons into complete standalone YouTube videos.
- Acceptance criteria: suggestions are transcript-based, have no maximum duration, include enough context to understand the topic from beginning to end, are previewable and adjustable, and require approval before export. Overlap with a pending/accepted removal is shown as a conflict and blocks approval until the edit is resolved; accepted removals are omitted from exported video and caption timelines. Each accepted cut exports as an individual horizontal video with source-language and selected translation captions and can be selected independently for private YouTube upload.
- Source: user request, 2026-10-16.

### REQ-011 — Analisar enquadramento e corrigir imagem com revisão
- Necessidade: melhorar o enquadramento 9:16, sugerir uma correção neutra de exposição/cor e conferir os renders antes da publicação.
- Prioridade e justificativa: MVP; reduz correções manuais e evita publicar verticais mal enquadrados ou exports com problemas visuais evidentes.
- Critérios de aceite: análise visual local sugere uma trajetória de crop para cortes verticais e informa confiança; a pessoa pode revisar o rastreamento ou escolher crop estável; uma folha de contato local compara original, correção sugerida e recorte 9:16 em três momentos do vídeo, e permite ajustar a intensidade e a posição do crop na prévia; correção neutra exige aprovação explícita antes de exportar; quando aprovada, vale para master e cortes horizontais/verticais. Cenas de câmera recebem sugestão, prévia e aprovação independentes; slides, cenas mistas/desconhecidas e falhas preservam as cores originais. A pessoa ajusta intensidade por cena; uma proposta neutra é válida. A validação multimodal usa o provedor escolhido para análise de texto e começa ligada, podendo ser desligada por gravação. Nas Configurações globais, a pessoa escolhe de 2 a 1024 frames reduzidos por execução (padrão 8). O serviço compõe pranchas de até 128 quadros; índice e timestamp aparecem acima de cada quadro, com até oito pranchas enviadas por chamada. O valor fica registrado ao iniciar cada análise. O vídeo completo nunca é enviado. Cada render tem checagem de dimensões, duração, amostras visuais e transições de corte com avisos recuperáveis.
- Fonte: solicitação do usuário sobre a skill `video-use`, exemplos de gravação com slides e pedido de avaliação multimodal MiMo e de ativá-la por padrão com toggle, 2026-10-17.

## Confirmed decisions, assumptions, and open questions

- Confirmed: default source language PT-BR; creator can select Portuguese (Brazil), English, Spanish, or French; translations are explicitly selected and generated only after transcript corrections are saved; selectable local transcription quality from `tiny` to `large-v3`, defaulting to `medium`; conservative edit suggestions; local review; vertical cut suggestions; YouTube upload after approval as private; public release manual.
- Confirmed: the global settings allow `opencode/mimo-v2.6-flash-free` or Codex `gpt-6-luna`/`medium` for transcript and optional frame analysis; transcription and caption translation remain local. Live Codex execution is not yet validated.
- Confirmed: MVP success is one real end-to-end recording; editing-time baseline is collected during pilot before defining a numeric target.
- Confirmed initially: upload PT-BR and EN YouTube caption tracks automatically after review approval; expanded by the 2026-10-17 multi-language caption request to upload the source track and all selected translations. This uses the broader `youtube.force-ssl` scope.
- Assumption: the creator is the only MVP user and operates one authorized channel at a time.
- Open: YouTube OAuth client credentials must be supplied/configured by the user before live upload; no credential values should be committed.

## Extensão proposta — qualidade da análise (2026-10-26)

Fonte: relato do criador sobre o projeto `[id de projeto local]` e [diagnóstico rev. 2](../engineering/analysis-quality-audit.md). Resultado solicitado confirmado; mecanismos foram implementados parcialmente conforme o [plano de qualidade rev. 10](../planning/analysis-quality-plan.md). O comportamento implementado anterior permanece descrito acima.

- **REQ-002 — complemento implementado em parte:** silêncio deve ter evidência no áudio, incluindo cauda inferior ao antigo limiar de 3 s; repetição textual/artefato ASR não basta para propor apagar vídeo; preservar enumerações e pausas didáticas. Erros suspeitos de transcrição têm revisão separada. Margens preservam a última fala.
- **REQ-003/010 — regra de conflito implementada:** sugestões de remoção pendentes sinalizam conflito revisável em vez de eliminar cortes; rejeitadas não bloqueiam; aceitas são removidas junto às legendas. Revalidar contexto após edição interna antes de aprovar o corte. Esta proposta substitui a exclusão de toda sobreposição somente quando implementada.
- **REQ-010 — complemento implementado em parte:** gerar unidades temáticas completas com começo/conclusão sustentados pela transcrição; distinguir ausência legítima, candidatos descartados e falha de geração; permitir retomar etapa sem retranscrever.
- **REQ-011 — complemento implementado em parte:** avaliar câmera inicial/final separadamente dos slides; aprovação, intensidade e prévia por intervalo; slides, mistos e desconhecidos preservam cores. A avaliação pode concluir que nenhum ajuste é necessário. Limite de frames reduzidos configurável de 2–1024 (padrão 8) e toggle por execução; o usuário escolhe o volume transmitido.

### REQ-012 — Explicar cobertura e recuperar etapas da análise
- Status: necessidade derivada dos problemas relatados; estado por capacidade e retomada manual implementados parcialmente.
- Necessidade: saber quais resultados estão completos, parciais ou indisponíveis, e retomar somente a etapa falha sem perder trabalho de revisão.
- Prioridade: correção central do fluxo de análise, independente do piloto OAuth.
- Critérios de aceite: falha não equivale a lista vazia válida; estados por capacidade e motivos recuperáveis; resultados válidos persistidos; no máximo uma retomada manual por capacidade; revisão e traduções preservadas; resultados dependentes desatualizados identificados; execução concorrente não sobrescreve geração vigente. Metas de qualidade são validadas nos casos anotados, sem afirmar percentuais ainda não medidos.
- A revisão também resume longas sequências de segmentos ASR muito curtos por faixa temporal e resume cobertura de slides/áreas incertas; só cenas de câmera classificadas com segurança mostram controles de cor.
- Fontes: pedidos de 2026-10-26/27, diagnóstico rev. 2; JRN-001; DEC-024–034; TASK-022–035.

## Reconciliação de provedor — 2026-10-26

As referências anteriores descrevem a implementação histórica. O seletor atual permite OpenCode ou Codex; a execução registra provedor/modelo/esforço. Codex usa workspace temporário isolado e configuração explícita. A integração real com autenticação/modelo ainda depende de validação no container. Plano de qualidade rev. 3.
