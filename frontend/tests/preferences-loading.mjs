// Real App + AccountGate with isolated, delayed API fixtures. No live state.
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { chromium } from 'playwright';

process.env.TB_OFFLINE = '1';
const server = await createServer({ server: { host: '127.0.0.1', port: 0, hmr: false } });
await server.listen();
const origin = `http://127.0.0.1:${server.httpServer.address().port}`;
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const userId = '00000000-0000-4000-8000-000000000001';
const key = `tb.preferences.v2.${userId}`;
const now = '2026-10-16T05:00:00.000Z';
const results = {};

async function scenario(mode) {
  const context = await browser.newContext({ viewport: { width: 1480, height: 1000 } });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const errors = [], unexpected = [], writes = [], timeline = [];
  let reads = 0, releaseRead;
  const readReady = new Promise(resolve => { releaseRead = resolve; });
  const remote = { theme: 'dark', accent: 'purple', fontSize: 20, navLabels: { records: '云端记录' }, seenAchievements: ['official-1'] };
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(({ key }) => {
    localStorage.setItem(key, JSON.stringify({ theme: 'dark', accent: 'teal', seenAchievements: ['official-10'] }));
    window.fixtureHidden = false;
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => window.fixtureHidden });
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => window.fixtureHidden ? 'hidden' : 'visible' });
    window.setFixtureVisibility = hidden => { window.fixtureHidden = hidden; document.dispatchEvent(new Event('visibilitychange')); };
  }, { key });
  const achievements = [1, 10, 25].map(target => ({ id: `official-${target}`, name: `AC ${target}题`, description: '测试成就', target, progress: target, unlocked: true, unlockedAt: now, rewardXp: 25, rewardClaimed: true }));
  await page.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname;
    if (url.origin === origin && !path.startsWith('/api/')) return route.continue();
    if (url.origin !== origin) { unexpected.push(url.href); return route.abort(); }
    let value;
    if (path === '/api/preferences') {
      if (request.method() === 'GET') {
        reads++;
        timeline.push(`read-${reads}`);
        if (mode !== 'delayed' && reads === 1) return route.fulfill({ status: 503, json: { error: 'Temporary fixture preferences outage' } });
        await readReady;
        timeline.push('read-complete');
        value = { preferences: remote };
      } else {
        assert.equal(request.headers()['x-tb-token'], 'fixture');
        timeline.push('write');
        const body = request.postDataJSON();
        writes.push(body.preferences);
        value = body;
      }
    } else if (path === '/api/account') value = { required: false, authenticated: true, token: 'fixture', account: { userId, nickname: '偏好测试用户', loginId: 'fixture-login' } };
    else if (path === '/api/data') value = { rows: [], categories: [], token: 'fixture', today: now.slice(0, 10) };
    else if (path === '/api/workspace') value = { training: [], sets: [], contests: [], activeContest: null, summary: { total: 0, accepted: 0, attempts: 0, due: 0, pending: 0, todayAccepted: 0 }, now };
    else if (path === '/api/insights') value = { summary: {}, growth: { level: 1, currentLevelXp: 0, nextLevelXp: 100 }, achievements, knowledge: [], recommendations: [], activity: [], assessment: {}, dailyTasks: { tasks: [] } };
    else if (path === '/api/inbox') value = { pending: 0, errors: [] };
    else if (path === '/api/hub') value = null;
    else if (path === '/api/goals') value = { goals: [], contestPlan: { contests: [] } };
    else if (path === '/api/software-update') value = { currentVersion: '1.1.0', status: 'current', autoCheck: false, canInstall: false };
    else if (path === '/api/social') value = { available:false, activity:[], notifications:[] };
    else if (path === '/api/browser-preparation') value = { available: false };
    else if (path === '/api/desktop/fullscreen') value = { available: false, fullscreen: false };
    else { unexpected.push(path); value = { error: 'Unexpected fixture request' }; }
    await route.fulfill({ json: value });
  });
  try {
    await page.clock.install({ time: new Date(now) });
    await page.goto(origin);
    await page.getByRole('navigation', { name: '主导航', exact: true }).waitFor();
    await page.getByRole('button', { name: '成就', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: /成就 ·/ });
    const hovered = dialog.locator('[data-achievement-id="official-25"]');
    await hovered.waitFor();
    await hovered.hover();
    assert.ok(!(await hovered.getAttribute('class')).includes('progress-achievement-new'));
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: '切换主题', exact: true }).click();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
    assert.equal(writes.length, 0, 'never upload a local default before successfully reading remote preferences');
    if (mode === 'timer') {
      await page.clock.runFor(5100);
      await page.waitForFunction(() => document.querySelector('.app-shell'));
      for (let i = 0; reads < 2 && i < 100; i++) await new Promise(resolve => setTimeout(resolve, 10));
      assert.equal(reads, 2, 'failed initialization retries after five seconds');
    } else if (mode === 'visibility') {
      await page.evaluate(() => window.setFixtureVisibility(true));
      await page.clock.runFor(5100);
      assert.equal(reads, 1, 'retry does not poll while the interface is hidden');
      await page.evaluate(() => window.setFixtureVisibility(false));
      for (let i = 0; reads < 2 && i < 100; i++) await new Promise(resolve => setTimeout(resolve, 10));
      assert.equal(reads, 2, 'visibility restoration immediately retries the failed read');
    } else assert.equal(reads, 1, 'one delayed initialization request is shared');
    assert.equal(writes.length, 0, 'a retry in flight still blocks uploads');
    releaseRead();
    await page.waitForFunction(({ key }) => JSON.parse(localStorage.getItem(key)).accent === 'purple', { key });
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'light', 'late remote response preserves a theme changed while reading');
    const merged = await page.evaluate(key => JSON.parse(localStorage.getItem(key)), key);
    assert.equal(merged.fontSize, 20, 'untouched fields use remote values');
    assert.equal(merged.navLabels.records, '云端记录');
    assert.deepEqual([...merged.seenAchievements].sort(), ['official-1', 'official-10', 'official-25'], 'remote, earlier local and newly hovered read states are united');
    // The existing update/logout barrier must flush the merged dirty snapshot.
    const saved = await page.evaluate(async () => {
      const pending = [];
      window.dispatchEvent(new CustomEvent('tb-before-update', { detail: { waitUntil: promise => pending.push(promise) } }));
      return Promise.all(pending);
    });
    assert.ok(saved.length > 0 && saved.every(value => value === true));
    assert.equal(writes.length, 1);
    assert.equal(writes[0].theme, 'light');
    assert.equal(writes[0].accent, 'purple');
    assert.deepEqual([...writes[0].seenAchievements].sort(), ['official-1', 'official-10', 'official-25']);
    assert.ok(timeline.indexOf('read-complete') < timeline.indexOf('write'), 'read and upload stay serialized');
    await page.getByRole('button', { name: '成就', exact: true }).click();
    await dialog.waitFor();
    assert.equal(await dialog.locator('.progress-achievement-new').count(), 0, 'late read does not restore the hovered achievement highlight');
    assert.deepEqual(errors, []);
    assert.deepEqual(unexpected, []);
    results[mode] = { reads, writes: writes.length, localChangesPreserved: true, remoteUntouchedFieldsPreserved: true, seenUnion: true, exitSaveBarrier: true };
  } finally {
    releaseRead();
    await page.goto('about:blank');
    await context.close();
  }
}

try {
  await scenario('delayed');
  await scenario('timer');
  await scenario('visibility');
  console.log(JSON.stringify({ ok: true, scenarios: results, realAccounts: false }));
} finally {
  await browser.close();
  await server.close();
}
