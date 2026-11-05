import assert from 'node:assert/strict';
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, mkdtemp, writeFile, stat } from 'node:fs/promises';
import { createServer } from 'node:net';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const packaged = process.argv.includes('--packaged');
const output = resolve(root, packaged ? '.backups/native-window-packaged' : '.backups/native-window');
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
child.on('error', error => { launchError = error; });
let browser;
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
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
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
    return { capabilities, totalProblems: catalog.total, originalTitle: original.title,
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
  await page.setViewportSize({ width: 800, height: 650 });
  await page.screenshot({ path: resolve(output, 'narrow.png') });
  assert.deepEqual(failures, []);
  await writeFile(resolve(output, 'result.json'), JSON.stringify({ ...results, readyMillis, memory,
    binaryBytes: (await stat(binary)).size, binary, sandbox, packaged, pageErrors: failures,
    scope: 'Native migration diagnostic; feature parity and full application resource comparison are still pending' }, null, 2) + '\n');
  console.log(`Native Tauri/WebView2 IPC passed: ${results.totalProblems} real problems, committed draft, wide/narrow screenshots; ${resolve(output, 'result.json')}`);
} finally {
  if (browser) await browser.close();
  child.kill();
}
