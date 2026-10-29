import assert from 'node:assert/strict';
import fs from 'node:fs';
import {nextActions,learningEvidence,trustedDifficulty,LAB_ACTIONS,NEXT_ACTION_POLICY} from '../src/lib/nextActions.js';
import {availablePages} from '../src/lib/navigationVisibility.js';

const now=Date.parse('2026-10-29T04:00:00Z'),pages=availablePages(11);
const row=(id,extra={})=>({id,title:id,tags:['数组'],difficulty:1000,difficultySource:'Codeforces 官方 rating',
 difficultyConfidence:'HIGH',platform:'Codeforces',catalogContentReady:true,...extra});
const fact=(item,date='2026-10-28T00:00:00Z',extra={})=>({id:item.id,problemId:item.id,solved:true,weight:1,
 difficulty:item.difficulty,failures:0,date,...extra});
const insight=(facts,extra={})=>({assessment:{model:{method:'rasch-practice-evidence-v2',version:2},
 evidence:facts,qualified:facts.filter(item=>item.solved).length>=5,abilityScore:1200,...extra}});
const foundation=[1,2,3].map(n=>row('foundation-'+n,{accepted:true,tags:['数组','模拟']}));
const foundationFacts=foundation.map((item,i)=>fact(item,`2026-10-${26+i}T00:00:00Z`));
const prefix=row('prefix-new',{tags:['前缀和'],difficulty:1200});
const drill1=row('template-drill:prefix-difference:1',{tags:['前缀和'],difficulty:null,difficultySource:'',catalogHidden:true});
const drill2=row('template-drill:prefix-difference:2',{tags:['前缀和'],difficulty:null,difficultySource:'',catalogHidden:true});
const template={id:'builtin:prefix-difference',title:'前缀和与差分',tags:['前缀和','差分'],builtin:true,
 practiceIds:[drill1.id,drill2.id],practicePassed:[false,false]};
const base={rows:[...foundation,prefix,drill1,drill2],insights:insight(foundationFacts),availablePages:pages,
 templates:[template],now};
let count=0;const test=(name,run)=>{run();count++;console.log('PASS '+name);};

test('a beginner follows a real incomplete foundation unit with first-level help',()=>{
 const tasks=[1,2,3,4].map(n=>row('syntax-'+n,{tags:['模拟']}));
 const lists=[{id:'source:syntax',title:'输入输出与顺序结构',topicPath:['语言入门','顺序结构'],available:true,
  problems:tasks.map(item=>({problemId:item.id}))}];
 const result=nextActions({rows:tasks,lists,availablePages:pages,now});
 assert.equal(result[0].kind,'list');assert.match(result[0].reason,/独立通过 0/);assert.match(result[0].reason,/一级帮助/);
 assert(!result.some(item=>['course','template','stretch','contest'].includes(item.kind)));
});
test('XP, synced AC totals and assisted/local results do not bypass foundations',()=>{
 const rows=[...foundation,row('basic-new')];
 const result=nextActions({rows,availablePages:pages,now,insights:{growth:{level:100,xp:999999,
  ranked:{qualified:true,abilityScore:2300,evidenceCount:100}},knowledgeEvidence:[{id:foundation[0].id,independence:1}]}});
 assert.equal(result[0].id,'basic-new');assert.match(result[0].reason,/独立通过 0/);
 assert(!result.some(item=>['course','stretch'].includes(item.kind)));
});
test('the real lesson comes before its operation exercises',()=>{
 const result=nextActions(base);assert.equal(result[0].kind,'course');assert.equal(result[0].id,'prefix-difference');
 assert.match(result[0].reason,/前置/);assert(!result.some(item=>item.kind==='template-problem'));
 const saved=nextActions({...base,prefs:{learningPaths:{activePath:'prefix-difference','prefix-difference':{mode:'learn',labV1:{chapter:'sum'}}}}});
 assert.equal(saved[0].kind,'course');assert.match(saved[0].reason,/按保存章节继续/);
});
test('an implementation position offers a diagnostic, never claims course completion',()=>{
 const result=nextActions({...base,prefs:{learningPaths:{'prefix-difference':{mode:'learn',labV1:{chapter:'code'}}}}});
 assert.equal(result[0].id,drill1.id);assert.equal(result[0].kind,'template-problem');
 assert.match(result[0].reason,/先检验实现，再用独立官方题/);
});
test('actual template practicePassed advances drills and then hands off to an official problem',()=>{
 const prefs={learningPaths:{'prefix-difference':{mode:'guided'}}};
 const second=nextActions({...base,prefs,templates:[{...template,practicePassed:[true,false]}]});
 assert.equal(second[0].id,drill2.id);
 const done=nextActions({...base,prefs,templates:[{...template,practicePassed:[true,true]}]});
 assert.equal(done[0].id,prefix.id);assert.equal(done[0].kind,'problem');assert.match(done[0].reason,/独立实现/);
 assert.equal(learningEvidence(base.rows,base.insights,now).all.solved,3);
});
test('already accepted originals and completed operations are never new recommendations',()=>{
 const result=nextActions({...base,rows:base.rows.map(item=>item.id===prefix.id?{...item,accepted:true}:item),
  prefs:{learningPaths:{'prefix-difference':{mode:'guided'}}},templates:[{...template,practicePassed:[true,true]}]});
 assert(!result.some(item=>[prefix.id,drill1.id,drill2.id].includes(item.id)));
});
test('a missing prerequisite diverts Dijkstra to the real BFS lesson',()=>{
 const result=nextActions({...base,rows:[...foundation,row('shortest',{tags:['最短路']})],templates:[],
  prefs:{learningPaths:{activePath:'dijkstra',dijkstra:{mode:'learn'}}}});
 assert.equal(result[0].id,'bfs');assert.match(result[0].reason,/Dijkstra.*BFS/);
});
test('fresh independent representative evidence skips an unfinished foundation list',()=>{
 const tasks=[...foundation,row('spare-basic')];
 const lists=[{id:'source:array',title:'数组与字符串',topicPath:['语言入门','数组'],available:true,
  problems:tasks.map(item=>({problemId:item.id}))}];
 const result=nextActions({...base,rows:[...tasks,prefix,drill1,drill2],lists});
 assert(!result.some(item=>item.kind==='list'));assert.equal(result[0].kind,'course');
});
test('due reviewTask dates use Shanghai dates and take priority over new learning',()=>{
 const due=row('due',{accepted:true}),future=row('future',{accepted:true});
 const result=nextActions({...base,rows:[...base.rows,due,future],now:Date.parse('2026-10-28T16:01:00Z'),
  training:[{...future,queue:'review',reviewTask:{due:'2026-10-30'}},{...due,queue:'check',reviewTask:{due:'2026-10-29'}}]});
 assert.equal(result[0].id,'due');assert(!result.some(item=>item.id==='future'));
});
test('the server review budget prevents an unbounded new curriculum queue',()=>{
 const due=row('due',{accepted:true,queue:'review',reviewTask:{due:'2026-10-28'}});
 const result=nextActions({...base,training:[due],reviewPlan:{reviewOnly:true,newMinutes:0}});
 assert.deepEqual(result.map(item=>item.kind),['review']);
 assert.deepEqual(nextActions({...base,reviewPlan:{newMinutes:10}}),[]);
 assert.equal(nextActions({...base,reviewPlan:{}})[0].kind,'course');
});
test('same-day cramming and crossing midnight for a few minutes do not establish retention',()=>{
 const close=foundation.map((item,i)=>fact(item,`2026-10-28T${15+i}:55:00Z`));
 assert.equal(learningEvidence(foundation,insight(close),now).all.stable,false);
 const result=nextActions({...base,insights:insight(close),rows:[...base.rows,row('basic-new')]});
 assert.equal(result[0].id,'basic-new');
});
test('stale, future, invalid, zero-weight and explicitly non-independent evidence cannot unlock',()=>{
 for(const change of [{date:'2026-01-01T00:00:00Z'},{date:'2026-11-01T00:00:00Z'},{date:'invalid'},
  {weight:0},{independentKnown:false},{scope:'local'}]){
  const facts=foundationFacts.map(item=>({...item,...change}));
  assert.equal(learningEvidence(foundation,insight(facts),now).all.solved,0);
 }
 assert.equal(learningEvidence(foundation.map(item=>({...item,difficultySource:''})),insight(foundationFacts),now).all.solved,0);
});
test('aliases of an exact original cannot manufacture the required evidence count',()=>{
 const a=row('a',{url:'https://codeforces.com/contest/1/problem/A'}),b=row('b',{url:'https://codeforces.com/problemset/problem/1/A',aliasIds:['old-b']});
 const value=learningEvidence([a,b],insight([fact(a,'2026-10-26T00:00:00Z'),fact(b)]),now);
 assert.equal(value.all.solved,1);assert.equal(value.all.stable,false);
 const tie=learningEvidence([a,b],insight([fact(a),fact(b,undefined,{solved:false})]),now);
 assert.equal(tie.all.solved,0);
});
test('real failures and repeated retries hold back progression',()=>{
 const failures=[1,2,3].map(n=>row('failed-'+n));
 const value=learningEvidence([...foundation,...failures],insight([...foundationFacts,...failures.map(item=>fact(item,undefined,{solved:false}))]),now);
 assert.equal(value.all.stable,false);
 assert.equal(learningEvidence(foundation,insight(foundationFacts.map(item=>({...item,failures:3,weight:.5}))),now).all.stable,false);
});
test('cross-platform evidence uses summed weight, and is not incorrectly classified as assisted',()=>{
 const value=learningEvidence(foundation,insight(foundationFacts.map(item=>({...item,weight:.25}))),now);
 assert.equal(value.all.weight,.75);assert.equal(value.all.stable,true);
});
test('unknown/unreviewed difficulty, incomplete statements and locked content are excluded',()=>{
 assert(!trustedDifficulty(row('unknown',{difficulty:null})));assert(!trustedDifficulty(row('source-missing',{difficultySource:''})));
 assert(!trustedDifficulty(row('pending',{difficultySource:'待核验'})));
 const rows=[row('incomplete',{catalogContentReady:false}),row('locked',{locked:true}),row('hidden',{catalogHidden:true}),row('unknown',{difficulty:null})];
 assert.deepEqual(nextActions({rows,availablePages:pages,now}),[]);
});
test('a stable user gets a small stretch only when every concrete technique is supported',()=>{
 const supported=[...foundation,...[1,2,3].map(n=>row('prefix-'+n,{accepted:true,tags:['前缀和']}))];
 const facts=[...foundationFacts,...supported.slice(3).map((item,i)=>fact(item,`2026-10-${26+i}T00:00:00Z`))];
 const mixed=row('bad-stretch',{difficulty:1300,tags:['数组','网络流']}),stretch=row('stretch',{difficulty:1400,tags:['前缀和']});
 const result=nextActions({rows:[...supported,mixed,stretch],insights:insight(facts),availablePages:pages,now});
 assert.equal(result[0].id,'stretch');assert.equal(result[0].kind,'stretch');assert.match(result[0].reason,/保守训练参考/);
 assert(!result.some(item=>item.id==='bad-stretch'));
});
test('hidden and locked pages do not leak dependent actions; active contests stay exclusive',()=>{
 const hidden=nextActions({...base,availablePages:availablePages(11,{hiddenNavPages:['paths','templates','library']})});
 assert(!hidden.some(item=>['course','template','template-problem','stretch'].includes(item.kind)));
 assert.deepEqual(nextActions({...base,activeContest:{id:'active',name:'当前试卷'}}).map(item=>item.kind),['contest']);
 assert.deepEqual(nextActions({...base,availablePages:['mine'],activeContest:{id:'active',name:'当前试卷'}}),[]);
});
test('a completed standalone template hands off to official practice without inventing a lab',()=>{
 const strings=foundation.map(item=>({...item,tags:['数组','模拟','字符串']}));
 const task=row('kmp-official',{tags:['KMP'],difficulty:1200});
 const built={id:'builtin:kmp',title:'KMP',builtin:true,tags:['KMP'],practiceIds:['kmp-operation'],practicePassed:[true]};
 const result=nextActions({rows:[...strings,task],templates:[built],insights:insight(foundationFacts),availablePages:pages,now});
 assert.equal(result[0].id,'kmp-official');assert.equal(result[0].kind,'problem');
 assert(!result.some(item=>item.kind==='course'));
});
test('a started review is preserved before an older unopened review',()=>{
 const older=row('older',{queue:'review',reviewTask:{due:'2026-10-25'}});
 const started=row('started',{queue:'check',reviewTask:{due:'2026-10-28',openedAt:'2026-10-29T00:00:00Z'}});
 const result=nextActions({...base,training:[older,started],reviewPlan:{reviewOnly:true}});
 assert.equal(result[0].id,'started');
});
test('pending, absent and only broad topic metadata cannot prove a prerequisite',()=>{
 for(const fields of [{knowledgeReviewRequired:true},{tags:[]},{tags:['图论','动态规划','数学']}]){
  const tasks=foundation.map(item=>({...item,...fields})),value=learningEvidence(tasks,insight(foundationFacts),now);
  assert.equal(value.all.solved,3);assert.equal(value.forTopics(['数组','图论','动态规划','数学']).solved,0);
 }
});
test('an unrated complete old task remains eligible for its actual due review',()=>{
 const task=row('unrated-review',{difficulty:null,difficultySource:'',accepted:true,queue:'review',reviewTask:{due:'2026-10-29'}});
 const result=nextActions({...base,training:[task],reviewPlan:{reviewOnly:true}});
 assert.equal(result[0].kind,'review');assert.equal(result[0].id,task.id);
});
test('equivalent independent basics across source lists do not force an experienced user to clear spare syntax questions',()=>{
 const experienced=[...foundation,...[4,5].map(n=>row('equivalent-'+n,{accepted:true,tags:['数组','排序','模拟']}))];
 const facts=[...foundationFacts,...experienced.slice(3).map(item=>fact(item))];
 const spare=[1,2,3,4].map(n=>row('spare-syntax-'+n,{tags:['模拟']}));
 const lists=[{id:'source:spare',title:'输入输出与顺序结构',topicPath:['语言入门','顺序结构'],available:true,problems:spare.map(item=>({problemId:item.id}))}];
 const result=nextActions({...base,rows:[...experienced,...spare,prefix,drill1,drill2],lists,insights:insight(facts)});
 assert(!result.some(item=>item.kind==='list'));assert.equal(result[0].id,'prefix-difference');
});
test('an unsupported advanced bookmark does not suppress another ready learning path',()=>{
 const result=nextActions({...base,prefs:{learningPaths:{activePath:'knapsack',knapsack:{mode:'learn'}}}});
 assert.equal(result[0].id,'prefix-difference');
});
test('stable breadth offers an actual complete unseen mixed paper without starting it',()=>{
 const supported=[1,2,3,4,5,6,7,8].map(n=>row('mixed-proof-'+n,{accepted:true,tags:['数组','排序','前缀和']}));
 const facts=supported.map((item,i)=>fact(item,`2026-10-${26+i%3}T00:00:00Z`));
 const paper=[row('paper-a',{tags:['数组'],difficulty:1000}),row('paper-b',{tags:['排序'],difficulty:1100}),row('paper-c',{tags:['前缀和'],difficulty:1200})]
  .map((item,index)=>({...item,contest:'真实完整练习赛',contestId:'100',contestRoster:true,problem:String.fromCharCode(65+index),contestProblemCount:3}));
 const config={rows:[...supported,...paper],insights:insight(facts),availablePages:pages,now};
 const result=nextActions(config);assert.equal(result[0].kind,'mixed');assert.equal(result[0].page,'mock');
 assert.equal(result[0].contest,'真实完整练习赛');assert.match(result[0].reason,/去模拟赛选择/);
 assert(!Object.hasOwn(result[0],'start'));assert(!Object.hasOwn(result[0],'durationMinutes'));
 for(const changed of [paper.slice(0,2),paper.map((item,i)=>i===2?{...item,catalogContentReady:false}:item),
  paper.map((item,i)=>i===2?{...item,tags:['数组','网络流']}:item),paper.map((item,i)=>i===2?{...item,accepted:true}:item),
  paper.map(item=>({...item,contestProblemCount:null})),paper.map((item,i)=>i===2?{...item,difficulty:null}:item),
  paper.map((item,i)=>i===2?{...item,problem:'D'}:item),paper.map((item,i)=>i===2?{...item,problem:'A'}:item),
  paper.map((item,i)=>i===2?{...item,contestId:'another'}:item),paper.map((item,i)=>i===2?{...item,contestVariant:'another'}:item),
  paper.map(item=>({...item,contestRoster:false})),paper.map((item,i)=>i===2?{...item,problemKind:'interactive'}:item)]){
  assert(!nextActions({...config,rows:[...supported,...changed]}).some(item=>item.kind==='mixed'));
 }
 const paused=nextActions({...config,reviewPlan:{reviewOnly:true}});assert(!paused.some(item=>item.kind==='mixed'));
 const hidden=nextActions({...config,availablePages:pages.filter(page=>page!=='mock')});assert(!hidden.some(item=>item.kind==='mixed'));
});
test('unfinished prerequisite study outranks a possible mixed paper',()=>{
 const supported=[1,2,3,4,5,6,7,8].map(n=>row('breadth-'+n,{accepted:true,tags:['数组','模拟','排序','前缀和']}));
 const facts=supported.map((item,i)=>fact(item,`2026-10-${26+i%3}T00:00:00Z`));
 const paper=['数组','排序','前缀和'].map((tag,i)=>row('complete-'+i,{tags:[tag],contest:'完整试卷',contestId:'101',contestRoster:true,problem:String.fromCharCode(65+i),contestProblemCount:3}));
 const result=nextActions({rows:[...supported,...paper,row('bfs-study',{tags:['BFS']})],insights:insight(facts),availablePages:pages,now,
  prefs:{learningPaths:{activePath:'bfs',bfs:{mode:'learn'}}}});
 assert.equal(result[0].kind,'course');assert.equal(result[0].id,'bfs');assert(!result.some(item=>item.kind==='mixed'));
});
test('lesson IDs are shipped, actions stay bounded and the model does not mutate its inputs',()=>{
 const sorting=JSON.parse(fs.readFileSync(new URL('../../backend/resources/sorting-lab.json',import.meta.url)));
 const graph=JSON.parse(fs.readFileSync(new URL('../../backend/resources/graph-lab.json',import.meta.url)));
 const actual=new Set([...Object.keys(sorting),...Object.keys(graph),'prefix-difference','two-pointers','knapsack']);
 assert(LAB_ACTIONS.every(course=>actual.has(course.id)));
 const input=structuredClone(base),before=JSON.stringify(input);const result=nextActions(input);
 assert.equal(JSON.stringify(input),before);assert(result.length<=NEXT_ACTION_POLICY.maxActions);
 assert(result.every(item=>item.reason.length>20));assert.deepEqual(nextActions({...base,rows:[],training:[],insights:{},templates:[]}),[]);
});
console.log(`PASS ${count} evidence-backed learning recommendation scenarios`);
