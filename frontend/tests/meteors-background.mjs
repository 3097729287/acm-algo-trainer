import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {availablePages} from '../src/lib/navigationVisibility.js';
import {openSettings, setTheme} from './settings-navigation.mjs';

const out = '../.backups/meteors-20261105';
await mkdir(out, {recursive: true});
const server = await createServer({cacheDir: `${out}/vite`, optimizeDeps: {entries: ['index.html']}, server: {host: '127.0.0.1', port: 0, watch: null}, plugins: [{
  name: 'isolated-meteors-api', configureServer(server) {
    server.middlewares.use((request, response, next) => {
      if (!request.url?.startsWith('/api/')) return next();
      response.writeHead(410, {'Content-Type': 'application/json'});
      response.end('{"error":"Isolated animation test"}');
    });
  },
}]});
await server.listen();
const browser = await chromium.launch({channel: process.env.CI ? undefined : 'msedge', headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 960}});
page.setDefaultTimeout(12000);
const errors = [], external = [], writes = [], proof = [];
page.on('pageerror', error => errors.push(error.message));
const owner = 'c3e5d799-502a-4b4f-a864-a342f7db419e', now = new Date().toISOString();
let revision = 0;
let preferences = {theme: 'dark', accent: 'teal', backdrop: 'none', motion: true, panelOpacity: 76,
  pageOpacities: {settings: 55}, favorites: ['fixture::A'], fontSize: 15,
  onboardingGuideVersion: 2, onboardingCompleted: true, onboardingUnlockedPages: availablePages(11),
  levelNoticeVersion: 1, levelNoticeSeen: 100, levelNoticePending: 0};
const authority = () => ({owner, epoch: 'meteors-fixture', revision: ++revision});
const row = {id: 'fixture::A', title: '保留的训练题目', contest: '测试比赛', problem: 'A',
  platform: 'Codeforces', url: 'https://codeforces.com/contest/1/problem/A', difficulty: 800,
  contestDate: now, contestProblemCount: 1, catalogContentReady: true, statementAvailable: true, tags: ['模拟']};
const workspace = {training: [], sets: [], contests: [], activeContest: null,
  summary: {total: 0, accepted: 0, attempts: 0, pending: 0, due: 0}, now};
await page.route('**/api/**', async route => {
  const request = route.request(), url = new URL(request.url()), name = url.pathname.replace('/api/', '');
  if (!url.pathname.startsWith('/api/')) return route.continue();
  let value = {};
  if (name === 'account') value = {required: true, authenticated: true, token: 'fixture', account: {userId: owner, nickname: '测试学习者'}};
  else if (name === 'preferences') {
    if (request.method() === 'POST') {preferences = request.postDataJSON().preferences; writes.push(structuredClone(preferences));}
    value = {preferences, updatedAt: now};
  } else if (name === 'data') value = {rows: [row], categories: [], token: 'fixture', today: now.slice(0, 10)};
  else if (name === 'workspace') value = workspace;
  else if (name === 'navigation') value = {level: 11, confirmed: true, authority: authority()};
  else if (name === 'insights') value = {summary: {totalSolved: 98, activeDays: 20}, growth: {level: 11,
    confirmed: true, authority: authority(), currentLevelXp: 745, nextLevelXp: 2200, totalXp: 11745,
    ranked: {qualified: true, tier: '青铜', badge: 'tier-1', abilityScore: 900}},
    knowledge: [], recommendations: [], activity: [], assessment: {}, achievements: [], dailyTasks: {tasks: []}};
  else if (name === 'daily-tasks') value = {tasks: []};
  else if (name === 'software-update') value = {currentVersion: '1.6.1', status: 'current', autoCheck: false};
  else if (name === 'hub') value = {settings: {autoSync: false}, accounts: [], updates: {}, sync: {busy: false, providers: []}, notifications: []};
  else if (name === 'contest-calendar') value = {contests: [], providers: [], refreshing: false};
  else if (name === 'profile') value = {profile: {userId: owner, nickname: '测试学习者'}};
  else if (name === 'leaderboard') value = {configured: false, entries: []};
  else if (name === 'social') value = {available: false, notifications: [], totalLikes: 0, unreadCount: 0};
  else if (name === 'desktop/fullscreen') value = {available: false, fullscreen: false};
  else if (name === 'goals') value = {goals: [], contestPlan: {contests: []}};
  else if (name === 'training-lists') value = {lists: []};
  else if (name === 'lectures') value = {lectures: []};
  else if (name === 'templates') value = {templates: []};
  else if (name === 'wiki') value = {articles: []};
  else if (name === 'duel' || name === 'pk/v1/state' || name === 'browser-preparation') value = {available: false};
  else if (name === 'presence') value = {available: false, count: 0, entries: []};
  await route.fulfill({json: value});
});
await page.route(/^https?:\/\/(?!127\.0\.0\.1)(?!localhost)/, route => {external.push(route.request().url()); return route.abort();});
const sky = page.locator('.meteors-background'), rays = sky.locator('.meteors-background-ray');
const select = async name => {
  await page.getByRole('group', {name: '页面背景', exact: true}).getByRole('button', {name, exact: true}).click();
};
const waitSaved = backdrop => page.waitForFunction(({owner, backdrop}) =>
  JSON.parse(localStorage.getItem(`tb.preferences.v2.${owner}`) || '{}').backdrop === backdrop, {owner, backdrop});
try {
  await page.goto(server.resolvedUrls.local[0]);
  await page.waitForFunction(() => document.querySelector('.profile-level-number')?.textContent === '11');
  assert.equal(await sky.count(), 0);
  await openSettings(page, '外观');
  await select('流星夜空'); await sky.waitFor(); await waitSaved('meteors');
  await page.waitForResponse(response => response.url().includes('/api/preferences') && response.request().method() === 'POST' && response.ok());
  assert.equal(preferences.backdrop, 'meteors');
  assert.deepEqual(preferences.favorites, ['fixture::A']); assert.deepEqual(preferences.pageOpacities, {settings: 55});
  proof.push({settingsEntry: true, saved: true, unrelatedPreferencesPreserved: true});
  const positions = await rays.evaluateAll(nodes => nodes.map(node => [node.style.left, node.style.top]));
  for (const width of [2048, 1294, 800, 430]) for (const theme of ['dark', 'light']) {
    await page.setViewportSize({width, height: 960}); await setTheme(page, theme);
    const geometry = await sky.evaluate(node => {
      const box = node.getBoundingClientRect();
      return {x: box.x, y: box.y, w: box.width, h: box.height, pointerEvents: getComputedStyle(node).pointerEvents,
        overflow: document.documentElement.scrollWidth > innerWidth + 1,
        rays: [...node.querySelectorAll('.meteors-background-ray')].filter(ray => getComputedStyle(ray).display !== 'none').length,
        stars: node.querySelectorAll('circle').length};
    });
    assert.deepEqual([geometry.x, geometry.y, geometry.w, geometry.h], [0, 0, width, 960]);
    assert.equal(geometry.pointerEvents, 'none'); assert.equal(geometry.overflow, false); assert.equal(geometry.stars, 180);
    assert.equal(geometry.rays, width <= 650 ? 14 : 28);
    const font = page.getByRole('spinbutton', {name: '界面字号', exact: true});
    await font.fill('16'); await font.press('Tab'); assert.equal(await font.inputValue(), '16');
    assert.deepEqual(await rays.evaluateAll(nodes => nodes.map(node => [node.style.left, node.style.top])), positions);
    if (width === 2048 || width === 430) {
      await rays.evaluateAll(async nodes => {for (const node of nodes) {const animation = node.getAnimations()[0]; if (animation) {animation.pause(); await animation.ready; const timing = animation.effect.getTiming(), duration = Number(timing.duration); animation.currentTime = Number(timing.delay) + duration * (Math.ceil(Math.abs(Number(timing.delay)) / duration) + 1.3);}}});
      await page.screenshot({path: `${out}/meteors-${width}-${theme}.png`});
      await rays.evaluateAll(nodes => nodes.forEach(node => node.getAnimations()[0]?.play()));
    }
    proof.push({width, theme, ...geometry, inputUsable: true, stableSky: true});
  }
  const flight = await rays.first().evaluate(async node => {
    const animation = node.getAnimations()[0]; animation.pause(); await animation.ready;
    const timing = animation.effect.getTiming(), duration = Number(timing.duration), delay = Number(timing.delay);
    const start = delay + duration * (Math.ceil(Math.abs(delay) / duration) + 1);
    animation.currentTime = start + duration * .05; const from = new DOMMatrix(getComputedStyle(node).transform);
    animation.currentTime = start + duration * .65; const to = new DOMMatrix(getComputedStyle(node).transform);
    const core = getComputedStyle(node, '::before').boxShadow, tail = getComputedStyle(node).backgroundImage;
    animation.play(); return {dx: to.e - from.e, dy: to.f - from.f, core, tail};
  });
  assert(flight.dx < -100 && flight.dy > 80, JSON.stringify(flight));
  assert.match(flight.tail, /linear-gradient/); assert.notEqual(flight.core, 'none');
  proof.push({diagonalFlight: true, ...flight});
  await select('纯色'); assert.equal(await sky.count(), 0);
  for (const name of ['夜空极光', '细线网格', '熔金流体']) {await select(name); assert.equal(await sky.count(), 0);}
  await select('流星夜空'); await page.waitForTimeout(1100);
  await page.reload(); await sky.waitFor(); assert.equal(await page.locator('html').getAttribute('data-backdrop'), 'meteors');
  await openSettings(page, '外观'); assert.equal(await page.getByRole('button', {name: '流星夜空', exact: true}).getAttribute('aria-pressed'), 'true');
  await sky.evaluate(node => {Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange'));});
  assert.equal(await sky.getAttribute('data-paused'), 'true');
  assert.equal(await rays.first().evaluate(node => getComputedStyle(node).animationPlayState), 'paused');
  await sky.evaluate(() => {delete document.hidden; document.dispatchEvent(new Event('visibilitychange'));});
  assert.equal(await sky.getAttribute('data-paused'), 'false');
  await page.emulateMedia({reducedMotion: 'reduce'});
  assert.equal(await sky.locator('.meteors-background-rays').evaluate(node => getComputedStyle(node).display), 'none');
  assert.equal(await sky.locator('.meteors-star-group').first().evaluate(node => getComputedStyle(node).animationName), 'none');
  await page.emulateMedia({reducedMotion: 'no-preference'});
  preferences = {...preferences, motion: false}; await page.reload(); await sky.waitFor();
  assert.equal(await sky.locator('.meteors-background-rays').evaluate(node => getComputedStyle(node).display), 'none');
  proof.push({backgroundSwitchUnmounts: true, legacyBackgroundsSelectable: true, reloadRestores: true,
    hiddenPauses: true, visibleResumes: true, osReducedMotion: true, appReducedMotion: true});
  assert.deepEqual(errors, []); assert.deepEqual(external, []);
  console.log(JSON.stringify({ok: true, cases: proof.length, errors}));
  await writeFile(`${out}/verification.json`, JSON.stringify({ok: true, proof, preferenceWrites: writes.length, errors, external}, null, 2));
} catch (error) {
  await page.screenshot({path: `${out}/failure.png`}).catch(() => {});
  await writeFile(`${out}/failure.json`, JSON.stringify({error: error.stack, errors, external}, null, 2));
  throw error;
} finally {await browser.close(); await server.close();}
