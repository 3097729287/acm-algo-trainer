import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {createServer as createHttpServer} from 'node:http';
import {createReadStream} from 'node:fs';
import {resolve, sep, extname} from 'node:path';
import {availablePages} from '../src/lib/navigationVisibility.js';

const production = process.argv.includes('--built');
const out = '../.backups/rank-promotion-20261106/' + (production ? 'built-app' : 'app');
await mkdir(out, {recursive: true});
let server;
if (production) {
  const directory = resolve('dist');
  const http = createHttpServer((request,response) => {
    const pathname = new URL(request.url,'http://localhost').pathname;
    const file = resolve(directory, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (pathname.startsWith('/api/') || !file.startsWith(directory + sep)) {response.writeHead(410);response.end();return;}
    response.setHeader('Content-Type', ({'.js':'text/javascript','.css':'text/css','.html':'text/html','.woff2':'font/woff2','.svg':'image/svg+xml'})[extname(file)] || 'application/octet-stream');
    const stream = createReadStream(file);stream.on('error',()=>{response.writeHead(404);response.end();});stream.pipe(response);
  });
  await new Promise(resolve=>http.listen(0,'127.0.0.1',resolve));
  server = {resolvedUrls:{local:[`http://127.0.0.1:${http.address().port}/`]},close:()=>new Promise(resolve=>http.close(resolve))};
} else {
server = await createServer({cacheDir: `${out}/vite`, optimizeDeps: {entries: ['index.html']}, server: {host: '127.0.0.1', port: 0, watch: null}, plugins: [{
  name: 'isolated-meteors-api', configureServer(server) {
    server.middlewares.use((request, response, next) => {
      if (!request.url?.startsWith('/api/')) return next();
      response.writeHead(410, {'Content-Type': 'application/json'});
      response.end('{"error":"Isolated animation test"}');
    });
  },
}]});
await server.listen();
}
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
let ability = 900, insightReads = 0, workspaceReads = 0;
const authority = () => ({owner, epoch: 'meteors-fixture', revision: ++revision});
const row = {id: 'fixture::A', title: '保留的训练题目', contest: '测试比赛', problem: 'A',
  platform: 'Codeforces', url: 'https://codeforces.com/contest/1/problem/A', difficulty: 800,
  contestDate: now, contestProblemCount: 1, catalogContentReady: true, statementAvailable: true, tags: ['模拟']};
const workspace = {training: [{id:'fixture::A',activeAt:now,today:true,accepted:false,attempts:0}], sets: [], contests: [], activeContest: null,
  summary: {total: 1, accepted: 0, attempts: 0, pending: 0, due: 0}, now};
await page.route('**/api/**', async route => {
  const request = route.request(), url = new URL(request.url()), name = url.pathname.replace('/api/', '');
  if (!url.pathname.startsWith('/api/')) return route.continue();
  if (name === 'insights') insightReads++;
  if (name === 'workspace') workspaceReads++;
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
    ranked: {qualified: true, tier: '青铜', badge: 'tier-1', abilityScore: ability}},
    knowledge: [], recommendations: [], activity: [], assessment: {}, achievements: [], dailyTasks: {tasks: []}};
  else if (name === 'problem') value = {id:row.id,title:row.title,url:row.url,markdown:'# 测试题目\n\n求两个整数的和。',statementAvailable:true,samples:[{input:'1 2\n',output:'3\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1,label:'样例评测'},draft:'// isolated retained code\nint main(){return 0;}\n',draftSavedAt:now,submissions:[]};
  else if (name === 'training/start') value = {workspace};
  else if (name === 'initial-code') value = {selection:{cpp17:'default',python3:'default'},revisions:{cpp17:'r1',python3:'r1'},templates:[{id:'default',title:'默认',builtin:true,language:'cpp17',code:'int main(){return 0;}'},{id:'default',title:'默认',builtin:true,language:'python3',code:'print(0)'}]};
  else if (name === 'draft') value = {savedAt:now};
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

const promotion = page.getByRole('status', {name:'段位晋升',exact:true});
try {
 await page.goto(server.resolvedUrls.local[0]);
 await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='11');
 await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 await page.locator('tr[data-id="fixture::A"]').first().click();
 const editor=page.locator('.study-browser .cm-content');await editor.waitFor();
 await editor.click();await page.keyboard.press('Control+End');await page.keyboard.type('// preserve focus and code');
 const code=await editor.innerText(),oldInsightReads=insightReads;
 workspace.summary={...workspace.summary,attempts:1,pending:1};workspace.now=new Date(Date.now()+100).toISOString();
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await page.waitForResponse(response=>new URL(response.url()).pathname==='/api/workspace'&&response.ok());
 ability=1000;workspace.summary={...workspace.summary,accepted:1,pending:0};workspace.training=[{...workspace.training[0],accepted:true,verdict:'AC',attempts:1,lastSubmittedAt:new Date().toISOString()}];workspace.now=new Date(Date.now()+500).toISOString();
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await promotion.waitFor();
 assert(insightReads>oldInsightReads);assert.match(await promotion.innerText(),/白银/);
 assert(await editor.evaluate(node=>node.contains(document.activeElement)||node===document.activeElement));
 assert.equal(await editor.innerText(),code);assert.equal(await page.locator('.study-browser').count(),1);
 await page.screenshot({path:out+'/after-ac-in-study.png'});
 await page.keyboard.press('Escape');await promotion.waitFor({state:'detached'});
 assert.equal(await page.locator('.study-browser').count(),1,'Esc skips promotion while preserving the problem workspace');
 assert.equal(await editor.innerText(),code);
 assert.equal(await page.getByRole('dialog',{name:'等级提升',exact:true}).count(),0);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={ok:true,productionBundle:production,confirmedGrowthAfterWorkspaceUpdate:true,actualAppStudyWorkspace:true,editorFocusAndCodePreserved:true,escapePreservesStudy:true,noXpDialogCollision:true,insightReads,workspaceReads,errors,external};
 await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
} catch(error) {await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.json',JSON.stringify({error:error.stack,errors,external,insightReads,workspaceReads},null,2));throw error;}
finally {await browser.close();await server.close();}
