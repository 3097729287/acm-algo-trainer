import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/library-backgrounds/lab-reset';await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
await page.addInitScript(()=>{if(!localStorage.getItem('reset-fixture-seeded')){localStorage.setItem('learning-fixture.fixture-A.prefs',JSON.stringify({learningPaths:{'sorting-basics':{mode:'guided',labV1:{chapter:'applications',passed:{verified:true},drafts:{note:'existing work'}},guided:{problems:{one:{code:'existing code'}}}}}}));localStorage.setItem('reset-fixture-seeded','true');}});
const lab=page.locator('.study-lab:not([hidden])'),position=lab.locator('.lab-position');
const open=tab=>page.evaluate(tab=>studyFixture.open({...tab,newTab:true}),tab);
const beginning=async()=>{await page.waitForFunction(()=>document.querySelector('.study-lab:not([hidden]) .lab-position')?.textContent.trim()==='1 / 4');assert.equal(await lab.locator('.lab-lesson').evaluate(node=>node.scrollTop),0);};
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/learning-browser-fixture.html');await page.waitForFunction(()=>!!window.studyFixture);await open({kind:'lab',id:'sorting-basics',title:'排序基础'});await beginning();
 const input=lab.getByRole('textbox',{name:'排序实验数组'});await input.fill('9 3 9 1');await lab.getByRole('button',{name:'应用',exact:true}).click();await lab.locator('[aria-label="实验步骤"]').getByRole('button',{name:'下一步',exact:true}).click();await lab.locator('.lab-course-header').getByRole('button',{name:'下一页',exact:true}).click();assert.equal(await position.innerText(),'2 / 4');
 await open({kind:'wiki',id:'ds/stack',title:'栈'});await page.locator('.study-wiki:not([hidden])').waitFor();await page.getByRole('tab',{name:'排序基础',exact:true}).click();await beginning();assert.equal(await input.inputValue(),'5 2 5 1 4 2');
 for(let i=0;i<3;i++)await lab.locator('.lab-course-header').getByRole('button',{name:'下一页',exact:true}).click();assert.equal(await position.innerText(),'4 / 4');await page.evaluate(()=>studyFixture.hide());await open({kind:'lab',id:'sorting-basics',title:'排序基础'});await beginning();
 const kept=await page.evaluate(()=>studyFixture.prefs().learningPaths['sorting-basics']);assert.deepEqual(kept.labV1.passed,{verified:true});assert.deepEqual(kept.labV1.drafts,{note:'existing work'});assert.equal(kept.guided.problems.one.code,'existing code');
 await page.reload();await beginning();assert.deepEqual(errors,[]);const result={ok:true,oldPositionIgnored:true,tabReturnRestarts:true,reopenRestarts:true,reloadRestarts:true,experimentStartsOver:true,learningFactsAndWorkPreserved:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await server.close();}
