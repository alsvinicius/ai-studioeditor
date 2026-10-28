const { test, expect } = require('@playwright/test');
const { readFile } = require('node:fs/promises');
const { homedir } = require('node:os');
const { join } = require('node:path');

test('settings persist the selected analysis provider and show its readiness', async ({ page }) => {
  let selected = 'opencode';
  const options = {
    opencode: { label: 'OpenCode · MiMo V2.6 Flash Free', model: 'opencode/mimo-v2.6-flash-free', configured: true },
    codex: { label: 'Codex · GPT-6 Luna · Medium', model: 'gpt-6-luna', effort: 'medium', configured: false },
  };
  await page.route('**/api/health', route => route.fulfill({ json: { ffmpeg: true, youtube_authorized: false } }));
  await page.route('**/api/settings/youtube', route => route.fulfill({ json: { configured: false, connected: false, redirect_uri: 'http://localhost/callback', visibility: 'private', caption_languages: [] } }));
  await page.route('**/api/settings/ai', async route => {
    if (route.request().method() === 'PUT') selected = (await route.request().postDataJSON()).provider;
    await route.fulfill({ json: { provider: selected, model: options[selected].model, effort: options[selected].effort || null, configured: options[selected].configured, options } });
  });
  await page.goto('/settings');
  await expect(page.locator('#ai-provider')).toHaveValue('opencode');
  await page.locator('#ai-provider').selectOption('codex');
  await expect(page.locator('#ai-provider')).toHaveValue('codex');
  await expect(page.locator('#ai-message')).toContainText('Codex · GPT-6 Luna · Medium');
  await expect(page.locator('#ai-state')).toHaveText('Indisponível');
  await page.reload();
  await expect(page.locator('#ai-provider')).toHaveValue('codex');
});

test('scene review offers grade controls only on verified camera intervals', async ({ page }) => {
  const id = 'a'.repeat(32);
  const project = {
    id, name: 'Synthetic scene review', status: 'review-ready', analysis_model: 'medium', source_language: 'pt',
    ai_provider: 'codex', ai_model: 'gpt-6-luna', metadata: { duration: 12, width: 1920, height: 1080 },
    transcript: [], edits: [], shorts: [], youtube_cuts: [], captions: {}, job: { stage: 'complete' },
    color_grade: { enabled: false, intensity: 1, segments: {} },
    visual_analysis: {
      status: 'complete', framing_confidence: 'high', metrics: { median_luma: 0.4, shadow_clipping: 0, highlight_clipping: 0, median_saturation: 0.2 },
      scene_review: { status: 'complete', provider: 'codex' },
      grade_segments: [
        { id: 'open', start: 0, end: 4, layout: 'camera', confidence: 'high', status: 'reviewable', reason: 'Câmera inicial', suggestion: { brightness: 0.02, contrast: 1.02, saturation: 1 } },
        { id: 'slides', start: 4, end: 8, layout: 'slides', confidence: 'high', status: 'preserve', reason: 'Slides preservados' },
        { id: 'close', start: 8, end: 12, layout: 'camera', confidence: 'high', status: 'reviewable', reason: 'Câmera final', suggestion: { brightness: -0.01, contrast: 1, saturation: 1 } },
      ],
    },
  };
  let reviewPayload;
  await page.route(`**/api/projects/${id}`, route => route.fulfill({ json: project }));
  await page.route('**/api/projects', route => route.fulfill({ json: [project] }));
  await page.route(`**/api/projects/${id}/source`, route => route.fulfill({ status: 200, contentType: 'video/mp4', body: '' }));
  await page.route(`**/api/projects/${id}/visual-preview**`, route => route.fulfill({ status: 200, contentType: 'image/jpeg', body: Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAb/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxB//9k=', 'base64') }));
  await page.route(`**/api/projects/${id}/review`, async route => { reviewPayload = route.request().postDataJSON(); await route.fulfill({ json: project }); });
  await page.goto(`/projects/${id}`);
  await page.getByRole('tab', { name: /Imagem/ }).click();
  await expect(page.locator('[data-grade-segment]')).toHaveCount(2);
  await expect(page.getByText('Slides preservados')).toBeVisible();
  await expect(page.getByText('Câmera inicial')).toBeVisible();
  await expect(page.getByText('Câmera final')).toBeVisible();
  await page.locator('[data-grade-segment="open"]').check();
  await page.locator('[data-grade-intensity="open"]').fill('0.5');
  await page.getByRole('button', { name: 'Salvar revisão' }).click();
  await expect.poll(() => reviewPayload?.visual?.grade_segments?.length).toBe(2);
  expect(reviewPayload.visual.grade_segments.find(item => item.id === 'open')).toMatchObject({ enabled: true, intensity: 0.5 });
});

// REQ-006 / BDD-JRN-003-06 / DEC-010 / TASK-019.
test('gallery and project open a visible import dialog; cancel preserves state', async ({ page, request }, testInfo) => {
  const before = await (await request.get('/api/projects')).json();
  expect(before.length).toBeGreaterThan(0);
  // Opening the panel must not depend on programmatic activation of a file input.
  await page.addInitScript(() => {
    const original = HTMLInputElement.prototype.click;
    HTMLInputElement.prototype.click = function() {
      if (this.type === 'file') throw new Error('Programmatic picker blocked');
      return original.call(this);
    };
  });
  for (const route of ['/', `/projects/${before[0].id}`]) {
    await page.goto(route);
    const button = page.locator('#import-button');
    await button.click();
    const dialog = page.getByRole('dialog', { name: 'Nova gravação', exact: true });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByLabel('Vídeo da gravação')).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(route === '/' ? 'gallery-import.png' : 'project-import.png') });
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
    await expect(page).toHaveURL(new RegExp(`${route}$`));
    await expect(button).toBeFocused();
  }
  const after = await (await request.get('/api/projects')).json();
  expect(after.map(p => p.id).sort()).toEqual(before.map(p => p.id).sort());
});

test('empty gallery supports Enter, Space and close button', async ({ page }) => {
  await page.route('**/api/projects', route => route.fulfill({ json: [] }));
  await page.goto('/');
  const button = page.locator('#gallery-import');
  for (const key of ['Enter', 'Space']) {
    await button.focus();
    await button.press(key);
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('button', { name: 'Fechar nova gravação' }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(button).toBeFocused();
  }
});

test('visible file control opens a real file chooser', async ({ page }) => {
  await page.goto('/');
  await page.locator('#import-button').click();
  const chooserPromise = page.waitForEvent('filechooser');
  await page.getByLabel('Vídeo da gravação').click();
  await (await chooserPromise).setFiles([]);
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByLabel('Vídeo da gravação')).toBeEnabled();
});

test('invalid files and upload errors remain visible inside dialog and allow retry', async ({ page }) => {
  await page.goto('/');
  await page.locator('#import-button').click();
  await page.locator('#file').setInputFiles({ name: 'not-a-video.txt', mimeType: 'text/plain', buffer: Buffer.from('invalid') });
  await expect(page.locator('#import-feedback')).toContainText('Escolha um vídeo MP4 ou MKV');
  await page.route('**/api/projects/upload', route => route.fulfill({ status: 400, json: { detail: 'Vídeo inválido' } }));
  await page.locator('#file').setInputFiles({ name: 'invalid.mp4', mimeType: 'video/mp4', buffer: Buffer.from('invalid') });
  await expect(page.locator('#import-feedback')).toContainText('Vídeo inválido');
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.locator('#file')).toBeEnabled();
  await expect(page.locator('#file')).toHaveValue('');
});

test('real OBS upload reaches analysis settings and the dialog can reopen', async ({ page, request }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  const buffer = await readFile(process.env.OBS_TEST_VIDEO || join(homedir(), 'Videos/OBS/teste.mp4'));
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await page.locator('#import-button').click();
  const chooserPromise = page.waitForEvent('filechooser');
  await page.getByLabel('Vídeo da gravação').click();
  const uploaded = page.waitForResponse(response => response.url().endsWith('/api/projects/upload') && response.request().method() === 'POST');
  await (await chooserPromise).setFiles({ name: 'Playwright - Nova gravacao.mp4', mimeType: 'video/mp4', buffer });
  const response = await uploaded;
  expect(response.ok()).toBeTruthy();
  const project = await response.json();
  await expect(page).toHaveURL(new RegExp(`/projects/${project.id}$`));
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByLabel('Idioma da gravação')).toHaveValue('pt');
  await expect(page.getByLabel('Qualidade da transcrição')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Analisar gravação' })).toBeVisible();
  await expect(page.locator('#import-status')).toBeHidden();
  await expect(page.locator('#file')).toHaveValue('');
  expect((await (await request.get(`/api/projects/${project.id}`)).json()).status).toBe('imported');
  await page.screenshot({ path: testInfo.outputPath('import-complete.png'), fullPage: true });
  await page.locator('#import-button').click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Fechar nova gravação' }).click();
  await expect(page).toHaveURL(new RegExp(`/projects/${project.id}$`));
  expect(errors).toEqual([]);
});
