# OBS Post Production — User journeys

- Status: draft
- Revision: 36
- Revision history: [central log](../revision-history.md#docsproductuser-journeysmd)
- Updated: 2026-10-27
- Sources and revisions: [PRD revision 36](prd.md)
- Related artifacts: [workflow state](workflow-state.md), [technical definition](../engineering/technical-definition.md)
- Language: Portuguese

## Personas and context

The creator records lessons or video content in OBS and wants to review a prepared edit before sending selected output to their YouTube channel.

## Journeys

### JRN-001 — Prepare and review a recording
- Requirements: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-011
- Actor, trigger, prerequisites: creator; starts after an OBS recording is complete; recording is available as MKV or MP4.
- Outcome: creator has corrected the source-language transcript, generated selected translations, reviewed an edit, and selected vertical or contextual horizontal cuts.
- MVP inclusion and rationale: included; core product outcome.

| Step | User intent/input/action | Observable response | Business rules | Acceptance criteria |
|---|---|---|---|---|
| 1 | Select a recording | App validates and opens a project | Original file remains unchanged | Valid file starts analysis; invalid file gets a useful error |
| 2 | Select recording language and transcription quality, then start analysis | App stores both choices and shows loading/progress | PT-BR is the default; larger models may need more time, memory, and download | The selected language/model are used for this analysis and remain associated with the project |
| 3 | Wait for analysis | App shows a timeline of completed, current, and pending stages, plus the current operation | Timestamped transcript text always goes through OpenCode using `opencode/mimo-v2.6-flash-free`; image review begins enabled and can be switched off for this run. Up to 8 reduced JPEG samples are selected around scene transitions with uniform coverage. Spoken editorial intent remains untrusted data | Stage states follow backend job stages; skipped optional image review is omitted; long-running steps are not shown with fabricated continuous progress |
| 4 | Correct source-language transcript, then choose destination languages | App allows text corrections without changing segment times; translations run only after explicit request | Corrections invalidate previous translations | Only selected languages are generated from the corrected transcript |
| 5 | Review transcript and edits | App shows each suggestion's reason, supporting quote, source model/rules, and preview; creator can accept, reject, or adjust | Unapproved edits are excluded; model suggestions are advisory | Decisions are reflected in final preview |
| 6 | Review vertical and horizontal candidates | App presents 9:16 social cuts and complete-context 16:9 YouTube cuts, with previews and editable intervals | Horizontal cuts have no maximum duration and preserve the idea from introduction through conclusion; suggested removals are excluded | No suggested removal appears in a selected cut; horizontal exports retain their source aspect ratio and full contextual span |
| 7 | Review image and framing, then approve export | App shows a filtered preview, correction controls, face tracking or stable framing, and render-check results | Color correction requires explicit approval and applies consistently to all video exports | Crop/color decisions persist; exports match expected format/duration and quality warnings are visible |
| 8 | Approve export | App renders selected outputs and captions | Outputs use the saved review decisions | Export files are playable and captions are available as SRT/VTT |

#### Exception and recovery paths

- Invalid or unsupported media: explain the problem and preserve the source.
- Missing audio: stop transcription and explain how to provide a recording with audio.
- Processing interruption: preserve project decisions and allow retry from the last completed stage.
- Reviewer rejects all cuts: export the horizontal master without vertical cuts.

#### BDD scenarios

- **BDD-JRN-001-01 — Valid OBS recording reaches review**
  - Given a readable MKV or MP4 with audio
  - When the creator starts a project and analysis completes
  - Then the app shows the video, editable transcript in the selected source language, and edit suggestions; no translation exists until requested
  - Traceability: REQ-001, REQ-002, REQ-006
- **BDD-JRN-001-02 — Rejected edit is excluded**
  - Given an edit suggestion in review
  - When the creator rejects it and exports
  - Then the exported video retains that source interval
  - Traceability: REQ-002, REQ-006
- **BDD-JRN-001-03 — Invalid recording is recoverable**
  - Given an unsupported or unreadable file
  - When the creator imports it
  - Then the app explains the issue and does not modify the source
  - Traceability: REQ-001
- **BDD-JRN-001-13 — Analysis timeline explains progress**
  - Given an analysis job is queued or running
  - When its backend stage changes
  - Then the UI marks completed stages, the current stage, and pending stages; an optional image review disabled for that run is not shown as pending
  - And when the backend reaches a terminal state, fresh project data replaces the progress view with review or the actionable error state
  - And after export finishes, the publish view shows saved assets instead of the rendering state
  - Traceability: REQ-006, DEC-019
- **BDD-JRN-001-15 — Import and review flow renders horizontal cuts**
  - Given the creator selects a valid MP4 through the file input
  - When import, analysis, transcript correction, selected translation, review, and export finish
  - Then the project reaches publication with playable approved outputs and source/translated SRT/VTT; any available horizontal cut renders its title, interval, and preview controls without a client exception
  - And cancelling the file picker creates no empty project
  - Traceability: REQ-001, REQ-002, REQ-004, REQ-006, REQ-010, DEC-013, DEC-019
- **BDD-JRN-001-04 — Rounded end interval is accepted**
  - Given a media duration with more precision than the review UI displays
  - When the creator saves an interval rounded to milliseconds
  - Then the decision is clamped to the source duration and saved
  - Traceability: REQ-002, REQ-006
- **BDD-JRN-001-05 — Removed source interval is absent from vertical output**
  - Given a vertical candidate intersects a suggested or accepted removal
  - When candidates are generated or the candidate is rendered
  - Then suggested removals are excluded from candidates and accepted removals are absent from video and caption timing
  - Traceability: REQ-002, REQ-003, REQ-006
- **BDD-JRN-001-06 — Selected transcription model is used**
  - Given an imported recording and a supported model choice
  - When the creator selects a model, such as `large-v3`, and starts analysis
  - Then the project saves that selection and runs transcription with that model
  - Traceability: REQ-002, REQ-006
- **BDD-JRN-001-14 — Correct transcript before selected translations**
  - Given an analysis-ready recording with a source-language transcript
  - When the creator edits and saves segment text, then selects one or more destination languages and requests translation
  - Then translations reflect the saved text, source timestamps remain unchanged, and only the selected languages are generated
  - Traceability: REQ-002, REQ-006
- **BDD-JRN-001-16 — Generate several broad-reach caption languages together**
  - Given a saved, corrected source transcript
  - When the creator selects multiple destination languages from the ten-language list and requests translation
  - Then each selected language is translated locally, appears as a separate SRT/VTT track, and is included with the source track in the selected YouTube uploads
  - And an unavailable direct translation pair uses the local English pivot when both model directions exist; otherwise the app reports the unsupported pair and preserves completed translations
  - Traceability: REQ-002, REQ-004, REQ-005, REQ-006, DEC-020, DEC-022
- **BDD-JRN-001-07 — Semantic analysis is transcript-only and reviewable**
  - Given a transcript in the selected source language and authenticated OpenCode CLI
  - When analysis completes
  - Then the backend stores validated suggestions with source and evidence, excludes suggested removals from vertical cuts, and requires human review before export; only the source-language transcript exists
  - Traceability: REQ-002, REQ-003, REQ-006
- **BDD-JRN-001-08 — Local rules survive an OpenCode failure**
  - Given the OpenCode model request fails or times out
  - When analysis completes
  - Then the app records the model status and still returns suggestions from local rules
  - Traceability: REQ-002, REQ-006
- **BDD-JRN-001-10 — Spoken edit intent becomes a reviewable suggestion**
  - Given a transcript that clearly says the last 30 seconds were poor and asks to cut them
  - When semantic analysis completes for a recording with known duration
  - Then the model may suggest the matching final interval and quote the request wherever it occurs in the transcript; transcript text cannot override system instructions, and no cut is invented when the request cannot be located confidently
  - Traceability: REQ-002, REQ-006

- **BDD-JRN-001-11 — Contextual horizontal YouTube cut is reviewed and exported**
  - Given transcript passages that form complete explanations of any duration
  - When semantic analysis suggests horizontal cuts and the creator accepts one
  - Then the export contains an individual 16:9 video with source-language and selected-translation captions spanning its full context, and the asset can be selected for private YouTube upload
  - Traceability: REQ-002, REQ-004, REQ-005, REQ-006, REQ-010

- **BDD-JRN-001-12 — Visual review tracks framing and checks exports locally**
  - Given a recording with reviewable vertical cuts, including a slide presentation with a small webcam overlay
  - When local analysis finishes, the creator reviews framing/color and exports
  - Then the creator can compare original, suggested grade, and 9:16 crop at three video moments; adjust preview intensity and crop position; choose tracked or stable framing; leave default-on MiMo review enabled or switch it off; sampled frames prioritize scene transitions; see slides/screen-share warnings that block global grading; explicitly enable a conservative grade only when allowed; and see local dimension/duration/exposure checks for every video asset. MiMo is on by default when configured, can be switched off per run, and receives at most 8 reduced JPEG frames, never the full video
  - Traceability: REQ-001, REQ-003, REQ-004, REQ-006, REQ-011

### JRN-002 — Upload reviewed assets privately
- Requirements: REQ-004, REQ-005, REQ-006
- Actor, trigger, prerequisites: creator; exports are ready; YouTube OAuth is authorized.
- Outcome: selected videos are available on the authorized channel with private visibility and have source-language and selected-translation caption tracks.
- MVP inclusion and rationale: included; closes the reviewed publishing workflow.

| Step | User intent/input/action | Observable response | Business rules | Acceptance criteria |
|---|---|---|---|---|
| 1 | Review title, description, chapters, and selected assets | App shows editable metadata and upload selection | Only selected YouTube assets upload | Changes are persisted before approval |
| 2 | Approve and send | App uploads selected videos as private, then adds source-language and selected-translation caption tracks | Approval is required; privacy is always explicit | No upload starts before approval; video and caption states are shown separately |
| 3 | Handle result | App shows YouTube links, caption-track status, or actionable error | Retry must not silently duplicate video or caption uploads | Video and each language track have tracked results |
| 4 | Publish publicly later | Creator uses YouTube Studio | App does not change visibility to public | Public visibility is never set by MVP |

#### Exception and recovery paths

- OAuth denied or expired: show that authorization is needed and provide a retry path.
- Network interruption: retain upload state and resume or report the result without an untracked duplicate.
- API rejection/quota issue: preserve exports and metadata so user can retry after resolution.
- Caption upload result is unknown: check the caption tracks in YouTube Studio before retrying; the app blocks ambiguous repeats.

#### BDD scenarios

- **BDD-JRN-002-01 — Approved asset uploads privately**
  - Given an authorized YouTube account and selected export
  - When the creator approves and sends
  - Then the app uploads with private visibility, attaches the source-language and selected destination caption tracks, and shows the resulting video link
  - Traceability: REQ-005, REQ-006
- **BDD-JRN-002-02 — No upload before review approval**
  - Given selected assets and no approval action
  - When the project is opened or exported
  - Then no YouTube upload request is sent
  - Traceability: REQ-005, REQ-006
- **BDD-JRN-002-04 — Selected video receives selected-language captions**
  - Given an authorized account and selected video with source-language and selected-translation SRT files
  - When upload completes
  - Then the video has the source-language track and each selected translation track
  - Traceability: REQ-004, REQ-005
- **BDD-JRN-002-03 — OAuth failure preserves deliverables**
  - Given exports are ready and OAuth is denied or expired
  - When upload is attempted
  - Then exports remain available and the app explains how to authorize and retry
  - Traceability: REQ-005

### JRN-003 — Configurar o canal para todo o estúdio
- Requisitos: REQ-005, REQ-006, REQ-007.
- Ator: criador, com ou sem projeto aberto.
- Fluxo: acessar **Configurações** na navegação global; importar o JSON OAuth Web; copiar/conferir o URI de redirecionamento; conectar a conta na nova aba; retornar ao estúdio e verificar o estado global. O projeto apresenta um link para configurações e mantém os próprios metadados de publicação.
- Recuperação: JSON inválido não substitui a credencial existente; conexão pode ser refeita; desconexão remove a autorização local de todos os projetos; upload em curso bloqueia alterações de conexão.
- **BDD-JRN-003-01**: dado que nenhum projeto está aberto, acessar `/settings` apresenta o estado global e a configuração OAuth.
- **BDD-JRN-003-02**: dado um cliente OAuth Web válido, importar salva a credencial restrita e habilita conexão global; o JSON/segredo não é devolvido.
- **BDD-JRN-003-03**: dado um upload em andamento, trocar cliente ou desconectar recebe erro recuperável sem interromper o envio.
- **BDD-JRN-001-09**: alterar seleções/títulos, trocar abas e visitar configurações preserva os campos da revisão; salvar persiste inclusive as decisões nas abas ocultas.
- Critérios de interface: teclado acessa navegação, abas e campos; telas amplas usam prévia/revisão em paralelo; telas menores empilham as áreas sem rolagem horizontal. Galeria, editor e configurações compartilham a linguagem material selecionada: Graphite, Chalk ou Workshop, com a mesma hierarquia, módulos separados, foco visível e texto/controles legíveis.
- **BDD-JRN-003-04 — Escolher e manter tema visual**: dado que a pessoa escolhe Graphite, Chalk ou Workshop em Configurações, quando navega entre galeria, projeto e configurações ou recarrega a página, então o tema escolhido permanece ativo e todos os fluxos mantêm componentes e conteúdo legíveis. Traceabilidade: REQ-006, DEC-021, TASK-016.

- **BDD-JRN-003-05 — Navegação superior consistente**: dado que a pessoa acessa galeria, configurações ou projeto, quando alterna pelo menu, volta no histórico ou recarrega uma rota diretamente, então os links Gravações e Configurações permanecem no mesmo cabeçalho superior, com o destino atual identificado. Em telas estreitas o cabeçalho reflui no topo, sem navegação lateral ou overflow horizontal. Traceabilidade: REQ-006/007/008, DEC-010, TASK-018.
- **BDD-JRN-003-06 — Iniciar uma nova gravação**: dado que a pessoa está na galeria ou num projeto, quando aciona **Nova gravação**, então o painel de importação abre com campo de vídeo visível e arrastar e soltar, sem depender de ativação programática de seletor nativo; se ela cancelar, a rota e os dados atuais permanecem intactos e nenhum projeto é criado. Traceabilidade: REQ-006, DEC-010, TASK-019.
- **BDD-JRN-003-07 — Adaptar espaço de revisão**: dado que a pessoa abre um projeto sem preferência salva, então a prévia inicia compacta; quando escolhe outro tamanho ou recolhe/mostra o vídeo, a área de revisão se reorganiza sem overflow e a preferência é lembrada neste navegador. Em telas estreitas, o tamanho controla a altura do preview. Traceabilidade: REQ-006, DEC-023, TASK-020/021.

### JRN-004 — Encontrar e organizar projetos
- Requirements: REQ-008.
- Ator: criador navegando na biblioteca do estúdio.
- Fluxo: clicar em **Gravações** abre a galeria em largura ampla; pesquisar por nome ou filtrar pelo status; ajustar quantos cartões aparecem por página; abrir um projeto ou renomeá-lo diretamente no cartão. O editor também oferece a ação de renomear.
- Regras: a ordenação padrão é atividade mais recente; pesquisa/filtros/paginação só mudam a apresentação; renomear altera o nome do projeto e preserva fonte, decisões e exportações.
- **BDD-JRN-004-01**: a galeria lista todos os projetos e mostra 12, 24 ou 48 cartões conforme seleção, navegando páginas.
- **BDD-JRN-004-02**: busca por nome e filtro por status reduzem os resultados e exibem estado vazio recuperável.
- **BDD-JRN-004-03**: renomear pelo cartão ou editor persiste após recarga e mantém os ativos e dados do projeto.

### JRN-005 — Configurar OpenCode para análise de texto e imagem
- Requirements: REQ-009.
- Ator: criador configurando o estúdio.
- Fluxo: instalar e autenticar o OpenCode no host. O container do backend recebe o arquivo de autenticação como volume somente leitura; ao iniciar análise, o backend chama exclusivamente `opencode/mimo-v2.6-flash-free` para a transcrição temporizada e, se o toggle estiver ligado, até o limite global escolhido (2–1024, padrão 8) frames.
- Regras: modelo fixo `opencode/mimo-v2.6-flash-free`; transcrição e tradução continuam locais; toggle de imagem começa ligado e não desliga a análise textual; nenhum segredo é persistido pelo app ou devolvido na API; Codex nunca é invocado.
- **BDD-JRN-005-01**: sem CLI ou autenticação OpenCode, a análise não inicia e a interface orienta autenticar o OpenCode; com autenticação, texto é enviado via OpenCode ao ID fixo e o projeto registra o resultado.
- **BDD-JRN-005-02**: com OpenCode configurado, toggle ligado anexa no máximo oito pranchas ao mesmo modelo, cada uma com até 128 frames rotulados; desligado, somente a transcrição é enviada; chamadas reais de validação de texto e imagem confirmam o mesmo ID do modelo.

## Extensão proposta de JRN-001 — revisão com cobertura verificável

Fontes: PRD rev. 35, [diagnóstico rev. 2](../engineering/analysis-quality-audit.md), [plano rev. 10](../planning/analysis-quality-plan.md). Requisitos: REQ-002/003/006/010/011/012. Fluxo previsto: ver estado por capacidade → conferir transcrição suspeita e edições separadamente → revisar temas/cortes e conflitos → avaliar câmera inicial/final e preservar slides → exportar a composição aprovada. Falhas permitem retomada seletiva sem apagar revisão. Contratos implementados parcialmente; a execução real em clone está documentada, com revisão editorial humana pendente.

- **BDD-JRN-001-17 — Falha parcial visível:** dado timeout semântico e erro multimodal, ao abrir a revisão, mostrar capacidades incompletas e causas seguras; não apresentar zero horizontais como conclusão editorial.
- **BDD-JRN-001-18 — Cauda curta no áudio:** dado silêncio final abaixo de 3 s após “muito obrigado gente”, ao analisar o áudio, propor intervalo até EOF com margem e preservar a fala no preview/export; voz baixa e pausa interna não viram silêncio automaticamente.
- **BDD-JRN-001-19 — Enumeração preservada:** dada comparação entre Python, C e R, ao procurar retakes, preservar a enumeração; um retake real anotado continua detectável.
- **BDD-JRN-001-20 — Artefato ASR não remove fala:** dadas frases duplicadas em dezenas de milissegundos, ao validar a transcrição, sinalizar anomalia e conferir áudio; não promover duplicação a remoção do vídeo nem sobrescrever correção humana.
- **BDD-JRN-001-27 — Alinhamento de palavras colapsado:** dado um segmento com pelo menos cinco palavras e 40% ou mais com duração zero ou negativa, exibir aviso e identificar o trecho na transcrição; não gerar nova remoção semântica que cruze o segmento ou use citação presente nele, inclusive para pedidos editoriais. Edições anteriores e decisões do usuário permanecem revisáveis.
- A mesma proteção sinaliza oito ou mais palavras comprimidas acima de dez palavras por segundo, inclusive em transcrições antigas sem tempos por palavra; o alerta pede audição e não presume erro definitivo.
- **BDD-JRN-001-28 — Evidências incompletas:** dada uma lacuna no ASR, não presumir silêncio sem medição do áudio; dado frame ausente ou resposta incompleta/duplicada, preservar a área incerta e informar cobertura parcial; dada falha semântica ou de áudio, mostrar etapa e ação possível, sem indicar análise completa.
- **BDD-JRN-001-29 — Interrupção e fronteira de cena:** após reinício, projetos com trabalho interrompido mostram o estado recuperável; envio sem confirmação exige conferência antes de nova tentativa. Ao exportar, divisões curtas de cena preservam áudio e vídeo, e cena de câmera incerta não recebe correção por configuração antiga.
- **BDD-JRN-001-30 — Cobertura compacta e ASR fragmentado:** quando muitas falas são divididas em segmentos de até duas palavras e 0,65 s, mostrar faixas agregadas para audição/revisão; não bloquear automaticamente o texto. Na revisão visual, resumir a duração de slides e áreas sem classificação, exibindo controles somente para cenas de câmera revisáveis; não criar centenas de cartões para lacunas entre frames.
- **BDD-JRN-001-26 — Comentário de edição:** dada uma tentativa seguida do comentário explícito “vou cortar ... deu uma gaguejada” e de uma retomada, sugerir separadamente o comentário completo com tempos das palavras, preservando a retomada; quando houver sobreposição com o corte da tentativa, incluir a citação inteira. Citações ambíguas ou sem alinhamento confiável não produzem ajuste automático.
- **BDD-JRN-001-31 — Remover retake completo:** dada uma tentativa seguida de “Vou refazer isso” e de uma retomada corrigida, ao analisar, sugerir uma única remoção que cubra a tentativa e o comentário, mostre a retomada mantida e calcule os limites pelas palavras; se houver fala intercalada, anomalia ASR ou evidência ambígua, pedir revisão e não promover o corte incompleto.
- **BDD-JRN-001-21 — Retomada seletiva:** dada transcrição/revisão/traduções salvas e uma capacidade falha, ao retomá-la, preservar os artefatos válidos, limitar tentativas e impedir gravação de geração antiga. Editar texto marca dependentes desatualizados.
- **BDD-JRN-001-22 — Tema completo apesar de conflito pendente:** dado tema que cruza janelas e sugestão de remoção pendente, ao gerar horizontal, preservar contexto e exibir conflito; rejeitar remoção libera o trecho, aceitar recalcula a composição e exige revalidar contexto. Erro, schema ausente e zero justificado permanecem distintos.
- **BDD-JRN-001-23 — Layout misto por intervalos:** dada câmera→slides→câmera, ao analisar, representar intervalos e avaliar câmera inicial/final; não deixar slides ou falha de uma cena decidir o vídeo inteiro; respeitar o limite visual global escolhido, zero com toggle desligado.
- **BDD-JRN-001-24 — Cor e tempo coerentes:** dados ajustes por cena aceitos/rejeitados e remoção anterior à cena, ao exportar master e cortes, aplicar grade somente nas interseções aprovadas, preservar slides e remapear legendas; preview e export usam a mesma composição.

## Extensão de JRN-005 — escolher executor de análise

Fonte: REQ-009 atualizado pelo usuário em 2026-10-26, PRD rev. 29; DEC-029; TASK-031/032. O alvo substitui a exclusividade de OpenCode da jornada anterior. Fluxo: abrir Configurações → selecionar OpenCode/MiMo ou Codex/GPT-6 Luna/Medium → conferir disponibilidade → salvar → iniciar análise com provedor visível → revisar proveniência e resultados. Texto e imagens opcionais seguem a mesma opção; transcrição/tradução seguem locais.

- **BDD-JRN-005-01 — Seleção persistente:** dado Codex instalado/autenticado com acesso ao modelo, ao salvar Codex Luna Medium e recarregar configurações/iniciar análise, usar `gpt-6-luna`/`medium` para texto e imagens e registrar o executor; não exigir OpenCode.
- **BDD-JRN-005-02 — Execução estável:** dada execução iniciada em um provedor, ao trocar preferência global, execução ativa e retomada mantêm snapshot; novas execuções usam nova opção; histórico e decisões anteriores permanecem.
- **BDD-JRN-005-03 — Indisponibilidade sem substituição:** dado provedor escolhido indisponível, ao iniciar/retomar, explicar causa e preservar resultados; não executar outro modelo/provedor. Toggle off envia zero imagens; legado mantém origem OpenCode.
- **BDD-JRN-001-25 — Amostragem visual em pranchas:** dada preferência global entre 2 e 1024 frames (padrão 8), ao iniciar a análise, amostrar essa quantidade disponível, agrupar em pranchas com no máximo 128 quadros cada e imprimir índice e timestamp acima de cada quadro; até oito pranchas são enviadas por chamada. Persistir o limite e respeitá-lo nas retomadas; com toggle desligado não enviar imagens.
