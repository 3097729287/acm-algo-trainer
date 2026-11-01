import assert from 'node:assert/strict';
import {recommendationState,learningEvidence} from '../src/lib/nextActions.js';
import {KNOWLEDGE_TOPICS,FOUNDATION_LESSONS,LEARNING_COURSES,lectureCurriculum,orderedLectures} from '../src/lib/learningCurriculum.js';
import {startKnowledge,cancelKnowledge,rotateKnowledge,knowledgeState,reconcileKnowledge,assignKnowledgeProblem,recordKnowledgeLesson} from '../src/lib/knowledgeJourney.js';
import {availablePages,migrateNavigationAccess} from '../src/lib/featureUnlocks.js';
import {readSocialCounts,saveSocialCounts,retainSocialCounts} from '../src/lib/socialSnapshot.js';

const start=Date.parse('2026-11-01T16:00:00Z'),pages=availablePages(8);
const row=(id,extra={})=>({id,title:id,url:'https://codeforces.com/contest/900/problem/'+id,tags:['并查集'],platform:'Codeforces',difficulty:1000,difficultySource:'Codeforces 官方 rating',difficultyConfidence:'HIGH',catalogContentReady:true,solutionAvailable:true,solutionState:'available',...extra});
const rows=['A','B','C','D'].map(id=>row(id));
const template={id:'builtin:dsu',title:'并查集',practicePassed:[true,true]};
const prepared={learnedLectures:FOUNDATION_LESSONS.map(item=>item.id),learningPaths:{dsu:{mode:'guided'}}};
const prefs=startKnowledge(prepared,'dsu',{rows,templates:[template],now:start});
const fact=(id,hours,extra={})=>({id,problemId:id,date:new Date(start+hours*3600000).toISOString(),solved:true,independentKnown:true,scope:'official',failures:0,...extra});
const insights=facts=>({learningEvidence:{version:1,method:'verified-official-learning-v1',records:facts}});
const model=(extra={})=>recommendationState({rows,prefs,templates:[template],availablePages:pages,now:start+3600000,...extra});
let count=0;const test=(name,run)=>{run();console.log('PASS '+name);count++;};
test('recommendations survive empty, completed, pending and review-only inputs',()=>{
 for(const input of [{},{rows:[]},{rows:rows.map(item=>({...item,accepted:true}))},{reviewPlan:{reviewOnly:true,newMinutes:0,tasks:[]}}, {availablePages:['mine','records','settings']}]){
  const result=recommendationState({availablePages:pages,now:start,...input});
  assert(result.items.length>0);assert(result.items[0].reason);assert(result.items.length<=6);
 }
 const active=model({activeContest:{id:'running',name:'当前比赛'}});assert.deepEqual(active.items.map(item=>item.kind),['contest']);
});
test('new users can reach teaching immediately; earned legacy access and hidden preferences survive',()=>{
 const beginner=availablePages(1);for(const id of ['library','paths','templates','lectures'])assert(beginner.includes(id));
 assert(!beginner.includes('rankings'));assert(!beginner.includes('mock'));
 const migrated=migrateNavigationAccess({hiddenNavPages:['templates'],learningPaths:{draft:'keep'}},2);
 assert(availablePages(2,migrated).includes('rankings'));assert(!availablePages(2,migrated).includes('templates'));assert.equal(migrated.learningPaths.draft,'keep');
 assert.equal(migrateNavigationAccess(migrated,5),migrated);
});
test('every lesson and topic prerequisite is real and acyclic; rollback DSU is advanced',()=>{
 const graph=new Map(FOUNDATION_LESSONS.map(item=>[item.id,item.prerequisites])),visited=new Set();
 const visit=(id,path=new Set())=>{assert(graph.has(id),id);assert(!path.has(id),'cycle '+id);if(visited.has(id))return;const next=new Set([...path,id]);for(const parent of graph.get(id))visit(parent,next);visited.add(id);};
 for(const id of graph.keys())visit(id);
 const topics=new Map(KNOWLEDGE_TOPICS.map(item=>[item.id,item]));
 const walk=(id,path=new Set())=>{assert(topics.has(id));assert(!path.has(id));for(const parent of topics.get(id).prerequisites)walk(parent,new Set([...path,id]));};
 for(const item of KNOWLEDGE_TOPICS){walk(item.id);for(const id of item.lectures)assert(graph.has(id));if(item.course)assert(LEARNING_COURSES[item.course]);}
 const rollback={id:'rollback',title:'可撤销并查集：线段树分治 + 可撤销并查集',tags:['基础','并查集']},basic=FOUNDATION_LESSONS[0];
 const metadata=lectureCurriculum(rollback);assert.equal(metadata.level,3);assert(metadata.prerequisites.includes('lecture:foundation-dsu'));
 assert.equal(orderedLectures([rollback,basic])[0].id,basic.id);
});
test('candidate refresh changes suggestions without starting or deleting progress',()=>{
 const before=model({prefs:prepared}),next=model({prefs:rotateKnowledge(prepared)});
 assert.notEqual(before.journey.suggestion.id,next.journey.suggestion.id);assert.equal(knowledgeState(prepared).activeTopicId,null);
 const paused=cancelKnowledge(prefs);assert.equal(knowledgeState(paused).activeTopicId,null);assert.equal(knowledgeState(paused).journeys.dsu.status,'paused');
 const resumed=startKnowledge(paused,'dsu',{rows,now:start+86400000});assert.equal(knowledgeState(resumed).journeys.dsu.id,knowledgeState(prefs).journeys.dsu.id);
});
test('starting DSU resumes its course; partial template checks cannot skip implementation',()=>{
 const begun=startKnowledge({...prepared,learningPaths:{}},'dsu',{rows,templates:[template],now:start});
 const lab=model({prefs:begun}).items[0];assert.equal(lab.kind,'course');assert.equal(lab.id,'dsu');assert(lab.resume);
 const partial=model({templates:[{...template,practicePassed:[true,false]}]});assert.equal(partial.items[0].kind,'template');
 const pending=model({templates:[],templatesReady:false});assert.equal(pending.items[0].kind,'template');
 assert.equal(model().items[0].journeyPhase,'application');
});
test('an assigned failed application stays selected on return; original aliases cannot count twice',()=>{
 const first=model().items[0],assigned=assignKnowledgeProblem(prefs,first,start+3600000);
 const failedRows=rows.map(item=>item.id===first.id?{...item,verdict:'WA',attempts:1}:item);
 assert.equal(model({prefs:assigned,rows:failedRows}).items[0].id,first.id);
 const alias={...rows[0],id:'alias',url:'https://codeforces.com/problemset/problem/900/A'};
 const proof=learningEvidence([...rows,alias],insights([fact('A',1),fact('alias',2)]),start+3*3600000);
 assert.equal(proof.learningRecords.length,1);
 assert.notEqual(model({rows:[...rows,{...alias,accepted:true}]}).items[0].id,'A','A passed alias cannot return as an unfamiliar application');
});
test('coached examples, read marks, XP, local checks and unverified facts never establish mastery',()=>{
 const bad=[fact('A',1,{independentKnown:false}),fact('B',2,{scope:'local'}),fact('C',27,{date:'invalid'})];
 const result=model({now:start+28*3600000,insights:{...insights(bad),growth:{level:100,totalXp:999999},knowledgeEvidence:rows.map(item=>({id:item.id,independence:1}))}});
 assert.equal(result.journey.successes.length,0);assert(!result.journey.mastered);
 const guide=LEARNING_COURSES.dsu.problems[0],guidedRow=row('guided',{url:guide.url||'https://luogu.com.cn/problem/'+guide.pid,platform:'Luogu',accepted:true});
 assert.equal(model({rows:[...rows,guidedRow],insights:insights([fact('guided',1)])}).journey.successes.length,0);
});
test('today completion moves to the last green row and the next day needs a genuinely different problem',()=>{
 const current=model({now:start+3*3600000,rows:rows.map(item=>({...item,accepted:['A','B'].includes(item.id)})),insights:insights([fact('A',1),fact('B',2)])});
 assert(current.journey.doneForToday);assert(!current.journey.mastered);assert(current.items.at(-1).completed);assert.equal(current.items.at(-1).title,'并查集');assert(current.items[0].journeyTopicId!=='dsu');
 assert(!['dsu','builtin:dsu','C','D'].includes(current.items[0].id),'The completed daily topic cannot silently return as a routine/random primary');
 const tomorrow=model({now:start+26*3600000,rows:rows.map(item=>({...item,accepted:['A','B'].includes(item.id)})),insights:insights([fact('A',1),fact('B',2)])});
 assert.equal(tomorrow.items[0].kind,'knowledge-review');assert.equal(tomorrow.items[0].id,'C');
 const retained=model({now:start+27*3600000,insights:insights([fact('A',1),fact('B',2),fact('C',26)])});
 assert(retained.journey.mastered);const saved=reconcileKnowledge(prefs,retained.journey);assert.equal(knowledgeState(saved).activeTopicId,null);assert.equal(knowledgeState(saved).journeys.dsu.status,'mastered');
 assert.equal(reconcileKnowledge(saved,retained.journey),saved);
});
test('midnight alone, repeated failures and assisted successes cannot satisfy retention',()=>{
 for(const facts of [[fact('A',1),fact('B',2),fact('C',23.5)],[fact('A',1,{failures:2}),fact('B',2,{failures:1}),fact('C',26,{failures:1})],[fact('A',1),fact('B',2),fact('C',26,{solved:false})]])assert(!model({now:start+28*3600000,insights:insights(facts)}).journey.mastered);
});
test('daily lesson pacing is idempotent and persisted separately from actual mastery',()=>{
 const base=startKnowledge({learnedLectures:[]},'basic-control',{now:start});
 const after={...base,learnedLectures:['lecture:foundation-io-basics']},once=recordKnowledgeLesson(base,after,'lecture:foundation-io-basics',start);
 const twice=recordKnowledgeLesson(once,once,'lecture:foundation-io-basics',start+1000);assert.equal(once,twice);assert.equal(Object.values(knowledgeState(once).journeys['basic-control'].checkpoints).length,1);
});
test('heart counts survive loading failure and midnight without leaking another owner',()=>{
 const values=new Map(),storage={getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)};
 saveSocialCounts('alice',{available:true,totalLikes:12,todayLikes:3},storage,'2026-11-01T15:59:00Z');
 assert.equal(readSocialCounts('alice',storage,'2026-11-01T16:01:00Z').todayLikes,0);assert.equal(readSocialCounts('bob',storage),null);
 const retained=retainSocialCounts({totalLikes:12,todayLikes:0},{available:false});assert.equal(retained.totalLikes,12);assert.equal(retained.notifications.length,0);
 assert.equal(retainSocialCounts(retained,{available:true,totalLikes:13,todayLikes:1}).totalLikes,13);
});
console.log(`PASS ${count} knowledge learning, navigation and display scenarios`);
