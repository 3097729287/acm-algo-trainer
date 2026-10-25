import {withContestLetters} from '../src/lib/contestLetters.js';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {activityMonths,monthDays,fitCompactActivityGrid} from '../src/lib/activityDate.js';
import {snapDifficulty,difficultyPointerValue} from '../src/lib/difficultyDrag.js';
import {compareProblemDifficulty} from '../src/lib/problemOrder.js';
import {organizeTrainingLists,compareTrainingLists} from '../src/lib/trainingListCatalog.js';
import {buildTrainingCurriculum,CURRICULUM_STAGES} from '../src/lib/trainingCurriculum.js';
assert.equal(activityMonths('2026-10').length,12);
assert.equal(activityMonths('2024-12').flatMap(monthDays).length,366);
assert.equal(activityMonths('2026-10')[0],'2025-11');
for(const [w,h] of [[1800,280],[1100,200],[350,220]]){
 const grid=fitCompactActivityGrid(w,h,365);
 assert.ok(grid.columns*grid.rows>=365);
 assert.ok(grid.columns*grid.size+(grid.columns-1)*3<=w);
 assert.ok(grid.rows*grid.size+(grid.rows-1)*3<=h);
}
const snap=x=>snapDifficulty(difficultyPointerValue(x,{left:0,width:412,min:0,max:4000}),{min:0,max:4000,step:100});
assert.equal(snap(106),1000);assert.equal(snap(110),1000);assert.equal(snap(112),1100);
for(const descending of [false,true]) {
 const rows=[{difficulty:null},{difficulty:2000},{difficulty:1000}].sort((a,b)=>compareProblemDifficulty(a,b,descending));
 assert.equal(rows.at(-1).difficulty,null);assert.equal(rows[0].difficulty,descending?2000:1000);
}
const lists=JSON.parse(fs.readFileSync('../data/library/training_lists.json','utf8'));
const rows=JSON.parse(fs.readFileSync('../data/library/problems.json','utf8')).map(x=>x.encoded);
const original=organizeTrainingLists(lists),route=buildTrainingCurriculum(original,rows),seen=new Set();
for(const unit of route){
 assert.ok(CURRICULUM_STAGES.includes(unit.topicPath[0]));
 for(const problem of unit.problems){assert.ok(!seen.has(problem.problemId));seen.add(problem.problemId);}
 if(unit.curriculumOrder<100)assert.ok(unit.problems.length<=18);
}
assert.ok(route.length>30);assert.equal(original.length,563);
for(const stage of CURRICULUM_STAGES.slice(0,7))assert.ok(route.some(unit=>unit.topicPath[0]===stage),stage);
const first=route.filter(u=>u.curriculumOrder<100).sort(compareTrainingLists);
assert.equal(first[0].displayTitle,'输入输出与顺序结构');
for(const title of ['BFS 与最少步数','树状数组','拓扑排序与 DAG','数位 DP'])assert.ok(route.some(u=>u.displayTitle===title),title);
const examples=[['数据结构','树状数组','树状数组',2000,25],['图论','拓扑排序与 2-SAT','拓扑排序',1900,14],['搜索','综合练习','广度优先搜索 BFS',1500,12]];
for(const [category,topic,tag,difficulty,expected] of examples){
 const sample=buildTrainingCurriculum([{id:'x',available:true,title:topic,displayTitle:topic,topicPath:[category,topic],problems:[{problemId:'p'}]}],[{id:'p',tags:[tag],difficulty}]);
 assert.equal(sample[0].id,`curriculum:${expected}`);
}
console.log(JSON.stringify({ok:true,units:route.length,mainUnits:first.length,mainProblems:first.flatMap(u=>u.problems).length,uniqueProblems:seen.size}));

assert.deepEqual(withContestLetters([{problem:"A"},{problem:"C"},{problem:"G1"}]).map(r=>r.displayLetter),["A","C","G1"]);
assert.deepEqual(withContestLetters([{problem:"P14187"},{problem:"P14190"}]).map(r=>r.displayLetter),["A","B"]);
assert.ok(withContestLetters([{problem:"P14187"}])[0].localLetter);
