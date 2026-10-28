const { test, expect } = require('@playwright/test');

for (const theme of ['graphite', 'chalk', 'workshop']) {
  test(`review warnings describe incomplete analysis and transcript anomalies (${theme})`, async ({ page }, testInfo) => {
    const id = 'f'.repeat(32);
    const project = {
      id, name: 'Fixture de revisão', status: 'review-ready', analysis_model: 'large-v3', source_language: 'pt',
      ai_provider: 'codex', metadata: { duration: 60, width: 1920, height: 1080 }, visual_frame_limit: 128,
      transcript: [{ id: 's1', start: 10, end: 12, text: 'Trecho que precisa de revisão' }, { id: 's2', start: 24, end: 24.2, text: 'palavra' }],
      transcript_anomalies: [{ segment_id: 's1', start: 10, end: 12, kind: 'word-alignment' }, { segment_id: 's2', segment_index: 1, start: 24, end: 60, segment_count: 48, kind: 'segment-fragmentation' }],
      edits: [{ id: 'e1', start: 10, end: 12, label: 'Retirar tentativa e comentário', decision: 'pending', source: 'codex', confidence: 'medium', retake_evidence: {
        discard: { start: 10, end: 11, text: 'Tentativa descartada.' },
        comment: { start: 11.2, end: 12, text: 'Vou refazer isso.' },
        keep: { start: 12.3, end: 14, text: 'Versão corrigida preservada.' },
      } }],
      shorts: [], youtube_cuts: [], captions: {}, translated_languages: [], color_grade: { enabled: false, segments: {} },
      visual_analysis: { status: 'complete', scene_review: { status: 'partial', provider: 'codex' }, grade_segments: [] },
      analysis_run: { status: 'partial', provider_result: { blocked_edits_asr: 1 }, visual_frames_used: 128, capabilities: {
        semantic: { status: 'unavailable' }, visual: { status: 'partial', classified_frames: 96, requested_frames: 128 }, audio: { status: 'failed' },
      } },
    };
    await page.addInitScript(value => localStorage.setItem('recording-theme', value), theme);
    await page.route(`**/api/projects/${id}`, route => route.fulfill({ json: project }));
    await page.route('**/api/projects', route => route.fulfill({ json: [project] }));
    await page.route('**/api/health', route => route.fulfill({ json: { ok: true } }));
    await page.route('**/api/settings/ai', route => route.fulfill({ json: { provider: 'codex', configured: true, options: {} } }));
    await page.route('**/api/settings/youtube', route => route.fulfill({ json: { configured: false, connected: false } }));
    await page.route(`**/api/projects/${id}/source`, route => route.fulfill({ status: 200, contentType: 'video/mp4', body: '' }));
    await page.goto(`/projects/${id}`);
    const warning = page.getByRole('region', { name: 'Pontos para revisar' });
    await page.getByRole('button', { name: 'Ver pontos para revisar' }).click();
    await expect(warning).toBeFocused();
    await expect(warning).toContainText('Análise de texto');
    await expect(warning).toContainText('96 de 128 frames classificados');
    await expect(warning).toContainText('O limite de frames desta análise foi usado');
    await expect(warning).toContainText('Medição de silêncio');
    await expect(warning).toContainText('1 trecho tem');
    await expect(warning).toContainText('1 sugestão de remoção foi descartada');
    await expect(warning).toContainText('48 segmentos em 1 faixa');
    await expect(warning.locator('[data-retry-capability="semantic"]')).toBeVisible();
    await expect(warning.locator('[data-retry-capability="audio"]')).toBeVisible();
    await expect(warning.locator('[data-retry-capability="visual"]')).toHaveCount(0);
    for (const button of await warning.getByRole('button').all()) {
      const size = await button.boundingBox();
      expect(size.width).toBeGreaterThanOrEqual(24);
      expect(size.height).toBeGreaterThanOrEqual(24);
      const fontSize = await button.evaluate(el => parseFloat(getComputedStyle(el).fontSize));
      expect(fontSize).toBeGreaterThanOrEqual(12);
    }
    await expect(page.getByText('Transcrição ou tempos podem estar incorretos neste trecho.')).toBeVisible();
    await expect(page.getByText('Remover · tentativa descartada')).toBeVisible();
    await expect(page.getByText('Remover · comentário de edição')).toBeVisible();
    await expect(page.getByText('Manter · versão retomada')).toBeVisible();
    await page.screenshot({path: testInfo.outputPath('review-warning.png')});
    await warning.getByRole('button', { name: 'Revisar legendas' }).click();
    await expect(page.getByRole('tab', { name: 'Legendas' })).toHaveAttribute('aria-selected', 'true');
    const listen = page.getByRole('button', { name: /transcrição precisa de revisão/ }).first();
    await expect(listen).toBeVisible();
    await expect(listen).toHaveAttribute('data-seek', '8');
    await expect(listen).toHaveAttribute('data-end', '14');
    await page.getByRole('button', { name: 'Recolher prévia' }).click();
    await expect(page.locator('#video-preview')).toBeHidden();
    await listen.click();
    await expect(page.locator('#video-preview')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  });
}

test('uncertain upload shows an explicit recovery action before retry', async ({ page }) => {
  const id = 'e'.repeat(32);
  const asset = { id: 'master', type: 'master', filename: 'aula.mp4', upload_status: 'uploading-unknown', youtube_selected: true };
  const project = { id, name: 'Fixture de envio', status: 'upload-failed', analysis_model: 'medium', source_language: 'pt',
    metadata: { duration: 10, width: 1920, height: 1080 }, transcript: [], edits: [], shorts: [], youtube_cuts: [],
    captions: {}, translated_languages: [], exports: [asset], review: {}, visual_analysis: {}, color_grade: {} };
  let confirmed = false;
  await page.route(`**/api/projects/${id}`, route => route.fulfill({ json: project }));
  await page.route('**/api/projects', route => route.fulfill({ json: [project] }));
  await page.route('**/api/health', route => route.fulfill({ json: { ok: true } }));
  await page.route('**/api/settings/ai', route => route.fulfill({ json: { provider: 'codex', configured: true, options: {} } }));
  await page.route('**/api/settings/youtube', route => route.fulfill({ json: { configured: false, connected: false } }));
  await page.route(`**/api/projects/${id}/source`, route => route.fulfill({ status: 200, body: '' }));
  await page.route(`**/api/projects/${id}/youtube/retry-video`, async route => {
    confirmed = route.request().postDataJSON().confirmed_absent;
    asset.upload_status = 'not-uploaded';
    await route.fulfill({ json: project });
  });
  await page.goto(`/projects/${id}`);
  await expect(page.getByText('resultado não confirmado')).toBeVisible();
  page.on('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Conferi no Studio: vídeo ausente' }).click();
  await expect.poll(() => confirmed).toBe(true);
  await expect(page.getByRole('button', { name: 'Conferi no Studio: vídeo ausente' })).toHaveCount(0);
});

test('real project copy exposes the flagged transcript and rejected candidate', async ({ page }) => {
  const id = process.env.VALIDATION_PROJECT_ID;
  test.skip(!id, 'A cópia isolada do projeto real não está disponível.');
  await page.goto(`/projects/${id}`);
  const warning = page.getByRole('region', { name: 'Pontos para revisar' });
  await expect(warning).toContainText('3 trechos têm');
  await expect(page.getByText('Transcrição ou tempos podem estar incorretos neste trecho.')).toBeVisible();
  await expect(page.locator('[data-edit-state="ai-edits-2"]')).toHaveText('Estado salvo: rejeitada');
  await warning.getByRole('button', { name: 'Revisar legendas' }).click();
  await expect(page.getByRole('button', { name: /Ouvir trecho em 8:21.*transcrição precisa de revisão/ })).toBeVisible();
});

test('resolved retake shows the discarded attempt, full command, and complete kept restart', async ({ page }) => {
  const id = process.env.RETAKE_VALIDATION_PROJECT_ID;
  test.skip(!id, 'O clone real do caso de retake não está disponível.');
  await page.goto(`/projects/${id}`);
  await page.getByRole('tab', { name: 'Edição' }).click();
  const card = page.locator('.edit-card').filter({ hasText: 'Retirar tentativa descartada e comentário de edição' });
  await expect(card).toHaveCount(1);
  await expect(card).toContainText('Remover · tentativa descartada');
  await expect(card).toContainText('E isso daqui não se deve só ao propósito probabilístico.');
  await expect(card).toContainText('Remover · comentário de edição');
  await expect(card).toContainText('Vou refazer isso.');
  await expect(card).toContainText('Manter · versão retomada');
  await expect(card).toContainText('E isso não se deve apenas ao modelo probabilístico que é como um LLM funciona.');
  await expect(card).toContainText('2:27');
  await expect(card).toContainText('2:36');
});

test('visual coverage stays compact when sampled slides create many intervals', async ({ page }) => {
  const id = process.env.VALIDATION_VISUAL_PROJECT_ID;
  test.skip(!id, 'A cópia isolada com revisão visual não está disponível.');
  await page.goto(`/projects/${id}`);
  await page.getByRole('tab', { name: 'Imagem' }).click();
  await expect(page.locator('.visual-coverage')).toContainText('cenas de câmera ajustáveis: 0');
  await expect(page.locator('.scene-grade-card')).toHaveCount(0);
  await expect(page.getByText(/cores do vídeo permanecem intactas/)).toBeVisible();
});

test('legacy incomplete image review preserves prior color choices', async ({ page }) => {
  const id = 'd'.repeat(32);
  const project = { id, name: 'Fixture visual anterior', status: 'review-ready', metadata: { duration: 10, width: 1920, height: 1080 },
    source_language: 'pt', transcript: [], edits: [], shorts: [], youtube_cuts: [], captions: {}, visual_legacy_incomplete: true,
    color_grade: { segments: { cam: { enabled: true, intensity: 1 } } }, visual_analysis: { status: 'complete',
      grade_segments: [{ id: 'cam', start: 0, end: 10, layout: 'camera', confidence: 'high', status: 'reviewable' }] } };
  let payload;
  await page.route(`**/api/projects/${id}`, route => route.fulfill({ json: project }));
  await page.route('**/api/projects', route => route.fulfill({ json: [project] }));
  await page.route('**/api/health', route => route.fulfill({ json: { ok: true } }));
  await page.route('**/api/settings/ai', route => route.fulfill({ json: { provider: 'codex', configured: true, options: {} } }));
  await page.route('**/api/settings/youtube', route => route.fulfill({ json: { configured: false, connected: false } }));
  await page.route(`**/api/projects/${id}/source`, route => route.fulfill({ status: 200, body: '' }));
  await page.route(`**/api/projects/${id}/review`, async route => { payload = route.request().postDataJSON(); await route.fulfill({ json: project }); });
  await page.goto(`/projects/${id}`);
  await expect(page.getByRole('region', { name: 'Pontos para revisar' })).toContainText('Classificação visual anterior incompleta');
  await page.getByRole('tab', { name: 'Imagem' }).click();
  await expect(page.locator('[data-grade-segment]')).toHaveCount(0);
  await page.getByRole('button', { name: 'Salvar revisão' }).click();
  await expect.poll(() => Boolean(payload)).toBe(true);
  expect(payload).not.toHaveProperty('visual');
});
