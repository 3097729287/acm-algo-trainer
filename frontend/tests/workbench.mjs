import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const server = await createServer({ root, server: { host: '127.0.0.1', port: 18768, strictPort: true } });
await server.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1050, height: 700 } });
await page.context().grantPermissions(['clipboard-read','clipboard-write']);
await page.addInitScript(() => {
  window.acceptedTones = 0;
  const create = AudioContext.prototype.createOscillator;
  AudioContext.prototype.createOscillator = function() { window.acceptedTones++; return create.apply(this, arguments); };
});
const errors = [];
page.on('pageerror', error => errors.push(error.message));
try {
  await page.goto('http://127.0.0.1:18768/tests/workbench-fixture.html');
  const editor = page.getByRole('textbox', { name: 'C++ 代码' });
  const clickReturnCorner=async label=>{
    const back=page.getByRole('button',{name:label,exact:true});
    const point=await back.evaluate(button=>{
      // This standalone fixture has an outer rounded border. Use its first
      // painted top-left pixels; the full-window App case checks (1,1).
      const header=button.closest('.wb-compact-toolbar,.wb-pane-header'),rect=header.getBoundingClientRect(),x=rect.left+8,y=rect.top+1;
      return {x,y,hit:button.contains(document.elementFromPoint(x,y))};
    });
    assert(point.hit,'The upper-left header corner belongs to the actual return button: '+JSON.stringify({label,point}));
    const previous=await page.evaluate(()=>window.workbenchFixture.exitCount);
    await page.mouse.click(point.x,point.y);
    await page.waitForFunction(count=>window.workbenchFixture.exitCount===count+1,previous);
  };
  await editor.waitFor({ state: 'visible' });
  await page.waitForFunction(() => document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true');
  await editor.focus();
  assert.equal(await page.locator('.cm-editor').evaluate(node=>getComputedStyle(node).outlineStyle),'none');
  assert.ok(await page.locator('.wb-statement .katex').count() >= 3);
  const fontSize = page.getByRole('spinbutton', { name: '题面字号', exact: true });
  const setReadingSize = async value => { await fontSize.fill(value); await fontSize.press('Tab'); };
  const readingMetrics = () => page.evaluate(() => {
    const size = selector => parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
    return { prose: size('.wb-statement p'), math: size('.wb-statement .katex'), sample: size('.wb-statement pre'), editor: size('.cm-content'), toolbar: size('.wb-toolbar') };
  });
  const beforeSize = await readingMetrics();
  await setReadingSize('24');
  const enlarged = await readingMetrics();
  assert.equal(enlarged.prose, 24);
  assert.ok(enlarged.math > beforeSize.math && enlarged.sample > beforeSize.sample, 'formulas and samples follow the reading size');
  assert.equal(enlarged.editor, beforeSize.editor, 'reading size does not enlarge code');
  assert.equal(enlarged.toolbar, beforeSize.toolbar);
  await page.getByRole('button', { name: '放大题面字号', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('input[aria-label="题面字号"]').value === '25');
  assert.equal(await fontSize.inputValue(), '25');
  await page.getByRole('button', { name: '缩小题面字号', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('input[aria-label="题面字号"]').value === '24');
  assert.equal(await fontSize.inputValue(), '24');
  await page.reload();
  await editor.waitFor({ state: 'visible' });
  assert.equal(await fontSize.inputValue(), '24', 'reading size survives reopening');
  await setReadingSize('99');
  assert.equal(await fontSize.inputValue(), '32', 'reading size clamps typed values to its upper bound');
  assert.equal(await page.getByRole('button', { name: '放大题面字号', exact: true }).isDisabled(), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await setReadingSize('1');
  assert.equal(await fontSize.inputValue(), '14', 'reading size clamps typed values to its lower bound');
  assert.equal(await page.getByRole('button', { name: '缩小题面字号', exact: true }).isDisabled(), true);
  await setReadingSize('24');
  assert.equal(await page.locator('.wb-console').count(), 1, 'samples open on the first visit');
  assert.equal(await page.locator('.wb-sample-list .wb-result-message').count(),0,'The sample list has no redundant footer sentence');
  assert.equal(await page.getByText('运行会对比全部样例；通过样例不会计入已 AC。',{exact:true}).count(),0);
  assert.match(await page.locator('.wb-scope').getAttribute('title'),/仅使用公开样例/,'Removing the sample footer preserves the run-scope tooltip');
  await page.getByRole('button',{name:'收起控制台',exact:true}).click();
  assert.equal(await page.locator('.wb-console').count(),0);
  await page.getByRole('button',{name:'展开控制台',exact:true}).click();
  const splitter=page.getByRole('separator',{name:'调整题面与代码宽度'});
  const widths=()=>page.locator('.wb-body').evaluate(node=>[...node.querySelectorAll(':scope>.wb-statement-pane,:scope>.wb-code-pane')].map(p=>p.getBoundingClientRect().width));
  const initialWidths=await widths();assert(Math.abs(initialWidths[0]-initialWidths[1])<2,'first visit splits evenly');
  await splitter.focus();await splitter.press('ArrowRight');assert.equal(await splitter.getAttribute('aria-valuenow'),'52');
  await splitter.press('Home');assert((await widths())[0]>=319,'statement keeps its minimum usable width');
  await splitter.press('End');assert((await widths())[1]>=319,'code keeps its minimum usable width');
  const bodyBox=await page.locator('.wb-body').boundingBox(),handleBox=await splitter.boundingBox();
  await page.mouse.move(handleBox.x+4,handleBox.y+80);await page.mouse.down();await page.mouse.move(bodyBox.x+bodyBox.width*.6,handleBox.y+80);await page.mouse.up();
  assert(Math.abs(Number(await splitter.getAttribute('aria-valuenow'))-60)<=1,'pointer drag changes the actual split');
  const beforeToggle=await page.evaluate(()=>window.workbenchFixture.readCode());
  assert.equal(await page.locator('.wb-layout-toggle').count(),0,'The desktop toolbar no longer includes a layout button');
  await editor.press('Alt+2');assert.equal(await page.locator('.wb-statement-pane').isVisible(),false);
  await editor.press('Alt+0');assert.equal(await page.locator('.wb-statement-pane').isVisible(),true);
  assert.equal(await page.evaluate(()=>window.workbenchFixture.readCode()),beforeToggle,'switching layout preserves the code document');
  assert(Math.abs(Number(await splitter.getAttribute('aria-valuenow'))-60)<=1,'split ratio survives layout toggling');
  assert.equal(await page.getByRole('link',{name:'在浏览器打开原题'}).innerText(),'','original link is icon-only');
  for(const width of [2048,1294,960,430]){
    await page.setViewportSize({width,height:800});
    await page.waitForFunction(expected=>document.querySelector('.tb-workbench').classList.contains('wb-compact')===expected,width<996);
    await clickReturnCorner('返回列表');
    if(width<996){
      assert.equal(await page.locator('.wb-compact-toolbar .wb-layout-toggle').count(),1);
      // Alt+2 previously selected the code pane. Resizing preserves that choice;
      // exercise both actual compact controls without assuming a fresh default.
      if(await page.getByRole('button',{name:'题面与代码',exact:true}).count())await page.getByRole('button',{name:'题面与代码',exact:true}).click();
      assert(await page.locator('.wb-statement').isVisible());
      await page.getByRole('button',{name:'只看代码',exact:true}).click();assert(await editor.isVisible());
    }
    else assert.equal(await page.locator('.wb-layout-toggle').count(),0);
    const nextAlignment=await page.locator('.wb-next-button').evaluate(button=>{
      const header=button.closest('.wb-editor-header'),bounds=header.getBoundingClientRect(),next=button.getBoundingClientRect(),style=getComputedStyle(header);
      return {rightGap:bounds.right-next.right,expected:parseFloat(style.paddingRight)+parseFloat(style.borderRightWidth),within:next.left>=bounds.left&&next.right<=bounds.right+.5};
    });
    assert(nextAlignment.within&&Math.abs(nextAlignment.rightGap-nextAlignment.expected)<1,'Next question remains at the right edge of the editor toolbar: '+JSON.stringify({width,...nextAlignment}));
    if(width<996){await page.getByRole('button',{name:'题面与代码',exact:true}).click();assert(await page.locator('.wb-statement').isVisible());}
    const sizes=await page.locator('.wb-pane-header button:not(.wb-back-button):visible,.wb-pane-header select:visible,.wb-pane-header input:visible,.wb-original-link:visible,.wb-compact-toolbar button:not(.wb-back-button):visible').evaluateAll(nodes=>nodes.filter(n=>!n.disabled).map(n=>({height:n.getBoundingClientRect().height,label:n.getAttribute('aria-label')})));
    assert(sizes.every(item=>Math.abs(item.height-30)<1),`toolbar controls align at ${width}: ${JSON.stringify(sizes)}`);
    if(width>=996)assert((await page.getByLabel('编程语言',{exact:true}).boundingBox()).width>=80,'language name keeps a usable width');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  }
  await page.setViewportSize({width:1050,height:700});await page.waitForFunction(()=>!document.querySelector('.wb-compact'));
  await editor.press('Alt+0');
  await page.getByRole('button',{name:'打开模板',exact:true}).click();
  const templateDialog=page.getByRole('dialog',{name:'模板',exact:true});await templateDialog.locator('.catalog-card').first().waitFor();
  assert.equal(await templateDialog.locator('.catalog-card-actions').count(),0,'insertion no longer needs a separate plus button');
  await templateDialog.getByRole('button',{name:'插入模板 并查集：路径压缩与按大小合并',exact:true}).click();
  await templateDialog.waitFor({state:'detached'});
  const inserted=await page.evaluate(()=>window.workbenchFixture.readCode());
  assert(inserted.indexOf('struct DSU')>inserted.indexOf('using namespace std;')&&inserted.indexOf('struct DSU')<inserted.indexOf('int main'),'single click inserts above main after headers');
  assert.equal((inserted.match(/#include <bits\/stdc\+\+\.h>/g)||[]).length,1);
  assert.equal((inserted.match(/using ll = long long;/g)||[]).length,1);
  assert(inserted.indexOf('using ll = long long;')<inserted.indexOf('struct DSU'),'runtime insertion keeps the existing alias above the new template');
  await page.getByRole('button',{name:'复制题面',exact:true}).click();
  const copiedStatement=(await page.evaluate(()=>navigator.clipboard.readText())).replaceAll('\r\n','\n');
  assert(copiedStatement.includes('Given two integers')&&copiedStatement.includes('$a+b$')&&copiedStatement.includes('4 5\n')&&copiedStatement.includes('9\n'),'copy includes the whole visible statement and every sample');
  assert.ok(await page.locator('.cm-line > span').count() > 0, 'C++ syntax uses colored tokens');
  await editor.fill('fori');
  await editor.press('Control+Space');
  await page.locator('.cm-tooltip-autocomplete').waitFor();
  await page.waitForTimeout(150);
  await editor.press('Tab');
  assert.ok((await page.evaluate(() => window.workbenchFixture.readCode())).startsWith('for (int'), 'C++ snippet completion inserts a loop');
  await editor.press('Control+f');
  await page.locator('.cm-search').waitFor();
  await page.locator('.cm-search input').first().press('Escape');

  await editor.fill('int main(){\n    return 0;\n}\n');
  await editor.press('Control+s');
  await page.waitForFunction(() => window.workbenchFixture.drafts['solo:A']?.startsWith('int main'));
  assert.equal(await page.locator('.wb-editor-header .wb-save-state').count(),0,'successful save has no permanent toolbar status');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.notices.filter(n=>n.message==='草稿已保存').length),1);
  await editor.fill('// automatic save stays quiet');
  await page.waitForFunction(()=>window.workbenchFixture.drafts['solo:A']==='// automatic save stays quiet');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.notices.length),1,'consecutive automatic saves are throttled');
  await page.evaluate(()=>window.workbenchFixture.draftError='Fixture disk unavailable');await editor.fill('int main(){return 0;}');await editor.press('Control+s');
  await page.locator('.wb-save-error[role=alert]').waitFor();assert.match(await page.locator('.wb-save-error').getAttribute('title'),/Fixture disk unavailable/);
  assert.equal(await page.evaluate(()=>window.workbenchFixture.notices.length),1,'failed saves never announce success');
  await page.evaluate(()=>window.workbenchFixture.draftError='');await editor.press('Control+s');
  await page.waitForFunction(()=>window.workbenchFixture.drafts['solo:A']==='int main(){return 0;}');
  await editor.fill('int main(){\n    return 0;\n}\n');await editor.press('Control+s');
  await page.evaluate(() => window.workbenchFixture.selectCode(0));
  await editor.press('Tab');
  assert.ok((await page.evaluate(() => window.workbenchFixture.readCode())).startsWith('    int main'), 'editor Tab indents');
  await editor.press('Control+Tab');
  assert.equal(await page.evaluate(() => document.activeElement.textContent.trim()), '输入与样例', 'keyboard can leave editor');

  // A save is in flight while the user changes questions. It must keep its
  // original ID and must not contaminate B, even when A is revisited quickly.
  await page.evaluate(() => { window.workbenchFixture.draftDelay = 450; });
  await editor.fill('draft A newest');
  await editor.press('Control+s');
  await page.evaluate(() => window.workbenchFixture.changeProblem('B'));
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '最长的路径');
  await editor.fill('draft B newest');
  await editor.press('Control+s');
  await page.evaluate(() => window.workbenchFixture.changeProblem('A'));
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '两数之和');
  assert.equal(await page.evaluate(() => window.workbenchFixture.readCode()), 'draft A newest');
  await editor.fill('draft A latest after revisit');
  await editor.press('Control+s');
  await page.waitForFunction(() => window.workbenchFixture.drafts['solo:A'] === 'draft A latest after revisit' && window.workbenchFixture.drafts['solo:B'] === 'draft B newest');

  // The first old A save is pending, an additional old A edit exists, and a
  // newly mounted A saves again. The old loop must not write after the new one.
  await page.evaluate(() => { window.workbenchFixture.draftDelay = 650; });
  await editor.fill('old A first in-flight');
  await editor.press('Control+s');
  await editor.fill('old A second dirty edit');
  await page.evaluate(() => window.workbenchFixture.changeProblem('B'));
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '最长的路径');
  await page.evaluate(() => window.workbenchFixture.changeProblem('A'));
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '两数之和');
  await editor.fill('reopened A final code');
  await editor.press('Control+s');
  await page.waitForFunction(() => window.workbenchFixture.drafts['solo:A'] === 'reopened A final code');
  await page.waitForTimeout(900);
  assert.equal(await page.evaluate(() => window.workbenchFixture.drafts['solo:A']), 'reopened A final code');
  await page.evaluate(() => { window.workbenchFixture.draftDelay = 15; });

  await page.getByRole('button', { name: '原文', exact: true }).click();
  await page.waitForFunction(()=>document.querySelector('.wb-statement')?.textContent.includes('A 的中文题面'));
  assert.equal(await page.locator('.wb-translation-note').count(),0,'successful translations have no redundant status line');
  assert.ok(await page.locator('.wb-statement').textContent().then(text => text.includes('A 的中文题面')));
  assert.equal(await page.locator('.wb-statement p').first().evaluate(node => parseFloat(getComputedStyle(node).fontSize)), 24, 'Chinese uses the same reading size');
  assert.equal(await page.evaluate(() => 'code' in window.workbenchFixture.calls.filter(call => call.path === 'problem/translate').at(-1).body), false, 'translation sends only problem identity');
  await page.getByRole('button', { name: '中文', exact: true }).click();
  assert.ok(await page.locator('.wb-statement').textContent().then(text => text.includes('Given two integers')));

  const translationCalls=await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>call.path==='problem/translate').length);
  await page.evaluate(()=>{window.workbenchFixture.problemOverrides.E={title:'离线预置翻译',markdown:'Given a positive integer, print twice its value.',translation:{kind:'bundled',targetLanguage:'zh-CN',markdown:'给定一个正整数，输出它的两倍。',provider:'预置中文译文'}};window.workbenchFixture.changeProblem('E');});
  await page.waitForFunction(()=>document.querySelector('.wb-statement')?.textContent.includes('Given a positive integer'));
  await page.getByRole('button',{name:'原文',exact:true}).click();
  await page.getByRole('button',{name:'中文',exact:true}).waitFor();
  assert.match(await page.locator('.wb-statement').textContent(),/给定一个正整数/);
  await page.getByRole('button',{name:'中文',exact:true}).click();
  assert.match(await page.locator('.wb-statement').textContent(),/Given a positive integer/);
  assert.equal(await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>call.path==='problem/translate').length),translationCalls,'prebuilt text needs no provider request');
  await page.evaluate(()=>window.workbenchFixture.changeProblem('A'));
  await page.waitForFunction(()=>document.querySelector('.wb-heading strong').textContent==='两数之和');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.readCode()),'reopened A final code');

  await editor.press('Control+r');
  await page.waitForFunction(() => document.querySelector('.wb-result-summary')?.textContent.includes('样例通过'));
  assert.equal(await page.locator('.wb-case').count(), 2, 'all official samples are compared');
  assert.equal(await page.locator('.wb-case-mismatch').count(), 0, 'CRLF difference is not flagged');
  assert.equal(await page.evaluate(() => window.workbenchFixture.calls.filter(call => call.path === 'submissions').at(-1).body.sampleRun), true);
  assert.equal(await page.evaluate(() => window.workbenchFixture.progress.length), 0, 'running does not report accepted progress');

  await page.evaluate(() => { window.workbenchFixture.nextRunVerdict = 'WA'; });
  await editor.press('Control+r');
  await page.waitForFunction(() => document.querySelector('.wb-result-summary .wb-verdict-wa')?.textContent.trim() === 'WA');
  assert.ok(await page.locator('.wb-result-summary .wb-verdict-wa').evaluate(node => parseFloat(getComputedStyle(node).fontSize) >= 32));
  assert.equal(await page.locator('.wb-result-summary .wb-verdict-wa').evaluate(node => getComputedStyle(node).color), 'rgb(190, 57, 76)');
  assert.equal(await page.locator('.wb-case-mismatch').count(), 2, 'WA highlights expected and actual mismatch lines');
  assert.ok(await page.getByRole('generic', { name: '样例 2 实际输出' }).count() || await page.locator('pre[aria-label="样例 2 实际输出"]').count());
  await page.getByLabel('运行输入', { exact: true }).selectOption('custom');
  await page.getByRole('button', { name: '输入与样例', exact: true }).click();
  await page.getByRole('textbox', { name: '标准输入', exact: true }).fill('');
  await editor.press('Control+r');
  await page.waitForFunction(() => document.querySelector('.wb-result-summary')?.textContent.includes('运行完成（未校验）'));
  assert.equal(await page.evaluate(() => window.workbenchFixture.calls.filter(call => call.path === 'submissions').at(-1).body.sampleRun), false, 'empty custom input is not sample execution');
  assert.ok(await page.getByText('自定义输入没有预期答案，仅检查程序是否正常运行。', { exact: true }).isVisible());
  assert.equal(await page.evaluate(() => window.workbenchFixture.progress.length), 0);
  assert.deepEqual(await page.locator('.wb-run-actions button').allTextContents(), ['运行输入', '提交']);
  assert.equal(await page.getByRole('button', { name: '本地提交', exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: '官方提交', exact: true }).count(), 0);
  await editor.press('Control+Enter');
  await page.getByText('请在浏览器登录原站。', { exact: true }).waitFor();
  assert.equal(await page.evaluate(() => window.workbenchFixture.calls.filter(call => call.path === 'official/submit').at(-1).body.code), 'reopened A final code');
  assert.equal(await page.evaluate(() => window.workbenchFixture.submissions.length), 3, 'submit never invokes local judging');
  await page.getByRole('button', { name: '在浏览器查看', exact: true }).click();
  await page.getByText('请在浏览器登录原站。', { exact: true }).waitFor();
  assert.ok(await page.evaluate(() => window.workbenchFixture.calls.some(call => call.path === 'official/open')));
  assert.equal(await page.evaluate(() => window.workbenchFixture.progress.length), 0, 'login/opening never manufactures accepted progress');
  await page.evaluate(() => { window.workbenchFixture.officialStatus = 'ready'; });
  await page.getByText('登录成功，可以提交。', { exact: true }).waitFor();
  await page.getByRole('button', { name: '提交', exact: true }).click();
  await page.evaluate(() => { window.workbenchFixture.officialStatus = 'judging'; });
  await page.getByText('评测中', { exact: true }).waitFor();
  assert.equal(await page.getByRole('button', { name: '提交', exact: true }).isDisabled(), true);
  const beforeDuplicate = await page.evaluate(() => window.workbenchFixture.calls.filter(call => call.path === 'official/submit').length);
  await editor.press('Control+Enter');
  assert.equal(await page.evaluate(() => window.workbenchFixture.calls.filter(call => call.path === 'official/submit').length), beforeDuplicate);
  assert.equal(await editor.isVisible(), true, 'editor stays available while official judging');
  assert.equal(await page.evaluate(() => window.acceptedTones), 0, 'samples, WA, login and pending do not play the AC sound');
  await page.evaluate(() => { window.workbenchFixture.officialStatus = 'unconfirmed'; });
  await page.getByText('正在核对提交', { exact: true }).waitFor();
  await page.waitForTimeout(1200);
  await page.evaluate(() => { window.workbenchFixture.officialStatus = 'finished'; });
  await page.waitForFunction(() => document.querySelector('.wb-result-summary .wb-verdict-confirmed')?.textContent.trim() === 'AC');
  await page.waitForFunction(() => window.workbenchFixture.progress.length === 1);
  assert.ok(await page.locator('.wb-result-summary .wb-verdict-confirmed').evaluate(el => parseFloat(getComputedStyle(el).fontSize) >= 32));
  assert.equal(await page.evaluate(() => window.acceptedTones), 4, 'one confirmed AC plays one four-note chime');
  assert.equal(await page.locator('.wb-result-summary').textContent().then(value => value.includes('官方')), false);
  await page.waitForTimeout(1200);
  assert.equal(await page.evaluate(() => window.acceptedTones), 4, 'repeat receipt polling does not replay the sound');
  await page.getByRole('button', { name: /^记录/ }).click();
  await page.locator('.wb-history-main').first().click();
  assert.equal(await page.evaluate(() => window.acceptedTones), 4, 'viewing an accepted history record stays silent');

  await page.evaluate(() => {
    document.documentElement.style.setProperty('--blue', '#3e78bd');
    document.documentElement.style.setProperty('--verdict-purple', '#8053ba');
  });
  await page.getByLabel('运行输入', { exact: true }).selectOption('samples');
  for (const [verdict, color] of [['RE', 'rgb(128, 83, 186)'], ['CE', 'rgb(62, 120, 189)'], ['TLE', 'rgb(161, 100, 25)'], ['MLE', 'rgb(161, 100, 25)'], ['OLE', 'rgb(161, 100, 25)'], ['ERROR', 'rgb(190, 57, 76)']]) {
    await page.evaluate(value => { window.workbenchFixture.nextRunVerdict = value; }, verdict);
    await page.getByRole('button', { name: '运行样例', exact: true }).click();
    const badge = page.locator('.wb-result-summary .wb-verdict-' + verdict.toLowerCase());
    await badge.waitFor();
    assert.equal(await badge.textContent(), verdict === 'ERROR' ? 'SE' : verdict);
    assert.equal(await badge.evaluate(node => getComputedStyle(node).color), color);
    assert.ok(await badge.evaluate(node => parseFloat(getComputedStyle(node).fontSize) >= 32));
    if (verdict === 'RE') await page.screenshot({ path: path.join(root, 'tests', 'screenshots', 'workbench-re.png'), animations: 'disabled' });
  }
  assert.equal(await page.evaluate(() => window.acceptedTones), 4, 'errors never play acceptance sound');

  // Button Enter must remain a native click, not a preview toggle/global key.
  const solution = page.getByRole('button', { name: '题解', exact: true });
  await solution.focus();
  await solution.press('Enter');
  assert.equal(await page.evaluate(() => window.workbenchFixture.solutionCount), 1);
  assert.equal(await solution.getAttribute('aria-pressed'),'true');
  await solution.click();assert.equal(await solution.getAttribute('aria-pressed'),'false');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.solutionClosed),1);
  await editor.focus();
  await editor.press('Alt+1');
  assert.equal(await editor.isVisible(), false);
  await page.locator('.wb-statement').press('Alt+2');
  assert.equal(await editor.isVisible(), true);
  await editor.press('Alt+0');

  // Late problem fetches cannot replace the currently selected problem.
  await page.evaluate(() => { window.workbenchFixture.problemDelay.B = 650; window.workbenchFixture.changeProblem('B'); });
  await page.waitForFunction(() => document.querySelector('.tb-workbench').dataset.problemId === 'B');
  await page.evaluate(() => window.workbenchFixture.changeProblem('C'));
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '第三道题');
  await page.waitForTimeout(700);
  assert.equal(await page.locator('.wb-heading strong').textContent(), '第三道题');

  await page.evaluate(() => { window.workbenchFixture.translationError = '翻译服务暂不可用，已保留原文。'; });
  await page.getByRole('button', { name: '原文', exact: true }).click();
  await page.getByText('翻译服务暂不可用，已保留原文。', { exact: true }).waitFor();
  assert.equal(await page.getByRole('button', { name: '原文', exact: true }).getAttribute('aria-pressed'), 'false');
  assert.ok(await page.locator('.wb-statement').textContent().then(text => text.includes('Given two integers')));
  await page.evaluate(() => { window.workbenchFixture.translationError = ''; });
  await page.locator('.wb-translation-error').getByRole('button', { name: '重试', exact: true }).click();
  await page.waitForFunction(()=>document.querySelector('.wb-statement')?.textContent.includes('C 的中文题面'));

  // Site translations remain readable; missing statements can recover
  // without losing an unsaved draft, including a legitimate empty input.
  await page.evaluate(() => { window.workbenchFixture.translationKind = 'site'; window.workbenchFixture.changeProblem('D'); });
  await page.waitForFunction(() => document.querySelector('.tb-workbench').dataset.problemId === 'D' && document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true');
  await page.getByRole('button', { name: '原文', exact: true }).click();
  await page.waitForFunction(()=>document.querySelector('.wb-statement')?.textContent.includes('D 的中文题面'));
  assert.equal(await page.getByText('机器翻译 · Fixture provider', { exact: true }).count(), 0);
  await page.evaluate(() => { window.workbenchFixture.problemOverrides.E = { markdown: '', statementAvailable: false, statementError: 'Temporary fixture failure', samples: [] }; window.workbenchFixture.changeProblem('E'); });
  await page.getByText('题面暂时未能加载', { exact: true }).waitFor();
  await editor.fill('// keep this unsaved recovery draft');
  await page.evaluate(() => { window.workbenchFixture.problemOverrides.E = { samples: [{name:'样例 1',input:'',output:'1 1 2 3 5'}] }; });
  await page.getByRole('button', {name:'重新载入',exact:true}).click();
  await page.getByText('题面暂时未能加载', { exact: true }).waitFor({state:'hidden'});
  await page.waitForFunction(() => document.querySelector('.wb-statement')?.textContent.includes('Given two integers') && window.workbenchFixture.readCode() === '// keep this unsaved recovery draft');
  await page.evaluate(() => { window.workbenchFixture.officialStatus = 'needs_verification'; window.workbenchFixture.preparationEvents = []; });
  await page.getByRole('button', {name:'提交',exact:true}).click();
  await page.getByRole('button', {name:'完成原站验证',exact:true}).waitFor();
  assert.deepEqual(await page.evaluate(() => window.workbenchFixture.preparationEvents), [], 'submission verification never opens the four-account login panel');
  const viewCalls=await page.evaluate(() => window.workbenchFixture.calls.filter(call=>call.path==='official/open').length);
  await page.getByRole('button', {name:'完成原站验证',exact:true}).click();
  await page.waitForFunction(count => window.workbenchFixture.calls.filter(call=>call.path==='official/open').length===count+1, viewCalls);

  await page.evaluate(() => { window.workbenchFixture.problemDelay.B = 10; window.workbenchFixture.officialStatus = 'judging'; window.workbenchFixture.changeProblem('B'); });
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '最长的路径');
  await editor.fill('int main() { return 0; }');
  await editor.press('Control+Enter');
  await page.evaluate(() => { window.workbenchFixture.officialStatus = 'finished'; });
  await page.waitForFunction(() => document.querySelector('.wb-result-summary')?.textContent.includes('AC'));
  assert.equal(await page.locator('.tb-workbench > .wb-official-status').count(), 0, 'Submission status never adds a top strip');
  assert.equal(await page.getByLabel('原站提交状态').count(), 0, 'A final verdict appears only in the result panel');
  await page.waitForFunction(() => window.workbenchFixture.progress.length === 2);
  assert.equal(await page.evaluate(() => window.workbenchFixture.progress.at(-1).summary.accepted), 1);
  await editor.fill('unsaved edit before restoring history');
  await page.getByRole('button', { name: /^记录/ }).click();
  await page.getByRole('button', { name: '载入代码', exact: true }).first().click();
  assert.equal(await page.evaluate(() => window.workbenchFixture.readCode()), 'int main() { return 0; }');
  await page.getByRole('button', { name: '撤销载入代码', exact: true }).click();
  assert.equal(await page.evaluate(() => window.workbenchFixture.readCode()), 'unsaved edit before restoring history');
  await page.evaluate(() => window.workbenchFixture.changeProblem('A'));
  await page.waitForFunction(() => document.querySelector('.wb-heading strong').textContent === '两数之和');

  await page.evaluate(() => window.workbenchFixture.changeContest({ id: 'mock1', status: 'running', slots: [{ id: 'A', letter: 'A' }] }));
  await page.waitForFunction(() => document.querySelector('.wb-letter')?.textContent === 'A' && document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true');
  assert.equal(await fontSize.inputValue(), '24', 'mock practice uses the saved reading size');
  assert.equal(await page.getByRole('button', { name: '题解', exact: true }).count(), 0, 'mock never offers solutions while running');
  assert.equal(await page.getByRole('button', { name: '导入代码', exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: '保存草稿', exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: '赛内提交', exact: true }).count(), 0);
  assert.notEqual(await page.evaluate(() => window.workbenchFixture.readCode()), 'reopened A final code', 'mock draft is separate from solo draft');
  await editor.fill('contest draft');
  await editor.press('Control+s');
  await page.waitForFunction(() => window.workbenchFixture.drafts['mock1:A'] === 'contest draft');
  for(const width of [1050,430]){
    await page.setViewportSize({width,height:800});
    await page.waitForFunction(expected=>document.querySelector('.tb-workbench').classList.contains('wb-compact')===expected,width<996);
    await clickReturnCorner('返回工作台');
    assert.equal(await editor.getAttribute('aria-readonly'),'false','Returning leaves the running contest editable');
    assert.equal(await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>/contests\/(?:finish|cancel)/.test(call.path)).length),0,'Return never sends a finish or cancellation request');
  }
  await page.setViewportSize({width:1050,height:700});await page.waitForFunction(()=>!document.querySelector('.wb-compact'));
  await page.getByRole('button', {name:'提交',exact:true}).click();
  await page.waitForFunction(()=>window.workbenchFixture.calls.filter(call=>call.path==='official/submit').at(-1)?.body.contestId==='mock1');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>call.path==='official/submit').at(-1).body.code),'contest draft');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>call.path==='submissions'&&call.body?.mode==='submit'&&call.body?.contestId==='mock1').length),0);
  await page.evaluate(() => window.workbenchFixture.changeContest({ id: 'mock1', status: 'finished', slots: [{ id: 'A', letter: 'A' }] }));
  await page.waitForFunction(() => document.querySelector('.cm-content')?.getAttribute('aria-readonly') === 'true');
  assert.equal(await editor.getAttribute('aria-readonly'), 'true');
  assert.equal(await page.getByRole('button', { name: '提交', exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: '运行样例', exact: true }).isDisabled(), true);

  const overflow = await page.evaluate(() => ({
    page: document.documentElement.scrollWidth > innerWidth,
    body: document.querySelector('.wb-body').scrollWidth > document.querySelector('.wb-body').clientWidth,
  }));
  assert.deepEqual(overflow, { page: false, body: false }, '1050px layout does not overflow');
  await page.screenshot({ path: path.join(root, 'tests', 'screenshots', 'workbench-light.png'), animations: 'disabled' });
  assert.deepEqual(errors, []);
  console.log('Workbench: draft isolation, save ordering, keyboard, honest verdicts, mock locks, layout passed.');
} finally {
  await browser.close();
  await server.close();
}
