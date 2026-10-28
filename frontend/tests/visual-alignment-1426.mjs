import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const work='../.backups/local-1426',port=JSON.parse(fs.readFileSync(work+'/ui-port.json','utf8')).port;
fs.mkdirSync(work+'/ui',{recursive:true});
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage(),errors=[],frames=[];
page.on('pageerror',e=>errors.push(e.message));
const nav=name=>page.getByRole('navigation',{name:'主导航'}).getByRole('button',{name,exact:true});
try {
 await page.goto(`http://127.0.0.1:${port}`);
 for(const [width,height] of [[2048,1152],[1440,900],[1050,700]])for(const theme of ['dark','light']) {
  await page.setViewportSize({width,height});
  const frame={width,height,theme,catalogs:[]};
  for(const name of ['算法实验室','模板']) {
   await nav(name).click();await page.locator('.catalog-card').first().waitFor();
   await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
   await page.mouse.move(0,0);await page.waitForTimeout(70);
   const card=page.locator('.catalog-card').first();
   const geometry=await card.evaluate(node=>{
    const outer=node.getBoundingClientRect(),heading=node.querySelector('.catalog-card-heading').getBoundingClientRect(),catalog=node.closest('.lab-multi-catalog').getBoundingClientRect(),panel=node.closest('.scroll-panel'),parent=panel.getBoundingClientRect();
    return {headingCenter:Math.abs((heading.y+heading.height/2)-(outer.y+outer.height/2)),catalogCenter:Math.abs(catalog.x+catalog.width/2-(parent.x+panel.clientLeft+panel.clientWidth/2)),background:getComputedStyle(node).backgroundColor,headingMargin:getComputedStyle(node.querySelector('.catalog-card-heading')).margin,children:node.children.length,justify:getComputedStyle(node).justifyContent,padding:getComputedStyle(node).padding};
   });
   assert(geometry.headingCenter<=2,JSON.stringify(geometry));assert(geometry.catalogCenter<=2,JSON.stringify(geometry));
   await card.hover();await page.waitForTimeout(200);
   const highlight=await card.evaluate(n=>getComputedStyle(n).backgroundColor);
   assert.notEqual(highlight,geometry.background,`${name} hover must visibly highlight the card`);
   if(width===2048&&theme==='dark')await page.screenshot({path:work+`/ui/${name==='模板'?'templates':'lab'}.png`});
   frame.catalogs.push({name,...geometry,highlight});
  }
  await nav('提交记录').click();await page.locator('.submission-record-actions').first().waitFor();
  const actions=await page.locator('.submission-record-actions').evaluateAll(nodes=>nodes.filter(n=>n.getBoundingClientRect().height&&n.closest('.submission-log-row').getAttribute('aria-hidden')!=='true').map(n=>{const code=n.querySelector('.submission-code-button').getBoundingClientRect(),verdict=n.querySelector('.verdict').getBoundingClientRect();return {codeX:code.x,gap:verdict.left-code.right};}));
  assert(actions.length>=2);assert(actions.every(a=>a.gap>=0&&a.gap<=8),JSON.stringify(actions));assert(Math.max(...actions.map(a=>a.codeX))-Math.min(...actions.map(a=>a.codeX))<=1);
  frame.submissionActions=actions;
  await nav('成长与能力').click();await page.locator('.account-hero-statistics>div').last().waitFor();
  const growth=await page.locator('.growth-account-hero').evaluate(n=>{const goals=n.querySelector('.account-hero-goals').getBoundingClientRect(),stats=[...n.querySelectorAll('.account-hero-statistics b')].map(x=>x.getBoundingClientRect());return {lastStatisticToGoals:goals.top-Math.max(...stats.map(x=>x.bottom)),panelHeight:n.clientHeight};});
  assert(growth.lastStatisticToGoals>=0&&growth.lastStatisticToGoals<=85,JSON.stringify(growth));
  frame.growth=growth;frames.push(frame);
  if(width===2048&&theme==='dark')await page.screenshot({path:work+'/ui/growth.png'});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(work+'/visual-alignment-ui.json',JSON.stringify({ok:true,realApp:true,frames},null,2));console.log('Visual alignment passed: centered cards, visible hover, compact aligned submission actions and balanced growth panel in six desktop/theme layouts.');
} finally {await browser.close();}
