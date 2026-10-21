import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const server=await createServer({root,server:{host:'127.0.0.1',port:18776,strictPort:true}});
await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try {
 await page.goto('http://127.0.0.1:18776/tests/rankings-fixture.html');
 await page.getByRole('button',{name:'清空当前榜单'}).waitFor();
 const own=page.locator('.ranking-table tbody tr').first();
 assert.equal(await own.locator('.ranking-title-badge').count(),2);
 await own.getByText('Lv.10',{exact:true}).waitFor();
 const rank=own.getByLabel('黄金 · 能力分 1,560',{exact:true});
 await rank.waitFor();
 assert.match(await rank.getAttribute('class'),/\btier-3\b/,'skill rank retains its own tier style');
 await rank.hover();
 await page.getByRole('tooltip').getByText('黄金 · 能力分 1,560',{exact:true}).waitFor();
 assert.equal(await own.getByText('王者',{exact:true}).count(),0,'legacy experience tier is not repeated as a skill rank');
 assert.equal(await own.locator('.ranking-public-id').count(),0);
 assert.equal(await page.getByText('成长资料待同步',{exact:true}).count(),3);
 for(const [label,period] of [['每日','daily'],['本周','weekly'],['累计','total']]) {
  await page.getByRole('tab',{name:label,exact:true}).click();
  // Capture one complete render. A period switch can clear the previous table
  // between two locator reads while the new fixture response is still pending.
  const rendered=await page.waitForFunction(period=>{
   const nodes=[...document.querySelectorAll('.ranking-table .ranking-medal-'+period)];
   return nodes.length===3 ? nodes.map(node=>Number(node.dataset.grade)) : false;
  },period);
  assert.deepEqual(await rendered.jsonValue(),period==='total'?[9,8,7]:period==='weekly'?[6,5,4]:[3,2,1]);
  await rendered.dispose();
 }
 const gallery=page.getByRole('region',{name:'九种奖牌预览'});
 assert.equal(await gallery.locator('svg').count(),9);
 const drawings=await gallery.locator('svg').evaluateAll(nodes=>nodes.map(node=>[...node.querySelectorAll('path')].map(p=>p.getAttribute('d')).join('|')));
 assert.equal(new Set(drawings).size,9);
 fs.mkdirSync(path.join(root,'tests/screenshots'),{recursive:true});
 await page.screenshot({path:path.join(root,'tests/screenshots/rankings-medals-admin.png'),fullPage:true});
 await page.evaluate(()=>document.documentElement.dataset.theme='light');
 await page.screenshot({path:path.join(root,'tests/screenshots/rankings-medals-light.png'),fullPage:true});
 await page.evaluate(()=>document.documentElement.dataset.theme='dark');
 // Switching periods discards a late response from the previous period.
 await page.getByRole('tab',{name:'每日',exact:true}).click();
 await page.getByRole('tab',{name:'本周',exact:true}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.ranking-table .ranking-medal-weekly').length===3);
 const remove=page.getByRole('button',{name:'删除 练习者二 的本周过题成绩'});
 await remove.click();
 await page.getByRole('dialog').waitFor();
 await page.keyboard.press('Escape');
 assert.equal(await page.getByRole('dialog').count(),0);
 assert.equal(await page.evaluate(()=>window.rankingWrites.length),0);
 await remove.click();await page.getByRole('button',{name:'确认删除',exact:true}).click();
 await page.getByText('已删除 1 条排行榜成绩。').waitFor();
 assert.deepEqual(await page.evaluate(()=>window.rankingWrites[0]),{userId:'10000000-0000-4000-8000-000000000002',period:'weekly',confirmation:'delete'});
 await page.waitForFunction(()=>document.querySelectorAll('.ranking-table tbody tr').length===3);
 assert.equal(await page.locator('.ranking-table tbody tr').count(),3);
 await page.getByRole('button',{name:'清空当前榜单'}).click();
 await page.getByRole('button',{name:'取消',exact:true}).click();
 assert.equal(await page.evaluate(()=>window.rankingWrites.length),1);
 await page.evaluate(()=>window.rankingAdmin=false);
 await page.getByRole('button',{name:'同步与刷新'}).click();
 await page.getByRole('button',{name:'清空当前榜单'}).waitFor({state:'hidden'});
 assert.equal(await page.getByRole('button',{name:'清空当前榜单'}).count(),0);
 assert.equal(await page.locator('.ranking-table .ranking-delete-button').count(),0);
 // A fetched empty board remains readable when another period or XP fails.
 await page.evaluate(()=>window.rankingState={status:'error',hasSnapshot:true,entries:[],self:{count:0},error:'排行榜服务响应超时，后台将自动重试'});
 await page.getByRole('button',{name:'同步与刷新'}).click();
 await page.getByRole('heading',{name:'榜单已读取',exact:true}).waitFor();
 assert.equal(await page.getByText('排行榜暂时无法连接',{exact:true}).count(),0);
 await page.getByText('这个统计周期还没有首次官方 AC 记录。',{exact:true}).waitFor();
 await page.getByText('部分数据刷新未完成，后台将重试。',{exact:false}).waitFor();
 await page.evaluate(()=>window.rankingState={status:'error',hasSnapshot:false,entries:[],self:null,error:'排行榜服务响应超时，后台将自动重试'});
 await page.getByRole('button',{name:'同步与刷新'}).click();
 await page.getByRole('heading',{name:'排行榜暂时无法连接',exact:true}).waitFor();
 const retries=await page.evaluate(()=>window.rankingSyncs);
 await page.getByRole('button',{name:'重试连接',exact:true}).click();
 await page.waitForFunction(expected=>window.rankingSyncs>expected,retries);
 await page.evaluate(()=>window.rankingState=null);
 await page.getByRole('button',{name:'同步与刷新'}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.ranking-table tbody tr').length===3);
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=390));
 await page.screenshot({path:path.join(root,'tests/screenshots/rankings-mobile.png'),fullPage:true});
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({publicProgressAndNickname:true,idsHidden:true,legacyProgressPlaceholder:true,nineDistinctMedals:true,gradeOrder:true,threeWinners:true,adminControls:true,confirmationAndCancel:true,ordinaryUserHidden:true,periodSwitchRace:true,emptySnapshotPreserved:true,connectionRetry:true,mobile:true,errors}));
} finally {await browser.close();await server.close();}
