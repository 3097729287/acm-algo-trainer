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
for(const l of curriculum){assert.equal(l.topicPath.length,3);assert(l.directoryRow&&l.learningSequence);assert.match(l.topicPath[1],/^0[1-8] /);assert.match(l.topicPath[2],/^\d{2} /);assert(original.some(source=>source.id===l.sourceListId&&source.url===l.url));}
const sourceModel=trainingListModel(lists,rows,'source',[],14);
assert(sourceModel.index.own.get('nowcoder-926597').every(p=>(p.sections||[]).every(s=>!/^第.*章[：:]?\s*$/.test(s))));
const server=await createServer({cacheDir:'../.backups/followups-157/curriculum-vite',server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/nowcoder-curriculum-fixture.html');
 await page.locator('.catalog-folder-row').first().waitFor();
 assert.deepEqual(await page.locator('.catalog-folder-row strong').allTextContents(),NOWCODER_STAGES);
 await page.locator('.catalog-folder-row').filter({hasText:'01 编程基础'}).click();
 assert.equal(await page.locator('.catalog-folder-row').count(),6);assert.equal(await page.locator('.training-list-card').count(),0);
 await page.locator('.catalog-folder-row').filter({hasText:'01 输入输出与顺序结构'}).click();
 assert.equal(await page.locator('.training-list-card').count(),0);
 const names=await page.locator('.catalog-folder-row strong').allTextContents();assert.match(names[0],/^01 入门练习/);assert(names.some(n=>n.includes('精选练习')));
 await page.locator('.catalog-folder-row').first().click();await page.locator('.training-problem-row').first().waitFor();
 await page.locator('.problem-title').first().click();assert(await page.evaluate(()=>Boolean(window.openedProblem)));
 for(const width of [1100,800]){await page.setViewportSize({width,height:850});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
 assert.deepEqual(errors,[]);await fs.mkdir('../.backups/followups-157',{recursive:true});await page.screenshot({path:'../.backups/followups-157/nowcoder-learning.png'});
 console.log(JSON.stringify({ok:true,originalCollections:original.length,learningCollections:curriculum.length,unchangedProblemIdentities:1083,orderedStages:8,nestedDirectories:true,uniformRows:true}));
}finally{await browser.close();await server.close();}
