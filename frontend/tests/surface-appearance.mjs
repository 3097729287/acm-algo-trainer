import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';

export async function checkSurfaceAppearance({page,nav}) {
 const out='../.backups/surface-appearance-20261106';await mkdir(out,{recursive:true});
 const saved=await page.locator('html').evaluate(node=>({style:node.getAttribute('style'),theme:node.dataset.theme,panel:node.dataset.panelStyle,motion:node.dataset.motion}));
 const override=await page.addStyleTag({content:':root{}'}),proof=[];
 const bookmarks=()=>page.locator('#tb-page-bookmarks');
 const mine=()=>page.locator('#section-panel-mine .list-page');
 const task=()=>page.locator('.section-document:not([hidden]) .task-card').first();
 const mode=async(theme,preset,opacity,extra='')=>{
  await override.evaluate((node,{opacity,extra})=>node.textContent=`:root{--panel-opacity:${opacity}%!important;${extra}}`,{opacity,extra});
  await page.locator('html').evaluate((node,{theme,preset})=>{node.dataset.theme=theme;node.dataset.panelStyle=preset;node.dataset.motion='off';},{theme,preset});
 };
 const paint=locator=>locator.evaluate(node=>{
  const alpha=color=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,1,1);return ctx.getImageData(0,0,1,1).data[3]/255;};
  let transparency=1,contentOpacity=1;for(let item=node;item&&!item.matches('.workspace-area,body');item=item.parentElement){transparency*=1-alpha(getComputedStyle(item).backgroundColor);contentOpacity*=Number(getComputedStyle(item).opacity);}
  const style=getComputedStyle(node);return {alpha:1-transparency,contentOpacity,text:alpha(style.color),border:style.borderTopStyle,borderColor:style.borderTopColor,radius:style.borderTopLeftRadius,image:style.backgroundImage};
 });
 const near=(actual,expected,context)=>assert(Math.abs(actual-expected)<.006,context+': '+actual+' expected '+expected);
 try{
  for(const theme of ['dark','light'])for(const preset of ['minimal','outlined','aurora','blueprint'])for(const opacity of [0,44,76,100]){
   await nav('我的训练').click();await bookmarks().getByRole('tab',{name:'我的训练',exact:true}).click();await mode(theme,preset,opacity);
   const list=await paint(mine()),header=await paint(mine().locator('thead th').first()),group=await paint(mine().locator('.queue-heading td').first()),row=await paint(mine().locator('tr[data-id] td').first()),footer=await paint(mine().locator('.list-footer'));
   for(const [name,value] of Object.entries({list,header,group,row,footer})){near(value.alpha,opacity/100,`${theme}/${preset}/${opacity}/${name}`);assert.equal(value.contentOpacity,1);assert.equal(value.text,1);}
   await nav('任务').click();await bookmarks().getByRole('tab',{name:'学习概览',exact:true}).click();await task().waitFor();await mode(theme,preset,opacity);
   const card=await paint(task());near(card.alpha,opacity/100,'task '+JSON.stringify({theme,preset,opacity}));assert.equal(card.contentOpacity,1);assert.equal(card.text,1);
   for(const property of ['border','borderColor','radius','image'])assert.equal(card[property],list[property],`${property} matches between tasks and training`);
   assert.equal(card.border,preset==='blueprint'?'dashed':'solid');assert.equal(card.radius,({minimal:'10px',outlined:'18px',aurora:'22px',blueprint:'3px'})[preset]);
   if(opacity===0)assert(!card.image.match(/\/ (?!0(?:[\s,) ]|$))[\d.]+/),'No decorative color remains when opacity is zero');
   if(opacity===44&&['outlined','blueprint'].includes(preset))await page.screenshot({path:`${out}/tasks-${theme}-${preset}.png`});
   proof.push({theme,preset,opacity,headerGroupAndBodyOneFill:true,taskPresetMatches:true});
  }
  for(const view of ['学习概览','本周计划','专题进度','历史记录']){
   await bookmarks().getByRole('tab',{name:view,exact:true}).click();await mode('dark','blueprint',31);
   near((await paint(task())).alpha,.31,'Task page follows shared opacity '+view);assert.equal((await paint(task())).border,'dashed');
  }
  await bookmarks().getByRole('tab',{name:'学习概览',exact:true}).click();await page.getByRole('button',{name:'可用时间',exact:true}).click();
  await mode('light','blueprint',44,'--opacity-popups:37%!important;');
  const dialog=page.getByRole('dialog',{name:'可用时间',exact:true}),dialogPaint=await paint(dialog);
  near(dialogPaint.alpha,.37,'Portal dialog uses its own opacity');assert.equal(dialogPaint.border,'dashed');assert.equal(dialogPaint.radius,'3px');
  await page.keyboard.press('Escape');await dialog.waitFor({state:'detached'});
  await nav('我的训练').click();await mode('dark','outlined',88,'--opacity-mine:19%!important;--opacity-library:67%!important;');
  near((await paint(mine())).alpha,.19,'Mine override');
  await bookmarks().getByRole('tab',{name:'题库',exact:true}).click();await mode('dark','outlined',88,'--opacity-mine:19%!important;--opacity-library:67%!important;');
  near((await paint(page.locator('#section-panel-library .list-page'))).alpha,.67,'Library override');
  await bookmarks().getByRole('tab',{name:'我的训练',exact:true}).click();await mode('dark','outlined',44);
  const scroll=mine().getByRole('region',{name:'题目列表'}),head=mine().locator('thead');await page.mouse.move(0,0);
  const before=await head.screenshot();await scroll.evaluate(node=>node.scrollTop=77);await page.waitForTimeout(120);
  assert.equal(await mine().locator('tbody').evaluate(node=>getComputedStyle(node).clipPath),'inset(77px 0px 0px)');
  assert(before.equals(await head.screenshot()),'Scrolling rows do not paint through the translucent sticky header');
  assert(await scroll.evaluate(node=>node.scrollTop===77));await scroll.evaluate(node=>node.scrollTop=0);
  for(const [width,fontSize] of [[2048,16],[1280,18],[430,22]]){
   await page.setViewportSize({width,height:1000});await page.locator('html').evaluate((node,size)=>node.style.setProperty('--ui-font-size',size+'px'),fontSize);
   await page.screenshot({path:`${out}/training-${width}.png`});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await nav('任务').click();await mode('dark','outlined',44);await page.screenshot({path:`${out}/tasks-${width}.png`});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await nav('我的训练').click();
  }
  await page.setViewportSize({width:1600,height:1000});
  const result={ok:true,cases:proof.length,proof,taskViewsShareOpacity:true,independentPageOverrides:true,portalFollowsPreset:true,stickyHeaderDoesNotLeakRows:true,responsive:true,textAndControlsOpaque:true};
  await writeFile(`${out}/appearance-checks.json`,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,proof:undefined}));
 }catch(error){await page.screenshot({path:`${out}/failure.png`,fullPage:true});throw error;}
 finally{
  await override.evaluate(node=>node.remove());await page.locator('html').evaluate((node,saved)=>{node.setAttribute('style',saved.style||'');node.dataset.theme=saved.theme;node.dataset.panelStyle=saved.panel;node.dataset.motion=saved.motion;},saved);
  await nav('我的训练').click();await bookmarks().getByRole('tab',{name:'我的训练',exact:true}).click();
 }
}
