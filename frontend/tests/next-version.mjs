import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {DatabaseSync} from 'node:sqlite';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {startFixture} from '../../server/leaderboard/tests/local-server.mjs';
import {randomUUID} from 'node:crypto';

const shared=await startFixture(),wiki=new DatabaseSync('../backend/resources/oi-wiki.sqlite3',{readOnly:true});
shared.STORE.gameplay.verify=async()=>[];
const json=(res,value)=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));};
const vite=await createServer({plugins:[{name:'real-wiki-test-reader',configureServer(server){server.middlewares.use('/test-wiki',(req,res)=>{
 const params=new URL(req.url,'http://fixture').searchParams,id=params.get('id');
 if(id)return json(res,{article:wiki.prepare('SELECT id,title,html,url FROM articles WHERE id=?').get(id)});
 const q=params.get('q')||'';json(res,{articles:wiki.prepare('SELECT id,title,category,url FROM articles WHERE title LIKE ? OR search_text LIKE ?').all('%'+q+'%','%'+q+'%')});
});}}],server:{host:'127.0.0.1',port:0,watch:null,proxy:{'/online':{target:shared.endpoint,rewrite:p=>p.slice(7)}}}});
await vite.listen();const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),errors=[];
async function client(name,handle){
 const send=async(path,body,auth)=>{const r=await fetch(shared.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});const value=await r.json();assert(r.ok,JSON.stringify(value));return value;};
 const password='isolated-browser-fixture';await send('/v1/accounts/register',{loginId:name,nickname:handle,password});const auth={...await send('/v1/accounts/login',{loginId:name,password}),handle};
 const context=await browser.newContext({viewport:{width:1440,height:1100}});await context.addInitScript(value=>sessionStorage.setItem('next-auth',JSON.stringify(value)),auth);
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
 return {page,context,auth,send:(p,b)=>send(p,b,auth)};
}
try{
 const a=await client('browser_alpha','Alpha'),b=await client('browser_beta','Beta');
 for(const [i,xp] of [15,30,60,100].entries())await a.send('/v1/stickers/grant',{requestId:randomUUID(),day:'2026-11-02',taskId:'ac-chain:'+i,xp});
 await a.page.goto(base+'/tests/next-version-fixture.html');
 await a.page.getByRole('button',{name:'贴纸',exact:true}).click();
 const region=a.page.getByRole('region',{name:'贴纸区域'});let box=await region.boundingBox();
 await a.page.mouse.click(box.x+box.width*.34,box.y+box.height*.57);
 const picker=a.page.getByRole('dialog',{name:'选择贴纸'});await picker.waitFor();
 assert.match(await picker.locator('.sticker-choice').first().getAttribute('aria-label'),/^传说/);
 const first=picker.locator('button.sticker-choice:not([disabled])').first();await first.click();
 const selected=a.page.locator('.selected-sticker');await selected.waitFor();let sticker=await selected.boundingBox();
 await a.page.mouse.move(sticker.x+sticker.width/2,sticker.y+sticker.height/2);await a.page.mouse.down();await a.page.mouse.move(box.x+box.width*.65,box.y+box.height*.62,{steps:12});await a.page.mouse.up();
 await a.page.getByRole('button',{name:'旋转贴纸'}).click();await a.page.keyboard.press('Enter');await a.page.waitForFunction(()=>document.querySelectorAll('.placed-sticker:not(.selected-sticker)').length===1);
 let inventory=await a.send('/v1/stickers');assert.equal(inventory.units.filter(x=>x.placement).length,1);assert.equal(inventory.units.find(x=>x.placement).placement.angle,15);
 await a.page.reload();await a.page.locator('.placed-sticker').waitFor();assert.equal((await a.send('/v1/stickers')).units.length,4);
 await a.page.locator('.placed-sticker').click({button:'right'});await a.page.getByRole('alertdialog',{name:'回收贴纸确认'}).waitFor();await a.page.getByRole('button',{name:'回收',exact:true}).click();await a.page.waitForFunction(()=>!document.querySelector('.placed-sticker'));
 inventory=await a.send('/v1/stickers');assert.equal(inventory.units.length,4);assert.equal(inventory.units.filter(x=>x.placement).length,0);
 await a.page.getByRole('button',{name:'贴纸',exact:true}).click();box=await region.boundingBox();await a.page.mouse.click(box.x+box.width*.5,box.y+box.height*.5);await picker.waitFor();await picker.locator('button.sticker-choice:not([disabled])').first().click();await a.page.keyboard.press('Escape');assert.equal(await a.page.locator('.selected-sticker').count(),0);await a.page.keyboard.press('Escape');assert.equal(await a.page.locator('.sticker-mode').count(),0);
 await mkdir('tests/screenshots/next-version',{recursive:true});
 for(const [width,height] of [[1440,1100],[1100,800],[760,900],[430,760]]){await a.page.setViewportSize({width,height});await a.page.screenshot({path:`tests/screenshots/next-version/growth-${width}.png`});assert(await a.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no horizontal clipping '+width);}
 await a.page.getByRole('button',{name:'wiki',exact:true}).click();await a.page.getByRole('button',{name:'二分',exact:true}).click();
 const frame=a.page.frameLocator('iframe');await frame.locator('math').first().waitFor();assert(await frame.locator('pre').count()>0);await frame.locator('details').evaluateAll(nodes=>nodes.forEach(node=>node.open=true));await frame.locator('img').first().scrollIntoViewIfNeeded();await frame.locator('img').first().waitFor();await frame.locator('img').first().evaluate(img=>img.decode());assert(await frame.locator('img').first().evaluate(img=>img.complete&&img.naturalWidth>0));
 assert(await frame.locator('body').innerText().then(text=>text.includes('本页面贡献者')));assert.equal(await frame.locator('script').count(),0);
 await a.page.screenshot({path:'tests/screenshots/next-version/wiki-math.png'});
 await a.page.getByRole('button',{name:'返回维基目录'}).click();await a.page.getByRole('textbox',{name:'搜索维基百科'}).fill('no-such-wiki-xyz');await a.page.getByText('没有匹配的内容',{exact:true}).waitFor();
 await a.page.getByRole('button',{name:'duel',exact:true}).click();await a.page.getByRole('button',{name:'开始匹配'}).click();await a.page.getByRole('button',{name:'取消匹配'}).waitFor();
 await b.page.goto(base+'/tests/next-version-fixture.html');await b.page.getByRole('button',{name:'duel',exact:true}).click();await b.page.getByRole('button',{name:'开始匹配'}).click();await b.page.locator('.duel-player').first().waitFor();
 await a.page.locator('.duel-player').first().waitFor({timeout:15000});
 const matchA=(await a.send('/v1/duels')).match,matchB=(await b.send('/v1/duels')).match;
 assert.equal(matchA.id,matchB.id);assert.equal(matchA.startedAt,matchB.startedAt);assert.deepEqual(matchA.problem,matchB.problem);
 assert.match(await a.page.locator('.duel-players').innerText(),/Alpha/);assert.match(await a.page.locator('.duel-players').innerText(),/Beta/);
 await a.page.reload();await a.page.getByRole('button',{name:'duel',exact:true}).click();await a.page.locator('.duel-player').first().waitFor();assert.equal((await a.send('/v1/duels')).match.id,matchA.id);
 await a.page.screenshot({path:'tests/screenshots/next-version/duel-two-clients.png'});
 assert.deepEqual(errors,[]);console.log('PASS real isolated two-client match/reconnect; authoritative sticker drag/rotate/Enter/Esc/recycle; real OI Wiki MathML/code/images/attribution/search; four viewport sizes');
}finally{await browser.close();await vite.close();wiki.close();await shared.close();}
