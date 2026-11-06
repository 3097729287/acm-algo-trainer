import assert from 'node:assert/strict';
import {BACKGROUND_CARDS} from '../src/lib/stickerCatalogue.js';
import {chooseBuiltinBackground,chooseRewardBackground,ownedBackgrounds,workspaceBackground} from '../src/lib/workspaceBackground.js';
import {mergeLearningTasks} from '../src/lib/learningTaskRows.js';

const prefs={backdrop:'meteors',learningPaths:{activePath:'arrays',browserV1:{version:1,tabs:[]}}};
const inventory={owner:'alice',revision:4,catalogue:BACKGROUND_CARDS,units:[{id:'old-rarity-copy',stickerId:'background-night-legendary',placement:{x:.5,y:.5}}]};
const before=JSON.stringify({prefs,inventory});
const selected=chooseRewardBackground(prefs,'background-night-legendary');
assert.equal(workspaceBackground(selected,inventory,'alice').id,'meteors');
assert.equal(ownedBackgrounds(inventory,'alice').length,1);
assert.deepEqual(ownedBackgrounds(inventory,'bob'),[]);
assert.equal(workspaceBackground(selected,inventory,'bob').id,'none');
assert.equal(workspaceBackground(selected,{...inventory,units:[]},'alice').source,'builtin');
assert.equal(workspaceBackground(chooseBuiltinBackground(selected,'custom'),inventory,'alice',{level:10}).kind,'image');
assert.equal(workspaceBackground(chooseBuiltinBackground(selected,'none'),inventory,'alice').kind,'none');
assert.equal(workspaceBackground(chooseBuiltinBackground(selected,'custom'),inventory,'alice',{level:9}).kind,'none');
for(const id of ['meteors','grid','aurora','sunset'])assert.equal(workspaceBackground({...prefs,backdrop:id},inventory,'alice',{level:20}).kind,'none');
assert(ownedBackgrounds(inventory,'alice').every(item=>!('rarity' in item)));
assert.equal(selected.learningPaths.activePath,'arrays');
assert.deepEqual(selected.learningPaths.browserV1,prefs.learningPaths.browserV1);
assert.equal(JSON.stringify({prefs,inventory}),before,'Choosing a background cannot change reward copies or stored paths');
assert(ownedBackgrounds({...inventory,unlimited:true},'alice')[0].unlimited);
assert.equal(BACKGROUND_CARDS.length,7);
for(const theme of ['globe','cells','halo','rings','dots','underground','rain','river','galaxy','desert','snow']){
 const legacy={...inventory,units:[{id:'original-copy',stickerId:'background-'+theme+'-legendary',placement:null}]};
 const rain=ownedBackgrounds(legacy,'alice');assert.equal(rain.length,1);assert.equal(rain[0].theme,'rainfall');assert.equal(rain[0].count,1);assert.equal(legacy.units[0].id,'original-copy');
}

const index=[{key:'problem:p',kind:'problem',id:'p',title:'原题标题',trainingGroup:'pending',trainingOrder:100000},{key:'lecture:l',kind:'lecture',id:'l',title:'已有讲解'}];
const plan={tasks:[{key:'p-solve',id:'p',kind:'problem',title:'计划题名',status:'done',order:2},{key:'p-review',id:'p',kind:'review',title:'复习同一道题',status:'pending',order:3},{key:'l-read',id:'l',kind:'lecture',title:'已有讲解',status:'pending',order:1},{key:'new',id:'new',kind:'course',title:'新课程',status:'pending',order:4}]};
const original=JSON.stringify({index,plan}),rows=mergeLearningTasks(index,plan);
assert.equal(rows.filter(row=>row.id==='p').length,1);
assert.equal(rows.find(row=>row.id==='p').title,'原题标题');
assert.equal(rows.find(row=>row.id==='p').summaryTask.key,'p-review');
assert.equal(rows.find(row=>row.id==='p').trainingLabel,'待完成');
assert.equal(rows.find(row=>row.id==='l').trainingLabel,'待完成');
assert.equal(rows.find(row=>row.id==='new').kind,'lab');
const finished=mergeLearningTasks(index,{tasks:plan.tasks.map(task=>({...task,status:'done'}))});
assert.equal(finished.find(row=>row.id==='p').trainingLabel,'已完成');
assert.equal(finished.find(row=>row.id==='l').trainingOrder,rows.find(row=>row.id==='l').trainingOrder,'Completion changes the status without moving the task');
assert.equal(JSON.stringify({index,plan}),original);
assert.deepEqual(mergeLearningTasks(index,null),index);
console.log(JSON.stringify({ok:true,ownedOnly:true,accountIsolation:true,legacyRarity:true,adminUnlimited:true,inventoryUnchanged:true,inlineTasksUnique:true,completionStable:true,originalDataUnchanged:true}));
