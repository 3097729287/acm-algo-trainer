import assert from 'node:assert/strict';

export async function openMockSelection(page,mode){
 const trigger=page.getByRole('button',{name:mode,exact:true});
 if(await trigger.getAttribute('aria-expanded')!=='true')await trigger.click();
 const menu=page.getByRole('listbox',{name:mode==='专项训练'?'专项训练知识点':'重现赛比赛',exact:true});
 await menu.waitFor();return menu;
}

// Follow the rendered folder tree and choose the actual canonical value. This
// never forces a hidden select or bypasses the production navigation events.
export async function chooseMockValue(page,mode,value){
 const menu=await openMockSelection(page,mode),label=mode==='专项训练'?'专项训练知识点':'重现赛比赛';
 await page.waitForFunction(({label,value})=>[...document.querySelectorAll('select')].some(select=>select.getAttribute('aria-label')===label&&[...select.options].some(option=>option.value===value)),{label,value});
 const find=async(depth=0)=>{
  assert(depth<15,'Unexpectedly deep mock folder tree');
  const rows=await menu.getByRole('option').evaluateAll(nodes=>nodes.map((node,index)=>({index,value:node.dataset.value,folder:Boolean(node.querySelector('.lucide-folder')),label:node.querySelector('span')?.textContent,disabled:node.disabled})));
  const match=rows.find(row=>row.value===value&&!row.disabled);
  if(match){await menu.getByRole('option').nth(match.index).click();if(!match.folder)return true;await menu.getByRole('button',{name:'返回上一级',exact:true}).waitFor();return find(depth+1);}
  for(const row of rows.filter(row=>row.folder&&!row.disabled)){
   await menu.getByRole('option').nth(row.index).click();
   await menu.getByRole('button',{name:'返回上一级',exact:true}).waitFor();
   if(await find(depth+1))return true;
   await menu.getByRole('button',{name:'返回上一级',exact:true}).click();
  }
  return false;
 };
 assert(await find(),`Actual mock menu contains ${value}`);
 await menu.waitFor({state:'detached'});
 assert.equal(await page.locator(`select[aria-label="${label}"]`).inputValue(),value);
}
