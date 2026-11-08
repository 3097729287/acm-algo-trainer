import assert from 'node:assert/strict';
import {resolve} from 'node:path';

export async function exerciseNativeAssets(page,output) {
 const result=await page.evaluate(async()=>{
  const rpc=async(path,query={})=>{const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path,query}});if(!result.ok)throw Error(result.error.code+': '+result.error.message);return result.data;};
  const found=await rpc('library/page',{q:['小月的屏幕'],limit:['2']});
  const row=found.rows.find(row=>row.title==='小月的屏幕');if(!row)throw Error('Reviewed public image statement is missing');
  const statement=await rpc('problem',{id:[row.id]});
  const image=Object.values(statement.images||{}).find(value=>typeof value==='string'&&value.startsWith('data:image/'));
  if(!image)throw Error('Actual original image was not hydrated');
  const body=image.slice(image.indexOf(',')+1),bytes=Uint8Array.from(atob(body),char=>char.charCodeAt(0));
  const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value=>value.toString(16).padStart(2,'0')).join('');
  const asset=await rpc('library/asset',{sha256:[digest]});
  if(asset.data!==body||asset.bytes!==bytes.length)throw Error('The asset route differs from the displayed original resource');
  return {id:row.id,title:row.title,sha256:digest,mime:asset.mime,bytes:asset.bytes};
 });
 const back=page.locator('button[aria-label="返回主界面"]:visible').first();if(await back.isVisible())await back.click();
 await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});await page.keyboard.press('Control+2');
 await page.getByRole('searchbox',{name:'统一搜索',exact:true}).fill(result.title);
 await page.locator('.workspace-search-row').filter({hasText:result.title}).first().click();
 await page.locator('.tb-workbench:visible').waitFor();
 const image=page.locator('.wb-statement img:visible').first();
 if(!await image.isVisible())await page.keyboard.press('Alt+1');await image.waitFor();
 await page.waitForFunction(()=>[...document.querySelectorAll('.wb-statement img')].some(image=>image.getClientRects().length&&image.complete&&image.naturalWidth>0&&image.src.startsWith('data:image/')));
 assert((await image.getAttribute('src')).startsWith('data:image/'));
 await page.screenshot({path:resolve(output,'native-original-image.png')});
 return {...result,realTauriIpc:true,reviewedPublicSeedImage:true,originalImageActuallyRendered:true,assetRouteMatchesOriginalBytes:true,remoteTransportScope:'This full-seed window reads an embedded original. Remote first-fetch, offline restart, locked-read behavior and failure/no-write boundaries are verified by separate service and transport tests.'};
}
