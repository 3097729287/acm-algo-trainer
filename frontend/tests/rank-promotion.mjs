import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
const out = '../.backups/rank-promotion-20261106'; await mkdir(out, {recursive: true});
const server = await createServer({cacheDir: out + '/vite', optimizeDeps: {entries: ['tests/rank-promotion-fixture.html']}, server: {host: '127.0.0.1', port: 0, watch: null}}); await server.listen();
const browser = await chromium.launch({channel: process.env.CI ? undefined : 'msedge', headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 960}}), errors = [], proof = [];
page.setDefaultTimeout(10000); page.on('pageerror', error => errors.push(error.message));
const base = server.resolvedUrls.local[0], stage = () => page.getByRole('status', {name: '段位晋升', exact: true});
const emit = (rank, revision, options = {}) => page.evaluate(([rank, revision, options]) => rankFixture.emit(rank, revision, options), [rank, revision, options]);
const snapshot = () => page.evaluate(() => rankFixture.snapshot());
const skip = async () => {await page.keyboard.press('Escape'); await stage().waitFor({state: 'detached'});};
try {
 await page.goto(base + 'tests/rank-promotion-fixture.html'); await page.getByRole('textbox').waitFor();
 await page.waitForTimeout(300); assert.equal(await stage().count(), 0);
 const draft = page.getByRole('textbox', {name: '练习草稿'}); await draft.fill('// saved while solving');
 await emit(2, 2); await draft.press('End'); await draft.press('A'); await page.waitForTimeout(150);
 assert.equal(await stage().count(), 0, 'Active input queues the promotion');
 await stage().waitFor(); assert(await draft.evaluate(node => document.activeElement === node), 'Promotion does not steal editor focus');
 assert.match(await stage().innerText(), /白银/); await page.waitForTimeout(1900);
 assert.equal((await snapshot()).receipt.pending, null, 'Actually revealed rank is acknowledged');
 assert.equal(await draft.inputValue(), '// saved while solvingA'); await skip();
 await page.reload(); await draft.waitFor(); await page.waitForTimeout(450); assert.equal(await stage().count(), 0);
 proof.push({liveRankIncrease: true, typingDeferred: true, editorFocusAndCodePreserved: true, acknowledgedAfterReveal: true, reloadDoesNotReplay: true});
 await emit(2, 3, {score: 1040}); await page.waitForTimeout(100); assert.equal(await stage().count(), 0);
 await page.evaluate(() => rankFixture.block(true)); await emit(3, 4); await emit(5, 5); assert.equal(await stage().count(), 0);
 await page.reload(); await draft.waitFor(); assert.equal(await stage().count(), 0);
 await page.evaluate(() => rankFixture.block(false)); await stage().waitFor(); assert.equal((await snapshot()).notice.from, 2); assert.equal((await snapshot()).notice.to, 5); await skip();
 await page.evaluate(() => rankFixture.other(true)); await emit(6, 6); await page.waitForTimeout(350); assert.equal(await stage().count(), 0);
 await page.getByRole('button', {name: '关闭其它弹窗'}).click(); await stage().waitFor(); await skip();
 proof.push({withinTierSilent: true, contestOrJudgingDeferred: true, multipleRanksMerged: true, pendingSurvivesReload: true, otherDialogWaits: true});
 await page.evaluate(() => {Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange'));});
 await emit(7, 7); await page.waitForTimeout(300); assert.equal(await stage().count(), 0);
 await page.evaluate(() => {delete document.hidden; document.dispatchEvent(new Event('visibilitychange'));});
 await stage().waitFor(); await page.waitForTimeout(200);
 await page.evaluate(() => {Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange'));});
 await stage().waitFor({state: 'detached'}); assert((await snapshot()).receipt.pending);
 await page.evaluate(() => {delete document.hidden; document.dispatchEvent(new Event('visibilitychange'));});
 await stage().waitFor(); await skip();
 await page.evaluate(() => rankFixture.switchOwner('second-owner', 4)); await page.waitForTimeout(200); assert.equal(await stage().count(), 0);
 await emit(8, 999, {owner: 'rank-owner'}); await page.waitForTimeout(150); assert.equal(await stage().count(), 0);
 await draft.focus(); await emit(5, 2); await stage().waitFor();
 await stage().getByRole('button',{name:'跳过段位晋升动画',exact:true}).click(); await stage().waitFor({state:'detached'});
 assert(await draft.evaluate(node=>document.activeElement===node),'Clicking skip restores the original editor focus');
 proof.push({hiddenDefers: true, hiddenBeforeRevealNotAcknowledged: true, foregroundResumes: true, accountBaselineSilent: true, foreignOwnerIgnored: true});
 await page.getByRole('button', {name: '离开编辑器'}).click(); await draft.dispatchEvent('compositionstart'); await emit(6, 3, {level: 12});
 await page.waitForTimeout(900); assert.equal(await stage().count(),0,'IME composition waits even after the ordinary input idle time');
 await draft.dispatchEvent('compositionend'); await stage().waitFor();
 assert.equal(await page.getByRole('dialog', {name: '等级提升'}).count(), 0); await skip();
 await page.getByRole('dialog', {name: '等级提升'}).waitFor(); await page.keyboard.press('Escape');
 proof.push({rankAndLevelSerialize: true, imeCompositionWaits:true, skipRestoresFocus:true});
 for (const [width, theme] of [[1440, 'dark'], [1440, 'light'], [430, 'dark'], [430, 'light']]) {
  await page.setViewportSize({width, height: 850}); await page.evaluate(theme => {rankFixture.theme(theme); document.documentElement.style.fontSize = '22px';}, theme);
  await page.evaluate(() => rankFixture.reset(2, 3, 40)); await page.reload(); await stage().waitFor();
  await page.evaluate(theme => {rankFixture.theme(theme); document.documentElement.style.fontSize = '22px';}, theme);
  await stage().evaluate(node => {for (const animation of node.getAnimations({subtree: true})) {animation.pause(); animation.currentTime = 2400;}});
  const geometry = await stage().evaluate(node => {const rect = node.getBoundingClientRect(), result = node.querySelector('.promotion-result').getBoundingClientRect(); return {width: rect.width, height: rect.height, resultFits: result.left >= 0 && result.right <= innerWidth && result.top >= 0 && result.bottom <= innerHeight, opacity: getComputedStyle(node.querySelector('.promotion-complete')).opacity, pieces: getComputedStyle(node.querySelector('.promotion-pieces')).opacity};});
  assert(geometry.resultFits); assert.equal(geometry.opacity, '1'); assert.equal(geometry.pieces, '0');
  await page.screenshot({path: `${out}/promotion-${width}-${theme}.png`}); proof.push({width, theme, ...geometry}); await skip();
 }
 await page.setViewportSize({width:1440,height:960});
 await page.evaluate(() => rankFixture.reset(3, 4, 45)); await page.reload(); await stage().waitFor();
 for (const phase of [180,750,1250,1850,2500,4100]) {
  await stage().evaluate((node,phase) => {for (const animation of node.getAnimations({subtree:true})) {animation.pause();animation.currentTime=phase;}}, phase);
  if (phase===1250) assert.notEqual(await stage().locator('.piece-left').evaluate(node=>getComputedStyle(node).transform),'matrix(1, 0, 0, 1, 0, 0)','The new crest wings move into place');
  await page.screenshot({path:`${out}/phase-${phase}.png`});
 }
 await skip(); proof.push({chargeForgeAndRevealFrames:true,wingMotion:true,settledPartsAligned:true});
 for (const reduced of ['os', 'app']) {
  if (reduced === 'os') await page.emulateMedia({reducedMotion: 'reduce'});
  await page.evaluate(() => rankFixture.reset(5, 6, 50)); await page.reload();
  if (reduced === 'app') await page.evaluate(() => rankFixture.motion(false));
  await stage().waitFor(); await page.waitForTimeout(100);
  assert.equal(await stage().evaluate(node => node.getAnimations({subtree: true}).filter(animation => animation.playState === 'running').length), 0);
  assert.equal(await stage().locator('.promotion-complete').evaluate(node => getComputedStyle(node).opacity), '1');
  await skip(); await page.emulateMedia({reducedMotion: 'no-preference'}); proof.push({reducedMotion: reduced, staticReveal: true});
 }
 await page.evaluate(() => rankFixture.reset(7, 8, 60)); await page.reload(); await stage().waitFor();
 const timing=await page.evaluate(()=>new Promise(resolve=>{const values=[];let previous;const sample=now=>{if(previous!==undefined)values.push(now-previous);previous=now;if(values.length<90)requestAnimationFrame(sample);else{const sorted=[...values].sort((a,b)=>a-b);resolve({frames:values.length,medianMs:sorted[Math.floor(sorted.length*.5)],p95Ms:sorted[Math.floor(sorted.length*.95)],maxMs:sorted.at(-1)});}};requestAnimationFrame(sample);}));
 proof.push({realtimeAnimation:timing});
 await stage().waitFor({state: 'detached', timeout: 6500}); assert.equal((await snapshot()).receipt.pending, null);
 assert.deepEqual(errors, []); const result = {ok: true, proof, errors}; await writeFile(out + '/ui-checks.json', JSON.stringify(result, null, 2)); console.log(JSON.stringify({ok: true, cases: proof.length, errors}));
} catch (error) {await page.screenshot({path: out + '/failure.png'}); await writeFile(out + '/failure.json', JSON.stringify({error: error.stack, errors, state: await snapshot().catch(() => null)}, null, 2)); throw error;}
finally {await browser.close(); await server.close();}
