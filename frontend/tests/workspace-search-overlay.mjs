import assert from 'node:assert/strict';

export async function checkSearchOverlay({page,search,out}){
 const table=page.locator('.section-document:not([hidden]) .table-scroll');
 const results=page.getByRole('region',{name:'全局搜索结果'});
 const sort=table.getByRole('button',{name:'难度',exact:true});
 await sort.click();
 const order=await table.locator('tr[data-id]').evaluateAll(nodes=>nodes.map(node=>node.dataset.id));
 const appearance=await page.evaluate(()=>({theme:document.documentElement.dataset.theme,opacity:document.documentElement.style.getPropertyValue('--panel-opacity')}));
 const cases=[{width:2048,theme:'dark',opacity:'0%'},{width:1600,theme:'light',opacity:'35%'},{width:640,theme:'dark',opacity:'35%'}];
 for(const [index,scenario] of cases.entries()){
  await page.setViewportSize({width:scenario.width,height:1000});
  await page.evaluate(({theme,opacity})=>{document.documentElement.dataset.theme=theme;document.documentElement.style.setProperty('--panel-opacity',opacity);},scenario);
  await table.evaluate(node=>{node.scrollTop=470;node.dispatchEvent(new Event('scroll'));});
  const position=await table.evaluate(node=>({top:node.scrollTop,left:node.scrollLeft}));
  assert(position.top>0,'The underlying problem list has an actual saved scroll position');
  await search.fill('二分');
  await results.getByRole('listitem',{name:'单题 二分',exact:true}).first().waitFor();
  const painted=await page.locator('.workspace-area > :not(.workspace-search-results)').evaluateAll(roots=>roots.flatMap(root=>[root,...root.querySelectorAll('*')]).filter(node=>{
   const style=getComputedStyle(node);
   return style.visibility==='visible'&&style.display!=='none'&&node.getClientRects().length;
  }).map(node=>({tag:node.tagName,text:node.textContent.trim().slice(0,60)})).slice(0,12));
  assert.deepEqual(painted,[],'Underlying headers, tags and practice dates must not paint through search results');
  await page.keyboard.press('Tab');
  assert(await page.evaluate(()=>!document.activeElement.closest('.workspace-area')||Boolean(document.activeElement.closest('.workspace-search-results'))),'Keyboard navigation cannot enter the hidden page');
  await page.screenshot({path:`${out}/search-overlay-${scenario.width}-${scenario.theme}.png`});
  if(index===0){await search.focus();await page.keyboard.press('Escape');}
  else if(index===1)await results.getByRole('button',{name:'关闭搜索结果',exact:true}).click();
  else await page.getByRole('button',{name:'清空搜索',exact:true}).click();
  await results.waitFor({state:'detached'});
  assert.deepEqual(await table.evaluate(node=>({top:node.scrollTop,left:node.scrollLeft})),position,'Closing search preserves the original scroll position');
  assert.deepEqual(await table.locator('tr[data-id]').evaluateAll(nodes=>nodes.map(node=>node.dataset.id)),order,'Global search preserves the existing sort and problem selection');
  assert(await table.getByRole('button',{name:'难度',exact:true}).isVisible(),'The original page becomes usable again');
 }
 await page.evaluate(({theme,opacity})=>{document.documentElement.dataset.theme=theme;if(opacity)document.documentElement.style.setProperty('--panel-opacity',opacity);else document.documentElement.style.removeProperty('--panel-opacity');},appearance);
 await page.setViewportSize({width:1600,height:1000});
 await table.evaluate(node=>{node.scrollTop=0;node.dispatchEvent(new Event('scroll'));});
 return {cases:cases.length,allUnderlyingContentHidden:true,keyboardIsolation:true,scrollAndSortRestored:true,closeMethods:['Escape','close','clear']};
}
