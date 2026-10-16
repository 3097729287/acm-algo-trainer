import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { createServer } from 'vite';

const source = JSON.parse(await readFile('../data/library/detailed_solutions.json', 'utf8'));
const contests = new Set(['周赛 165', '周赛 164', '周赛 163', '周赛 162', 'Div.3 1125', 'Div.3 1122', 'Div.3 1119', 'Div.2 1127', 'Div.2 1124', 'Div.2 1123', 'Div.4 1090', 'Div.4 1074', 'Div.4 1062', 'ABC 479', 'ABC 478', 'ABC 477']);
const records = source.filter(row => contests.has(row.problem_id.split('::')[0]));
const defaults = JSON.parse(await readFile('../data/library/solutions.json', 'utf8'));
const expected = defaults.filter(row => contests.has(row.problem_id.split('::')[0]));
assert.ok(records.length >= 81);
assert.deepEqual(records.map(row => row.problem_id).sort(), expected.map(row => row.problem_id).sort());
const vite = await createServer({ server: { host: '127.0.0.1', port: 18780, strictPort: true } });
await vite.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const report = [];
try {
  const page = await browser.newPage({ viewport: { width: 1220, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:18780/tests/corpus-reading.html');
  await page.waitForFunction(() => typeof window.renderDocument === 'function');
  await mkdir('tests/screenshots/latest-editorials', { recursive: true });
  for (const record of records) {
    const result = await page.evaluate(row => window.renderDocument({ id: row.problem_id, markdown: row.markdown, images: row.images }), record);
    assert.deepEqual(result.mathErrors, [], record.problem_id + ': math');
    assert.deepEqual(result.missing, [], record.problem_id + ': images');
    report.push({ id: record.problem_id, ...result });
    if (['周赛 165::D', '周赛 165::E', '周赛 165::F', 'ABC 479::E', 'ABC 479::F', 'Div.2 1127::D'].includes(record.problem_id)) {
      const images = page.locator('.reading-image-open img');
      for (let index = 0; index < await images.count(); index++) {
        await images.nth(index).screenshot({ path: `tests/screenshots/latest-editorials/${record.problem_id.replace('::', '-')}-${index}.png` });
      }
    }
  }
  assert.deepEqual(errors, []);
  await writeFile('tests/screenshots/latest-editorials/report.json', JSON.stringify(report, null, 2));
  console.log(`Rendered ${records.length} detailed editorials; ${report.reduce((sum, row) => sum + row.math, 0)} formulas and ${report.reduce((sum, row) => sum + row.images, 0)} illustrations; no missing images or math errors.`);
} finally {
  await browser.close();
  await vite.close();
}
