import assert from 'node:assert/strict';
import {resolve} from 'node:path';

export async function exerciseNativeReviewedContent(page, output) {
 const checks=[];
 for(const id of ['remote:codeforces:102992::A','remote:codeforces:105459::B']) {
  const source=await page.evaluate(async id=>{
   const rpc=async(path,query)=>{const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path,query}});if(!result.ok)throw Error(result.error.code+': '+result.error.message);return result.data;};
   const problem=await rpc('problem',{id:[id]});
   const row=(await rpc('data',{compact:['1']})).rows.find(row=>row.id===id);
   if(!row)throw Error('Reviewed public identity is absent from the current native catalogue');
   if(!problem.translationAvailable||!problem.translation?.markdown)throw Error('Reviewed Chinese text is absent');
   const pdf=problem.statementPdf;
   if(!pdf?.data?.startsWith('data:application/pdf;base64,'))throw Error('Original PDF was not hydrated through native IPC');
   const bytes=Uint8Array.from(atob(pdf.data.split(',')[1]),char=>char.charCodeAt(0));
   const sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
   if(sha!==pdf.sha256)throw Error('Original PDF bytes differ from reviewed digest');
   const asset=await rpc('library/asset',{sha256:[sha]});
   if(asset.bytes!==bytes.length||asset.data!==pdf.data.split(',')[1])throw Error('Direct asset route differs from original PDF');
   return {id,title:problem.title,contest:row.contest,pages:pdf.pageCount,pdfSha256:sha,pdfBytes:bytes.length,samples:problem.samples.length,
    chineseCharacters:problem.translation.markdown.length,expectedImages:[...problem.translation.markdown.matchAll(/!\[[^\]]*\]\([^)]+\)/g)].length};
  },id);
  const back=page.getByRole('button',{name:'返回主界面',exact:true}).first();if(await back.isVisible())await back.click();
  await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
  await page.getByRole('searchbox',{name:'统一搜索',exact:true}).fill(source.title);
  await page.locator('.workspace-search-row[aria-label^="单题 "]').filter({hasText:source.title})
   .filter({has:page.locator('.workspace-search-context').filter({hasText:source.contest})}).first().click();
  await page.locator(`.tb-workbench[data-problem-id="${id}"]:visible`).waitFor();
  const toggle=page.locator('.wb-language-toggle button:visible').first();await toggle.waitFor();
  if(await toggle.getAttribute('aria-label')==='中文')await toggle.click();
  await page.locator('.wb-pdf-page[data-page="1"][data-ready="true"]').waitFor();
  assert.equal(await page.locator('.wb-pdf-page').count(),source.pages);
  const original=page.locator('.wb-statement-pdf');
  for(const item of await original.locator('.wb-pdf-page').all()){
   await item.scrollIntoViewIfNeeded();
   await page.waitForFunction(element=>element.dataset.ready==='true',await item.elementHandle());
   assert((await item.locator('.wb-pdf-text-layer').textContent()).trim().length>0);
  }
  await toggle.click();
  await page.getByRole('button',{name:'中文',exact:true}).waitFor();
  const statement=page.locator('.wb-statement:visible');await statement.waitFor();
  assert.match(await statement.textContent(),/输入格式|题目描述/);
  assert.equal(await statement.locator('.katex-error').count(),0);
  assert.equal(await page.locator('.wb-translation-error').count(),0);
  assert.equal(await statement.locator('img').count(),source.expectedImages);
  for(const picture of await statement.locator('img').all()){
   await picture.scrollIntoViewIfNeeded();await picture.evaluate(image=>image.decode());
   assert(await picture.evaluate(image=>image.complete&&image.naturalWidth>0));
  }
  await page.screenshot({path:resolve(output,id.replaceAll(':','_')+'-native-chinese.png')});
  checks.push({...source,allPdfPagesRendered:true,actualChineseAndOriginalImagesRendered:true,formulaErrors:0});
 }
 return {realTauriIpc:true,reviewed1610Content:true,checks,externalAccountUsed:false};
}
