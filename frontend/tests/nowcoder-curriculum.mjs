import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {trainingListModel} from '../src/lib/trainingListModel.js';
import {NOWCODER_STAGES} from '../src/lib/nowcoderCurriculum.js';
const lists=JSON.parse(await fs.readFile(new URL('../../data/library/training_lists.json',import.meta.url),'utf8'));
const rows=JSON.parse(await fs.readFile(new URL('../../data/library/problems.json',import.meta.url),'utf8')).map(p=>p.encoded);
const snapshot=JSON.stringify(lists),model=trainingListModel(lists,rows,'algorithm',[],14);
const original=model.organized.filter(l=>l.id.startsWith('nowcoder-')&&!l.id.startsWith('nowcoder-curriculum:'));
const curriculum=model.organized.filter(l=>l.id.startsWith('nowcoder-curriculum:'));
const identities=items=>[...new Set(items.flatMap(l=>model.index.all(l.id).map(p=>p.row?.id||p.problemId)))].sort();
assert.deepEqual(identities(curriculum),identities(original),'The ordered projection retains every original problem identity');
assert.equal(identities(curriculum).length,1083);assert.equal(JSON.stringify(lists),snapshot);
assert(curriculum.every(list=>list.problems.length>2),'No orphan one- or two-problem supplement is generated');
for(const l of curriculum){assert.equal(l.topicPath.length,2);assert(!l.directoryRow&&l.learningSequence);assert.match(l.topicPath[1],/^0[1-8] /);assert(original.some(source=>source.id===l.sourceListId&&source.url===l.url));assert(l.problems.every(p=>!p.sections.length),'A generated learning list opens directly into its problems');assert.equal(new Set(l.problems.map(p=>p.problemId||p.url)).size,l.problems.length);for(const id of l.legacyIds)assert.equal(model.index.byList.get(id),l);}
console.log(JSON.stringify({learningCollections:curriculum.length,small:curriculum.filter(l=>l.problems.length<=2).map(l=>({title:l.title,count:l.problems.length})),intro:curriculum.filter(l=>l.topicPath[1]===NOWCODER_STAGES[0]).map(l=>({title:l.title,count:l.problems.length}))}));
const sourceModel=trainingListModel(lists,rows,'source',[],14);
assert(sourceModel.index.own.get('nowcoder-926597').every(p=>(p.sections||[]).every(s=>!/^第.*章[：:]?\s*$/.test(s))));
const compactRows=rows.map(({id,aliasIds,title,platform,url,tags,knowledge,difficulty,accepted})=>({id,aliasIds,title,platform,url,tags,knowledge,difficulty,accepted}));
const fixtureData=JSON.stringify({lists,rows:compactRows});
const server=await createServer({cacheDir:'../.backups/catalog-xp-20261107/vite',optimizeDeps:{entries:['tests/nowcoder-curriculum-fixture.html']},plugins:[{name:'public-curriculum-fixture',configureServer(server){server.middlewares.use('/__nowcoder-fixture',(_,response)=>{response.setHeader('Content-Type','application/json');response.end(fixtureData);});}}],server:{host:'127.0.0.1',port:0,watch:null,hmr:false}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/nowcoder-curriculum-fixture.html');
 await page.locator('.catalog-folder-row').first().waitFor();
 assert.deepEqual(await page.locator('.catalog-folder-row strong').allTextContents(),NOWCODER_STAGES);
 await page.locator('.catalog-folder-row').filter({hasText:'01 编程基础'}).click();
 assert.equal(await page.locator('.catalog-folder-row').count(),0);assert.equal(await page.locator('.training-list-card').count(),6);
 const names=await page.locator('.training-list-card strong').allTextContents();assert.equal(names[0],'输入输出与顺序结构');assert(!names.some(n=>/补充练习|精选练习/.test(n)));
 await page.getByRole('button',{name:'打开题单：输入输出与顺序结构',exact:true}).click();await page.locator('.training-problem-row').first().waitFor();assert.equal(await page.locator('.catalog-folder-row,.training-list-card').count(),0);
 await page.locator('.problem-title').first().click();assert(await page.evaluate(()=>Boolean(window.openedProblem)));
 for(const width of [2048,1100,800,390]){await page.setViewportSize({width,height:850});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
 assert.deepEqual(errors,[]);await fs.mkdir('../.backups/followups-157',{recursive:true});await page.screenshot({path:'../.backups/followups-157/nowcoder-learning.png'});
 const result={ok:true,originalCollections:original.length,learningCollections:curriculum.length,unchangedProblemIdentities:1083,orderedStages:8,stageCards:true,directProblemList:true,noOrphanSupplement:true,legacyIdsPreserved:true};await fs.mkdir('../.backups/catalog-xp-20261107/checks',{recursive:true});await fs.writeFile('../.backups/catalog-xp-20261107/checks/nowcoder.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();await server.close();}
