import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { luoguComboFixture } from './luogu-combo-fixture.mjs';

const source = await readFile(new URL('../../desktop/official_languages.js', import.meta.url), 'utf8');
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage();
try {
  const native = [
    ['Codeforces', '<select name="programTypeId"><option value="4">GNU G++14 6.4.0</option><option value="54">GNU G++17 7.3.0</option><option value="89">GNU G++20 13.2</option></select>', '54', 'int main(){}'],
    ['Codeforces', '<select name="programTypeId"><option value="54">GNU G++17 7.3.0</option><option value="89">GNU G++20 13.2</option></select>', '89', '#include <ranges>\nint main(){}'],
    ['AtCoder', '<select id="select-lang" name="data.LanguageId" style="display:none"><option value="old">C++14 (GCC 5.4.1)</option><option value="17">C++17 (GCC 12.2)</option><option value="20">C++20 (GCC 12.2)</option></select>', '17', 'int main(){}'],
    ['洛谷', '<select name="language"><option value="cpp">C++14</option><option value="cpp17">C++17</option><option value="cpp20">C++20</option></select>', 'cpp17', 'int main(){}'],
    ['洛谷', '<select><option value="java">Java 21</option><option value="12">C++17</option><option value="28">C++20</option></select>', '12', '#include <stdio.h>\nint main(){printf("0");}'],
    ['洛谷', '<select><option value="cpp14">C++14</option><option value="12" selected>C++17</option><option value="28">C++20</option></select>', '12', 'int main(){}'],
  ];
  for (const [platform, html, expected, code] of native) {
    await page.setContent(html);
    await page.addScriptTag({ content: source });
    const result = await page.evaluate(({ platform, code }) => selectOfficialCompiler(code, platform), { platform, code });
    assert.ok(result, platform);
    assert.equal(await page.locator('select').inputValue(), expected, platform);
  }
  // Actual Luogu 2026 DOM has no select/combobox role; options are teleported.
  for(const current of ['C++23','Java 21','C++98']){
    const combo=luoguComboFixture(current);
    await page.setContent(combo.html);
    await page.addScriptTag({content:combo.script});await page.addScriptTag({content:source});
    const result=await page.evaluate(()=>selectOfficialCompiler('int main(){}','洛谷'));
    assert.ok(result,'Luogu actual ComboBox must be recognized: '+current);
    assert.equal(await page.evaluate(()=>fixtureLang),current==='C++23'?28:12);
    assert.equal(await page.evaluate(()=>fixtureLanguageClicks),current==='C++23'?0:1);
  }
  const pythonCombo=luoguComboFixture();
  await page.setContent(pythonCombo.html);await page.addScriptTag({content:pythonCombo.script});await page.addScriptTag({content:source});
  assert.equal((await page.evaluate(()=>selectOfficialCompiler('print(42)','洛谷','python3'))).language,'python3');
  assert.equal(await page.evaluate(()=>fixtureLang),7);
  const legacyCombo=luoguComboFixture('C++98',['C++98','C++14']);
  await page.setContent(legacyCombo.html+'<div class="dropdown"><ul><li>C++23</li></ul></div>');
  await page.addScriptTag({content:legacyCombo.script});await page.addScriptTag({content:source});
  assert.equal(await page.evaluate(()=>selectOfficialCompiler('int main(){}','洛谷')),null,'Legacy-only language menu and unrelated open dropdown must not be accepted');
  // Custom controls dispatch ordinary clicks and confirm the visible selection.
  for (const label of ['Java 17', 'C++(g++ 13)']) {
    await page.setContent(`<div class="nc-select language-select"><button class="nc-select-label">${label}</button><ul hidden><li class="nc-select-item">C++(g++ 4.8)</li><li class="nc-select-item">C++(g++ 13)</li><li class="nc-select-item">Java 17</li></ul></div>`);
    await page.addScriptTag({ content: `document.querySelector('button').onclick=()=>document.querySelector('ul').hidden=false; document.querySelectorAll('li').forEach(node=>node.onclick=()=>{document.querySelector('button').textContent=node.textContent;document.querySelector('ul').hidden=true;});` });
    await page.addScriptTag({ content: source });
    const result = await page.evaluate(() => selectOfficialCompiler('int main(){}', '牛客'));
    assert.equal(result.standard, 17);
    assert.equal(result.compilerVersion, 13);
    assert.equal(await page.locator('button').textContent(), 'C++(g++ 13)');
  }
  // Actual Nowcoder 2026 DOM: Element UI readonly input, full-width parentheses.
  for (const label of ['Java', 'C++（clang++18）']) {
    await page.setContent(`<div class="el-select el-select--small btn-language"><div class="el-input"><input class="el-input__inner" readonly value="${label}"></div><ul class="el-select-dropdown" hidden><li class="el-select-dropdown__item">C++（clang++18）</li><li class="el-select-dropdown__item">C++(g++ 13)</li><li class="el-select-dropdown__item">Java</li></ul></div>`);
    await page.addScriptTag({ content: `document.querySelector('input').onclick=()=>document.querySelector('ul').hidden=false; document.querySelectorAll('li').forEach(node=>node.onclick=()=>{document.querySelector('input').value=node.textContent;document.querySelector('ul').hidden=true;});` });
    await page.addScriptTag({ content: source });
    const result = await page.evaluate(() => selectOfficialCompiler('int main(){}', '牛客'));
    assert.equal(result.standard, 17);
    assert.equal(result.compilerVersion, 18);
    assert.equal(await page.locator('input').inputValue(), 'C++（clang++18）');
    assert.equal(await page.evaluate(() => selectOfficialCompiler('#include <ranges>\nint main(){}', '牛客')), null);
  }
  await page.setContent('<select name="language"><option>Java 17</option><option>C++14</option></select><p>GNU G++20 13.2</p>');
  await page.addScriptTag({ content: source });
  assert.equal(await page.evaluate(() => selectOfficialCompiler('int main(){}', '牛客')), null);
  assert.equal(await page.evaluate(() => compilerCandidate('C++(g++ 13)', '#include <ranges>', '牛客')), null);
  for(const platform of ['Codeforces','AtCoder','牛客','洛谷']){
    await page.setContent('<select name="language"><option value="cpp">GNU C++17</option><option value="py2">Python 2.7</option><option value="pypy">PyPy 3.10</option><option value="py">Python 3.13</option></select>');
    await page.addScriptTag({content:source});
    const language=await page.evaluate(platform=>selectOfficialCompiler('print(42)',platform,'python3'),platform);
    assert.equal(language.language,'python3');assert.equal(await page.locator('select').inputValue(),'py');
  }
  await page.setContent('<select name="language"><option>Python 2.7</option><option>GNU C++17</option></select>');await page.addScriptTag({content:source});
  assert.equal(await page.evaluate(()=>selectOfficialCompiler('print(42)','Codeforces','python3')),null);
  console.log('Compiler adapters passed: Codeforces, AtCoder, Luogu, Nowcoder custom dropdown, standard requirements and unsupported options.');
} finally {
  await browser.close();
}
