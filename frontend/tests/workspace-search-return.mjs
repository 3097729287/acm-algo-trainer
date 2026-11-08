import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';

export async function checkSearchReturn({page,search}){
 const results=page.getByRole('region',{name:'全局搜索结果'});
 const opened=page.locator('.study-pane[data-study-key="problem:fixture::2"]:not([hidden])');
 const back=async()=>{
  await page.getByRole('button',{name:'返回主界面',exact:true}).click();
  await page.waitForFunction(()=>document.activeElement?.getAttribute('aria-label')==='统一搜索');
 };
 await search.fill('列表定位测试');await results.getByRole('listitem').first().waitFor();
 const first=await results.getByRole('listitem').first().getAttribute('aria-label');
 assert(first.includes('003'),'Enter follows the first displayed result');
 await search.press('Enter');await opened.waitFor();await back();
 assert.equal(await search.inputValue(),'列表定位测试');
 await search.press('Enter');await opened.waitFor();await back();
 assert.equal(await search.inputValue(),'列表定位测试');
 await search.press('End');await search.pressSequentially(' 003');
 await results.getByRole('listitem').first().click();await opened.waitFor();await back();
 assert.equal(await search.inputValue(),'列表定位测试 003','Click and keyboard opening both preserve the query');
 await search.fill('no-matching-fixture-xyz');await search.press('Enter');assert(await opened.isHidden());
 await search.fill('列表定位测试 003');await results.getByRole('listitem').first().waitFor();
 await search.evaluate(node=>node.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',isComposing:true,bubbles:true})));
 assert(await opened.isHidden(),'Composing Enter must not open a result');
 await search.press('Escape');await results.waitFor({state:'detached'});
 const report={firstMatchOnEnter:true,repeatEnter:true,queryPreserved:true,returnFocus:true,clickReturn:true,noMatchSafe:true,compositionSafe:true};
 await mkdir('../.backups/editorial-playback-20261108/ui',{recursive:true});await writeFile('../.backups/editorial-playback-20261108/ui/search-return.json',JSON.stringify(report,null,2));
 return report;
}
