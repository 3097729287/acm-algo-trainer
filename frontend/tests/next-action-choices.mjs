import assert from 'node:assert/strict';
import {nextActionChoices,MAX_NEXT_ACTION_CHOICES} from '../src/lib/nextActionChoices.js';
const now=Date.parse('2026-11-05T03:00:00Z'),date='2026-11-05',availablePages=['mine','tasks','mock'],rows=[{id:'a',title:'已通过',accepted:true,catalogContentReady:true},{id:'b',title:'剩余训练题',catalogContentReady:true},{id:'c',title:'缺题面'},{id:'d',title:'已锁定',locked:true,catalogContentReady:true}];
const plan={tasks:[{key:'lesson',kind:'lecture',id:'lecture',title:'窗口边界',date,status:'pending'},{key:'future',kind:'problem',id:'c',title:'明天的任务',date:'2026-11-06',status:'pending'}]},dailyTasks={tasks:[{id:'daily',title:'训练',completed:false},{id:'done',completed:true,claimed:true}]};
const input={snapshot:{plan},items:[{kind:'review',id:'b',title:'复习'},{kind:'knowledge',id:'done',title:'已完成',completed:true}],training:rows,rows,dailyTasks,availablePages,now};
let choices=nextActionChoices(input);assert.equal(choices[0].id,'lecture');assert(choices.some(item=>item.kind==='daily'));assert(choices.some(item=>item.kind==='replay'));assert.equal(choices.filter(item=>item.id==='b').length,1);assert(!choices.some(item=>['a','c','d','done','future'].includes(item.id)));
assert.equal(choices.find(item=>item.kind==='daily').taskView,'overview');assert.notEqual(choices.find(item=>item.kind==='daily').id,'today');
choices=nextActionChoices({...input,snapshot:{plan:{tasks:plan.tasks.map(task=>({...task,status:'done'}))}}});assert.equal(choices[0].kind,'daily');assert(choices.some(item=>item.id==='b'));assert(!choices.some(item=>item.id==='lesson'));
choices=nextActionChoices({...input,snapshot:{recommendation:{title:'字符串'}},dailyTasks:null});assert.equal(choices[0].title,'字符串');assert(!choices[0].title.includes('推荐'));
assert.deepEqual(nextActionChoices({...input,activeContest:{id:'in-progress'}}),input.items);
assert(!nextActionChoices({...input,snapshot:{plan:{tasks:[]}},items:[],availablePages:[]}).some(item=>item.kind==='problem'||item.kind==='replay'||item.kind==='daily'));
assert.equal(nextActionChoices({...input,snapshot:null})[0].kind,'review');
const originalRows=[{id:'cf-a',aliasIds:['alias-a'],url:'https://codeforces.com/contest/123/problem/A'},{id:'cf-a-copy',url:'https://codeforces.com/problemset/problem/123/A'}];
const capped={snapshot:{plan:{tasks:[]}},availablePages:['mock'],rows:originalRows,items:[
 {kind:'problem',id:'cf-a',title:'第一道题'}, {kind:'problem',id:'alias-a',title:'题目别名'}, {kind:'random',id:'cf-a-copy',title:'同一道原题'},
 ...['第二道题','第二道题','第三道题'].map((title,index)=>({kind:'problem',id:'p'+index,title})),
 ...['甲','乙','丙'].flatMap((title,index)=>['lecture','review','template','course','specialized'].map(kind=>({kind,id:kind+index,title:kind+title}))),
 {kind:'replay',id:'contest-replay',title:'重现赛'},{kind:'replay',id:'replay-picker',title:'选择一场重现赛'},
]};
choices=nextActionChoices(capped);
assert.deepEqual(choices.filter(item=>item.kind==='problem').map(item=>item.title),['第一道题','第二道题']);
assert(!choices.some(item=>item.kind==='random'),'Original problem aliases do not return under another task type');
assert.equal(choices.length,MAX_NEXT_ACTION_CHOICES);assert.equal(choices.length-1,4,'Four alternatives remain beside the primary recommendation');
assert.equal(nextActionChoices({...capped,activeContest:{id:'in-progress'}}).length,MAX_NEXT_ACTION_CHOICES,'Active-contest choices follow the same total limit');
for(const kind of new Set(choices.map(item=>item.kind)))assert(choices.filter(item=>item.kind===kind).length<=2);
choices=nextActionChoices({...capped,items:capped.items.filter(item=>['replay','problem'].includes(item.kind))});assert.equal(choices.filter(item=>item.kind==='replay').length,1,'Both replay labels are one picker');
const plannedProblems={plan:{tasks:['a','b','c'].map(id=>({key:id,kind:'problem',id,title:id,date,status:'pending'}))}};
choices=nextActionChoices({...input,snapshot:plannedProblems,training:[],items:[]});assert.deepEqual(choices.filter(item=>item.kind==='problem').map(item=>item.id),['a','b']);
console.log('PASS pending work, one replay picker, same-original and repeated-label deduplication, at most two choices per kind including primary, and active-contest exclusivity');
