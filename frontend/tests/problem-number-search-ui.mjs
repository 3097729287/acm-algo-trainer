import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';

export async function checkProblemNumberSearch({page,search}){
 await mkdir('../.backups/problem-number-search-20261108',{recursive:true});
 const results=page.getByRole('region',{name:'全局搜索结果'}),name='单题 单调队列 / 滑动窗口';
 for(const query of ['P1886','p1886','Ｐ１８８６']){
  await search.fill(query);await results.getByRole('listitem',{name,exact:true}).waitFor();
  assert.equal(await results.getByRole('listitem').first().getAttribute('aria-label'),name);
  assert((await results.getByRole('listitem').first().textContent()).includes('P1886'),'The result identifies the matching number');
 }
 await search.fill('P1886');await search.press('Enter');await page.locator('.study-pane[data-study-key="problem:fixture::119"] .tb-workbench').waitFor();
 await page.getByRole('button',{name:'返回主界面',exact:true}).click();await page.waitForFunction(()=>document.activeElement?.getAttribute('aria-label')==='统一搜索');
 assert.equal(await search.inputValue(),'P1886');await results.getByRole('listitem',{name,exact:true}).waitFor();
 await page.screenshot({path:'../.backups/problem-number-search-20261108/number-search.png'});
 await search.press('Escape');await results.waitFor({state:'detached'});
 const report={ok:true,numberSearch:true,lowercase:true,fullWidth:true,numberShown:true,enterOpensMatchingProblem:true,returnPreservesNumber:true,returnFocus:true};
 await writeFile('../.backups/problem-number-search-20261108/ui.json',JSON.stringify(report,null,2));return report;
}
