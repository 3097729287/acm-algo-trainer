import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
try {
  const page=await browser.newPage();
  const row=(owner,id,status)=>`<tr><td><time>2026-10-14 18:00:00+0900</time><a href="/users/${owner}">${owner}</a><a href="/contests/abc479/tasks/abc479_a">A</a><a href="/contests/abc479/submissions/${id}">Detail</a><span class="label">${status}</span></td></tr>`;
  await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:'<nav class="navbar"><a href="/users/owner">owner</a></nav><table><tbody>'+row('owner','12345','AC')+row('someone-else','12346','AC')+row('owner','12347','WJ')+'</tbody></table>'}));
  await page.goto('https://atcoder.jp/contests/abc479/tasks/abc479_a');
  await page.evaluate(()=>{window.messages=[];window.chrome={runtime:{sendMessage:async value=>messages.push(value)}};});
  await page.addScriptTag({content:await readFile(new URL('../../desktop/browser_extension/receipts.js',import.meta.url),'utf8')});
  await page.waitForFunction(()=>messages.length>0);
  const [value]=await page.evaluate(()=>messages);
  assert.equal(value.owner,'owner');assert.equal(value.records.length,1);
  assert.deepEqual(value.records[0],{submissionId:'12345',url:'https://atcoder.jp/contests/abc479/tasks/abc479_a',verdict:'AC',acceptedAt:'2026-10-14T09:00:00.000Z'});
  console.log('AtCoder unbound personal history: exact owner, final verdict and original submission time passed. No real account submission.');
} finally {await browser.close();}
