import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawn } from 'node:child_process';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const root = resolve('..');
const state = await mkdtemp(join(tmpdir(), 'tb-recent-editorials-'));
const external = process.env.TB_TEST_URL;
const service = external ? null : spawn(process.env.TB_PYTHON || 'python', [join(root, 'frontend/tests/local-api-server.py')], {
  cwd: root, windowsHide: true,
  env: { ...process.env, TB_STATE_DIR: state, TB_OFFLINE: '1', PYTHONIOENCODING: 'utf-8' },
});
let stderr = '', vite, browser;
service?.stderr.on('data', value => { stderr += value; });
const output = join(root, '.backups/recent-reader-ui');
fs.mkdirSync(output, { recursive: true });
try {
  const api = external || await new Promise((done, fail) => {
    const timer = setTimeout(() => fail(Error(stderr || 'API startup timeout')), 45000);
    service.stdout.on('data', value => {
      const match = String(value).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); done(match[0]); }
    });
    service.once('exit', code => { clearTimeout(timer); fail(Error(`API exited ${code}: ${stderr}`)); });
  });
  process.env.TB_API_URL = api;
  if (!external) {
    vite = await createServer({ server: { host: '127.0.0.1', port: 0, fs: { allow: [process.cwd(), fs.realpathSync('node_modules')] } } });
    await vite.listen();
  }
  const url = external || `http://127.0.0.1:${vite.httpServer.address().port}`;
  browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1480, height: 960 } });
  page.setDefaultTimeout(20000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({ theme: 'light', onboardingCompleted: true, navSchema: 2 })));
  const items = JSON.parse(fs.readFileSync(join(root, 'docs/contests/20261024/import-report.json'), 'utf8')).created;
  await page.goto(url);
  await page.getByRole('heading', { name: '从第一道题开始', exact: true }).waitFor();
  await page.keyboard.press('Control+2');
  for (const item of items) {
    const payload = await (await page.request.get(url + '/api/solution?id=' + encodeURIComponent(item.id))).json();
    assert.ok(payload.markdown && payload.detailedSolution?.markdown, item.id);
    const code = text => [...text.matchAll(/```cpp\n([\s\S]*?)```/g)].at(-1)?.[1];
    assert.equal(code(payload.markdown), code(payload.detailedSolution.markdown));
    const title = payload.markdown.split('\n')[0].replace(/^## \w+\. /, '');
    await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill(title);
    await page.locator(`tr[data-id=${JSON.stringify(item.id)}]`).getByRole('button', { name: '题解 ' + title, exact: true }).click();
    const panel = page.getByRole('complementary', { name: '题解阅读' });
    await panel.getByRole('group', { name: '题解版本' }).waitFor();
    for (const variant of ['默认题解', '详细题解']) {
      await panel.getByRole('button', { name: variant, exact: true }).click();
      await panel.locator('.reader-content .markdown').first().waitFor();
      await page.waitForTimeout(100);
      const full = panel.locator('.solution-full:not([open]) > summary');
      if (await full.count()) await full.click();
      assert.equal(await panel.locator('.katex-error').count(), 0, item.id + variant);
      assert.equal(await panel.locator('.lecture-disclosure[open]').count(), 0);
      assert.ok(await panel.locator('.lecture-disclosure').count());
      for (const img of await panel.locator('.reader-content img').all()) {
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(node => node.decode());
        assert.ok(await img.evaluate(node => node.naturalWidth > 0));
        await img.screenshot({ path: join(output, item.id.replace(/[: ]/g, '_') + '-' + variant + '.png') });
      }
      await panel.locator('.lecture-disclosure summary').first().click();
      assert.equal(await panel.locator('.lecture-disclosure[open]').count(), 1);
      await panel.locator('.lecture-disclosure summary').first().click();
    }
    await page.keyboard.press('Escape');
    await panel.waitFor({ state: 'hidden' });
  }
  await page.locator('.sidebar').getByRole('button', { name: '题单', exact: true }).click();
  const catalog = page.locator('.training-list-content');
  await catalog.locator('strong').filter({ hasText: /^字符串$/ }).click();
  assert.equal(await catalog.locator('button.catalog-folder-row').count(), 8);
  await catalog.locator('strong').filter({ hasText: /^模式匹配$/ }).click();
  await catalog.getByText('KMP 与 AC 自动机 · 基础练习', { exact: false }).waitFor();
  await page.screenshot({ path: join(output, 'catalog-real-api.png'), fullPage: true });
  assert.deepEqual(errors, []);
  console.log('PASS: real API catalog and eight editorials, sixteen variants, identical reference code, collapsed foundations, all six figures and KaTeX' + (external ? '; frozen desktop' : ''));
} finally {
  await browser?.close();
  await vite?.close();
  service?.kill();
}
