import assert from 'node:assert/strict';
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, mkdtemp, writeFile, stat } from 'node:fs/promises';
import { createServer } from 'node:net';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { exerciseNativePlanning } from './native-learning-flow.mjs';
import { exerciseNativeRuns } from './native-run-flow.mjs';
import { exerciseNativeReviews } from './native-review-flow.mjs';
import { exerciseNativeContestHistory } from './native-contest-history-flow.mjs';
import { exerciseNativeAssets } from './native-assets-flow.mjs';
import { exerciseNativeGoals } from './native-goals-flow.mjs';
import { exerciseNativeReviewedContent } from './native-reviewed-content-flow.mjs';
import { exerciseNativeContestLifecycle } from './native-contest-lifecycle-flow.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const packaged = process.argv.includes('--packaged');
const output = resolve(process.env.TB_NATIVE_WINDOW_OUTPUT || resolve(root, packaged ? '.backups/native-window-packaged' : '.backups/native-window'));
await mkdir(output, { recursive: true });
const sandbox = await mkdtemp(resolve(output, 'sandbox-'));
const binary = resolve(process.argv[2] || resolve(root, 'target/release/tobe-desktop.exe'));
const listener = createServer();
await new Promise(resolve => listener.listen(0, '127.0.0.1', resolve));
const port = listener.address().port;
await new Promise(resolve => listener.close(resolve));
const start = performance.now();
const runtimeEnvironment = { ...process.env,
  TB_NATIVE_SANDBOX_DIR: sandbox,
  WEBVIEW2_USER_DATA_FOLDER: resolve(sandbox, 'webview'),
  WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`,
};
if (packaged) delete runtimeEnvironment.TB_NATIVE_SOURCE_ROOT;
else runtimeEnvironment.TB_NATIVE_SOURCE_ROOT = root;
const child = spawn(binary, [], { windowsHide: true, cwd: packaged ? sandbox : root, env: runtimeEnvironment });
let launchError;
let nativeStderr = '';
child.stderr?.on('data', data => { nativeStderr = (nativeStderr + data).slice(-8192); });
child.on('error', error => { launchError = error; });
let browser;
const failures = [], consoleErrors = [];
try {
  const deadline = Date.now() + 45000;
  while (true) {
    if (launchError) throw launchError;
    if (child.exitCode !== null) throw new Error(`Native window exited during startup: ${child.exitCode}`);
    try { const response = await fetch(`http://127.0.0.1:${port}/json/version`); if (response.ok) break; } catch {}
    if (Date.now() > deadline) throw new Error('Native WebView2 debugging endpoint did not appear');
    await delay(200);
  }
  browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
  let page;
  for (let attempt = 0; attempt < 100; attempt++) {
    page = browser.contexts().flatMap(context => context.pages()).find(page => /native-check/.test(page.url()));
    if (page) break;
    await delay(100);
  }
  assert.ok(page, 'Tauri must load its bundled React entrypoint');
  page.on('pageerror', error => failures.push(error.message));
  page.on('console', event => { if (event.type() === 'error') consoleErrors.push(event.text()); });
  await page.getByRole('heading', { name: /现有题库/ }).waitFor();
  await page.getByRole('listitem').first().waitFor();
  const readyMillis = performance.now() - start;
  const results = await page.evaluate(async () => {
    const invoke = window.__TAURI__.core.invoke;
    let id = 0;
    const rpc = async (path, query = {}, body, token) => {
      const request = { version: 1, id: `window-${++id}`, method: body === undefined ? 'GET' : 'POST', path, query,
        ...(body === undefined ? {} : { body }), ...(token ? { token } : {}) };
      const response = await invoke('api_request', { request });
      if (!response.ok) throw new Error(JSON.stringify(response.error));
      return response;
    };
    const capabilities = (await rpc('api/capabilities')).data;
    const account = (await rpc('account')).data;
    const beforeFullscreen = (await rpc('desktop/fullscreen')).data;
    if (!beforeFullscreen.available) throw new Error('Native fullscreen controller is missing');
    const toggledFullscreen = (await rpc('desktop/fullscreen', {}, { fullscreen: !beforeFullscreen.fullscreen }, account.token)).data;
    if (toggledFullscreen.fullscreen === beforeFullscreen.fullscreen) throw new Error('The actual native window did not toggle fullscreen');
    const queriedFullscreen = (await rpc('desktop/fullscreen')).data;
    if (queriedFullscreen.fullscreen !== toggledFullscreen.fullscreen) throw new Error('Native fullscreen state was not read from the window');
    const restoredFullscreen = (await rpc('desktop/fullscreen', {}, { fullscreen: beforeFullscreen.fullscreen }, account.token)).data;
    if (restoredFullscreen.fullscreen !== beforeFullscreen.fullscreen) throw new Error('Native fullscreen state was not restored');
    const catalog = (await rpc('library/page', { limit: ['30'] })).data;
    const original = (await rpc('library/statement', { id: [catalog.rows[0].id] })).data;
    const draft = await rpc('draft', {}, { id: catalog.rows[0].id, code: 'int main() { return 0; }', language: 'cpp17' }, account.token);
    if (!draft.data.savedAt) throw new Error('Native draft was not committed');
    const durations = [];
    for (let count = 0; count < 30; count++) {
      const before = performance.now();
      await rpc('initial-code');
      durations.push(performance.now() - before);
    }
    durations.sort((a,b) => a-b);
    return { capabilities, fullscreen: { before: beforeFullscreen, toggled: toggledFullscreen, restored: restoredFullscreen }, totalProblems: catalog.total, originalTitle: original.title,
      draftCommitted: true, ipcInitialCodeP50Millis: durations[15], ipcInitialCodeP95Millis: durations[28],
      origin: location.origin, nativeGlobal: Boolean(window.__TAURI_INTERNALS__) };
  });
  assert.ok(results.nativeGlobal);
  assert.equal(results.capabilities.releaseReady, false);
  assert.ok(results.totalProblems > 10000);
  const snapshotScript = `$all = Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name; $ids = [System.Collections.Generic.HashSet[int]]::new(); [void]$ids.Add(${child.pid}); do { $changed = $false; foreach ($item in $all) { if ($ids.Contains([int]$item.ParentProcessId) -and $ids.Add([int]$item.ProcessId)) { $changed = $true } } } while ($changed); $rows = foreach ($item in $all) { if ($ids.Contains([int]$item.ProcessId)) { $p = Get-Process -Id $item.ProcessId -ErrorAction SilentlyContinue; if ($p) { [PSCustomObject]@{ name=$item.Name; pid=$item.ProcessId; workingSetBytes=$p.WorkingSet64; privateBytes=$p.PrivateMemorySize64 } } } }; ConvertTo-Json -InputObject @($rows) -Compress`;
  const memory = JSON.parse((await promisify(execFile)('powershell.exe', ['-NoProfile', '-Command', snapshotScript], { windowsHide: true })).stdout);
  await page.getByRole('listitem').first().click();
  await page.locator('.native-reading pre').waitFor();
  await page.screenshot({ path: resolve(output, 'wide.png') });
  await page.getByRole('button', { name: '打开本地测试工作区', exact: true }).click();
  await page.locator('.sidebar').first().waitFor();
  await page.locator('.problem-title').filter({ hasText: results.originalTitle }).first().waitFor();
  await page.locator('.problem-title').filter({ hasText: results.originalTitle }).first().click();
  const editor = page.getByRole('textbox', { name: 'C++ 代码', exact: true });
  await page.locator('.tb-workbench').waitFor();
  if (!await editor.isVisible()) await page.keyboard.press('Alt+2');
  await editor.waitFor();
  const savedCode = '// Native React editor persistence\nint main() { return 0; }\n';
  await editor.fill(savedCode);
  await editor.press('Control+s');
  await page.waitForFunction(() => document.querySelector('.wb-save-state')?.textContent.includes('已保存') || document.body.innerText.includes('草稿已保存'));
  const saved = await page.evaluate(async () => {
    const invoke = window.__TAURI__.core.invoke;
    const base = { version: 1, method: 'GET', query: {} };
    const workspace = await invoke('api_request', { request: { ...base, id: 'workspace-check', path: 'workspace' } });
    const id = workspace.data.training[0].id;
    const result = await invoke('api_request', { request: { ...base, id: 'draft-check', path: 'problem', query: { id: [id] } } });
    return { code: result.data.draft, id, training: workspace.data.training.length };
  });
  assert.equal(saved.code, savedCode);
  await page.screenshot({ path: resolve(output, 'react-workspace-wide.png') });
  await page.reload();
  await page.locator('.tb-workbench:visible').waitFor();
  if (!await editor.isVisible()) await page.keyboard.press('Alt+2');
  await editor.waitFor();
  assert.equal((await editor.innerText()).trimEnd(), savedCode.trimEnd());
  if(process.env.TB_NATIVE_TEST_GOALS==='1')results.goals=await exerciseNativeGoals(page,output,results.originalTitle);
  results.reactPlanning = await exerciseNativePlanning(page, output);
  await page.locator('.sidebar').getByRole('button', { name: '我的训练', exact: true }).click();
  await page.locator('.problem-title').filter({ hasText: results.originalTitle }).first().click();
  await editor.waitFor();
  await page.setViewportSize({ width: 800, height: 650 });
  await page.screenshot({ path: resolve(output, 'react-workspace-narrow.png') });
  results.reactWorkspace = { saved: true, recoveredAfterReload: true, training: saved.training, problemId: saved.id };
  if(process.env.TB_NATIVE_TEST_RUNNER==='1')results.localRuns=await exerciseNativeRuns(page,output);
  if(process.env.TB_NATIVE_TEST_REVIEWS==='1')results.reviews=await exerciseNativeReviews(page,output,sandbox,process.env.TB_NATIVE_TEST_PYTHON);
  if(process.env.TB_NATIVE_TEST_CONTEST_HISTORY==='1')results.contestHistory=await exerciseNativeContestHistory(page,output,sandbox,process.env.TB_NATIVE_TEST_PYTHON);
  if(process.env.TB_NATIVE_TEST_CONTEST_LIFECYCLE==='1')results.contestLifecycle=await exerciseNativeContestLifecycle(page,output,sandbox,process.env.TB_NATIVE_TEST_PYTHON);
  if(process.env.TB_NATIVE_TEST_ASSETS==='1')results.assets=await exerciseNativeAssets(page,output);
  if(process.env.TB_NATIVE_TEST_CONTENT1610==='1')results.reviewedContent=await exerciseNativeReviewedContent(page,output);
  assert.equal(results.capabilities.deployment, 'local-test-only');
  assert.equal(results.capabilities.formalArchitecture, 'react-python');
  assert.deepEqual(failures, []);
  await writeFile(resolve(output, 'result.json'), JSON.stringify({ ...results, readyMillis, memory,
    binaryBytes: (await stat(binary)).size, binary, sandbox, packaged, pageErrors: failures,
    scope: 'Native migration diagnostic; feature parity and full application resource comparison are still pending' }, null, 2) + '\n');
  console.log(`Native Tauri/WebView2 IPC passed: ${results.totalProblems} real problems, committed draft, wide/narrow screenshots; ${resolve(output, 'result.json')}`);
} catch (error) {
  await writeFile(resolve(output, 'failure-runtime.json'), JSON.stringify({ error: String(error), exitCode: child.exitCode, signal: child.signalCode, nativeStderr }, null, 2));
  const page = browser?.contexts().flatMap(context => context.pages())[0];
  if (page) {
    await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {});
    await writeFile(resolve(output, 'failure.txt'), await page.locator('body').innerText()).catch(() => {});
    await writeFile(resolve(output, 'failure.json'), JSON.stringify({ failures, consoleErrors, dom: await page.evaluate(() => ({
      innerWidth, width: document.documentElement.clientWidth, workbenches: [...document.querySelectorAll('.tb-workbench')].map(node => ({className:node.className,problemId:node.dataset.problemId,visible:node.getClientRects().length>0})),
      studyOpen:document.querySelector('.app-shell')?.dataset.studyOpen,workspacePage:document.querySelector('.workspace-area')?.dataset.page,
      textboxes: [...document.querySelectorAll('[role=textbox]')].map(node => ({ label: node.getAttribute('aria-label'), rect: node.getBoundingClientRect().toJSON() })),
      layout: [...document.querySelectorAll('.wb-layout-toggle')].map(node => ({label: node.getAttribute('aria-label'), pressed: node.getAttribute('aria-pressed')})),
    })) }, null, 2)).catch(() => {});
  }
  throw error;
} finally {
  if (browser) await browser.close();
  child.kill();
}
