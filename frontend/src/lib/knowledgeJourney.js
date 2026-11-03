import {KNOWLEDGE_TOPICS,KNOWLEDGE_BY_ID,FOUNDATION_BY_ID,LEARNING_COURSES,prerequisiteTitle} from './learningCurriculum.js';
import {rowKnowledgeNames,canonicalKnowledgeName} from './knowledgeNames.js';
import {original} from './problemIdentity.js';
import {trainingDay} from './trainingDate.js';

export const KNOWLEDGE_POLICY=Object.freeze({version:1,dailyTasks:2,independentProblems:2,masteryProblems:3,minimumRetentionHours:24,maximumRecentEvidence:5});
const array=value=>Array.isArray(value)?value:[];
const finite=value=>typeof value==='number'&&Number.isFinite(value);
const stamp=value=>typeof value==='string'?Date.parse(value):NaN;
const iso=now=>new Date(now).toISOString();
export const knowledgeState=prefs=>prefs?.learningPaths?.knowledgeLearning?.version===1?prefs.learningPaths.knowledgeLearning:{version:1,activeTopicId:null,selection:0,journeys:{}};
// These originals were reviewed as introductory exercises. Their general OJ
// tags (or a missing editorial) must not erase the connection to the lesson.
const curated=(row,topic)=>array(topic.practiceOriginals).includes(original(row));
const reviewedPracticeOriginals=new Set(KNOWLEDGE_TOPICS.flatMap(topic=>array(topic.practiceOriginals)));
export const isReviewedKnowledgePractice=row=>reviewedPracticeOriginals.has(original(row));
const topicMatches=(row,topic)=>curated(row,topic)||topic.tags.some(tag=>rowKnowledgeNames(row).has(canonicalKnowledgeName(tag)));
const usable=row=>row?.catalogContentReady===true&&row.solutionAvailable===true&&row.solutionState!=='missing'&&!row.locked&&!row.catalogHidden;
const practiceReady=(row,topic)=>(usable(row)||curated(row,topic)&&row?.catalogStatementReady===true)&&!row.locked&&!row.catalogHidden;
const practiceRank=(row,topic)=>curated(row,topic)?array(topic.practiceOriginals).indexOf(original(row))/100:studyRank(row);
const implemented=template=>array(template?.practicePassed).length>0&&array(template.practicePassed).every(Boolean);
const basicTopic=topic=>topic?.level===1&&!topic.course&&!topic.template&&topic.lectures.length>0&&topic.lectures.every(id=>FOUNDATION_BY_ID[id]?.kind==='language');
const distinct=rows=>[...new Map(rows.map(row=>[original(row),row])).values()];
const fresh=row=>!row.accepted&&!row.hasDraft&&!row.draft&&!row.lastSubmissionAt&&!row.lastSubmission&&!Number(row.attempts||row.attemptCount||row.submissionCount||0)&&!/(?:\b(?:AC|WA|TLE|MLE|RE|CE|OLE)\b|已通过|未通过|训练中)/i.test(String(row.status||'')+' '+String(row.verdict||''));
function studyRank(row){
 if(row.difficultyHidden)return null;
 if(finite(row.difficulty)&&row.difficulty>0&&!/未知|待核|未提供|无官方|unknown/i.test(row.difficultySource||'')&&(/官方|official/i.test(row.difficultySource||'')&&/^codeforces$/i.test(row.platform||'')&&row.difficultyEstimated!==true||['HIGH','MEDIUM'].includes(row.difficultyConfidence)))return row.difficulty;
 const native=['入门','普及-'].indexOf(String(row.nativeDifficultyLabel||row.nativeDifficulty?.label||'').replaceAll('−','-'));
 if(/^(洛谷|luogu)$/i.test(row.platform||'')&&native>=0)return native/10; // Native introductory order only; no invented CF score.
 return null;
}
const pidKey=problem=>{
 if(problem.url)return original({id:problem.pid,url:problem.url});
 const cf=String(problem.pid||'').match(/^(\d+)([A-Z]\d?)$/);
 return cf?`codeforces.com/contest/${cf[1]}/problem/${cf[2]}`:/^P\d+$/.test(problem.pid||'')?'luogu.com.cn/problem/'+problem.pid:problem.pid;
};
function edited(prefs,change){
 const state=knowledgeState(prefs),next=change(state);
 return next===state?prefs:{...prefs,learningPaths:{...prefs.learningPaths,knowledgeLearning:next}};
}
function exposureFor(prefs,rows,evidence){
 const names=new Set(),learned=new Set(prefs.learnedLectures||[]);
 for(const row of rows)if(row.accepted)for(const tag of rowKnowledgeNames(row))names.add(tag);
 const exposed=new Set(KNOWLEDGE_TOPICS.filter(topic=>topic.lectures.every(id=>learned.has(id))||topic.tags.some(tag=>names.has(canonicalKnowledgeName(tag)))||evidence?.forTopics(topic.tags).solved>0).map(topic=>topic.id));
 return topic=>exposed.has(topic.id);
}
export function requiredKnowledgeLessons(topic,prefs={},rows=[],evidence,exposure=exposureFor(prefs,rows,evidence)){
 const result=[],seen=new Set(),learned=new Set(prefs.learnedLectures||[]);
 for(const known of KNOWLEDGE_TOPICS)if(exposure(known))for(const id of known.lectures)learned.add(id);
 const addLesson=id=>{if(seen.has(id)||learned.has(id))return;seen.add(id);for(const parent of FOUNDATION_BY_ID[id]?.prerequisites||[])addLesson(parent);result.push(id);};
 const visit=id=>{const parent=KNOWLEDGE_BY_ID[id];if(!parent||exposure(parent))return;for(const prerequisite of parent.prerequisites)visit(prerequisite);for(const id of parent.lectures)addLesson(id);};
 for(const id of topic.prerequisites)visit(id);
 for(const id of topic.lectures)for(const parent of FOUNDATION_BY_ID[id]?.prerequisites||[])addLesson(parent);
 return result;
}
export function startKnowledge(prefs,topicId,{rows=[],templates=[],now=Date.now()}={}){
 const topic=KNOWLEDGE_BY_ID[topicId];if(!topic)return prefs;
 return edited(prefs,state=>{
  const previous=state.journeys?.[topicId],template=templates.find(item=>item.id===topic.template);
  const guideKeys=new Set(array(LEARNING_COURSES[topic.course]?.problems).map(pidKey));
  const current=previous?{...previous,status:'active'}:{topicId,id:globalThis.crypto?.randomUUID?.()||`${topicId}:${now}`,startedAt:iso(now),status:'active',checkpoints:{},assignments:{},initialLearned:array(prefs.learnedLectures),initialTemplate:template?implemented(template):null,initialCourse:prefs.learningPaths?.[topic.course]?.mode==='guided',initialAccepted:rows.filter(row=>row.accepted&&(topicMatches(row,topic)||guideKeys.has(original(row)))).map(original)};
  const journeys={...state.journeys};
  if(state.activeTopicId&&state.activeTopicId!==topicId&&journeys[state.activeTopicId])journeys[state.activeTopicId]={...journeys[state.activeTopicId],status:'paused'};
  journeys[topicId]=current;return {...state,activeTopicId:topicId,journeys};
 });
}
export const cancelKnowledge=prefs=>edited(prefs,state=>!state.activeTopicId?state:{...state,activeTopicId:null,journeys:{...state.journeys,[state.activeTopicId]:{...state.journeys[state.activeTopicId],status:'paused'}}});
export const rotateKnowledge=prefs=>edited(prefs,state=>({...state,selection:(Number.isSafeInteger(state.selection)?state.selection:0)+1}));
export function recordKnowledgeCheckpoint(prefs,key,minutes,now=Date.now()){
 return edited(prefs,state=>{
  const journey=state.journeys?.[state.activeTopicId];if(!journey||journey.status!=='active'||journey.checkpoints?.[key])return state;
  return {...state,journeys:{...state.journeys,[state.activeTopicId]:{...journey,checkpoints:{...journey.checkpoints,[key]:{at:iso(now),minutes}}}}};
 });
}
export function recordKnowledgeNavigation(previous,next,now=Date.now()){
 const state=knowledgeState(previous),topic=KNOWLEDGE_BY_ID[state.activeTopicId],course=topic?.course;
 if(!course||previous.learningPaths?.activePath!==course)return next;
 const before=previous.learningPaths?.[course],after=next.learningPaths?.[course];
 if(before?.mode==='guided'||!after)return next;
 const chapter=String(before?.labV1?.chapter??LEARNING_COURSES[course]?.first??'0');
 return after.mode==='guided'||after.labV1?.chapter!=null&&String(after.labV1.chapter)!==chapter?recordKnowledgeCheckpoint(next,`lab:${course}:${chapter}`,4,now):next;
}
export function recordKnowledgeLesson(previous,next,id,now=Date.now()){
 const state=knowledgeState(previous),topic=KNOWLEDGE_BY_ID[state.activeTopicId];
 if(!topic||!array(next.learnedLectures).includes(id)||array(previous.learnedLectures).includes(id))return next;
 const related=new Set([...topic.lectures,...requiredKnowledgeLessons(topic,previous)]);
 return related.has(id)?recordKnowledgeCheckpoint(next,'lecture:'+id,6,now):next;
}
export function confirmKnowledgeAction(prefs,action,now=Date.now()){
 const state=knowledgeState(prefs),topic=KNOWLEDGE_BY_ID[state.activeTopicId];
 if(!topic||action?.journeyTopicId!==topic.id||action.reviewOnly)return prefs;
 if(action.kind==='lecture'){
  if(array(prefs.learnedLectures).includes(action.id))return prefs;
  const lessons=new Set([...topic.lectures,...requiredKnowledgeLessons(topic,prefs)]);
  if(!lessons.has(action.id))return prefs;
  return recordKnowledgeLesson(prefs,{...prefs,learnedLectures:[...new Set([...array(prefs.learnedLectures),action.id])]},action.id,now);
 }
 if(action.kind==='course'&&action.id===topic.course)return recordKnowledgeCheckpoint(prefs,'course:'+action.id,6,now);
 return prefs;
}
export function assignKnowledgeProblem(prefs,item,now=Date.now()){
 if(!item.journeyTopicId||!item.journeyPhase)return prefs;
 return edited(prefs,state=>{
  const journey=state.journeys?.[item.journeyTopicId];if(state.activeTopicId!==item.journeyTopicId||!journey)return state;
  if(!['problem','guided','knowledge-review'].includes(item.kind))return state;
  const key=item.journeyPhase;return {...state,journeys:{...state.journeys,[item.journeyTopicId]:{...journey,assignments:{...journey.assignments,[key]:{id:item.id,at:iso(now)}}}}};
 });
}
export function reconcileKnowledge(prefs,context){
 if(!context?.journey)return prefs;
 const next=edited(prefs,state=>{
  const id=context.topic.id,current=state.journeys?.[id];if(!current||current.id!==context.journey.id||state.activeTopicId!==id)return state;
  const additions=context.events.filter(event=>!current.checkpoints?.[event.key]);
  if(!additions.length&&!context.mastered&&!context.learningComplete)return state;
  const checkpoints={...current.checkpoints};for(const event of additions)checkpoints[event.key]={at:event.at,minutes:event.minutes};
  return {...state,activeTopicId:context.mastered||context.learningComplete?null:id,journeys:{...state.journeys,[id]:{...current,checkpoints,...(context.mastered?{status:'mastered',masteredAt:context.masteredAt,masteryProblemIds:context.successes.map(item=>item.key)}:context.learningComplete?{status:'completed',completedAt:iso(context.now)}:{})}}};
 });
 if(next===prefs||!context.learningComplete||!context.continuation)return next;
 const {topicId,rows,templates,now}=context.continuation;
 const continued=startKnowledge(next,topicId,{rows,templates,now});
 return edited(continued,state=>({...state,journeys:{...state.journeys,[topicId]:{...state.journeys[topicId],continuedFrom:context.journey.id}}}));
}
export function knowledgeCandidates({rows=[],prefs={},evidence,now=Date.now(),exposure=exposureFor(prefs,rows,evidence)}={}){
 const learned=KNOWLEDGE_TOPICS.filter(exposure);
 const tier=learned.some(topic=>topic.level>=2)?3:learned.length?2:1;
 const state=knowledgeState(prefs);
 return KNOWLEDGE_TOPICS.filter(topic=>topic.level<=tier&&!['mastered','completed'].includes(state.journeys?.[topic.id]?.status)&&!evidence?.forTopics(topic.tags).stable)
  .sort((a,b)=>requiredKnowledgeLessons(a,prefs,rows,evidence,exposure).length-requiredKnowledgeLessons(b,prefs,rows,evidence,exposure).length||a.level-b.level||a.order-b.order);
}
export function knowledgeJourney({rows=[],prefs={},templates=[],templatesReady=true,availablePages=[],reviewPlan={},evidence,now=Date.now()}={}){
 const state=knowledgeState(prefs),topic=KNOWLEDGE_BY_ID[state.activeTopicId],journey=state.journeys?.[state.activeTopicId];
 const exposure=exposureFor(prefs,rows,evidence),options=knowledgeCandidates({rows,prefs,evidence,now,exposure}),alternatives=options.filter(item=>item.id!==topic?.id);
 const selected=alternatives[(Number.isSafeInteger(state.selection)?state.selection:0)%Math.max(1,alternatives.length)];
 const suggestion=selected?{kind:'knowledge',id:selected.id,page:'lectures',title:selected.title,topic:selected,reason:`按学习难度与先修推荐「${selected.title}」；先补需要的概念，再用应用与跨日独立练习检验掌握。`,refreshable:alternatives.length>1}:null;
 if(!topic||!journey||journey.status!=='active'){
  const last=Object.values(state.journeys||{}).filter(item=>item.status==='mastered'&&trainingDay(item.masteredAt)===trainingDay(now)).sort((a,b)=>stamp(b.masteredAt)-stamp(a.masteredAt))[0],learned=last&&KNOWLEDGE_BY_ID[last.topicId];
  return {suggestion,options:alternatives,completed:learned?{kind:'knowledge',id:learned.id,page:'lectures',title:learned.title,topic:learned,completed:true,mastered:true,reason:'已有不同原题的独立通过及跨日陌生题检验。'}:null};
 }
 const allowed=id=>availablePages.includes(id),course=LEARNING_COURSES[topic.course],template=templates.find(item=>item.id===topic.template),start=stamp(journey.startedAt),day=trainingDay(now);
 const acceptedOriginals=new Set(rows.filter(row=>row.accepted).map(original)),attemptedOriginals=new Set(rows.filter(row=>!fresh(row)).map(original));
 const unseen=row=>fresh(row)&&!attemptedOriginals.has(original(row));
 const guidedKeys=new Set(array(course?.problems).map(pidKey));
 const relevant=array(evidence?.learningRecords||evidence?.evidence).filter(item=>item.time>=start&&topicMatches(item.row,topic)&&!guidedKeys.has(item.key));
 const successes=relevant.filter(item=>item.solved).sort((a,b)=>a.time-b.time),recent=relevant.slice().sort((a,b)=>a.time-b.time).slice(-KNOWLEDGE_POLICY.maximumRecentEvidence);
 const uniqueDays=new Set(successes.map(item=>trainingDay(item.time))),first=successes[0]?.time;
 const mastered=successes.length>=KNOWLEDGE_POLICY.masteryProblems&&uniqueDays.size>=2&&successes.at(-1).time-first>=KNOWLEDGE_POLICY.minimumRetentionHours*3600000
  &&recent.filter(item=>item.solved).length>=3&&recent.at(-1)?.solved===true&&successes.filter(item=>item.failures===0).length>=2;
 const checkpoints=journey.checkpoints||{},events=successes.map(item=>({key:'official:'+item.key,at:iso(item.time),minutes:12}));
 if(implemented(template)&&journey.initialTemplate===false)events.push({key:'template:'+topic.template,at:iso(now),minutes:6});
 const guided=distinct(rows.filter(row=>guidedKeys.has(original(row))&&usable(row)));
 const guidePassed=guided.filter(row=>acceptedOriginals.has(original(row))).length;
 for(const row of guided)if(row.accepted&&!array(journey.initialAccepted).includes(original(row)))events.push({key:'guided:'+original(row),at:iso(now),minutes:12});
 // Daily pacing belongs to the learning route, including earlier foundations.
 // Reusing an old AC advances a basic lesson but creates no new task receipt.
 const todayPoints={};for(const saved of Object.values(state.journeys||{}))for(const [key,value] of Object.entries(saved.checkpoints||{}))if(!todayPoints[key])todayPoints[key]=value;
 for(const event of events)if(!todayPoints[event.key])todayPoints[event.key]=event;
 const spent=Object.values(todayPoints).filter(item=>trainingDay(item.at)===day).reduce((sum,item)=>sum+(Number(item.minutes)||0),0);
 const budget=Math.max(8,Math.min(topic.level===1?20:25,finite(reviewPlan.newMinutes)?reviewPlan.newMinutes:topic.level===1?15:20));
 const cap=Math.min(2300,Math.max(1100,Number(evidence?.assessment?.abilityScore)||1100)+100);
 const independent=distinct(rows.filter(row=>practiceReady(row,topic)&&topicMatches(row,topic)&&(curated(row,topic)||!row.knowledgeReviewRequired)&&practiceRank(row,topic)!=null&&practiceRank(row,topic)<=cap&&!guidedKeys.has(original(row)))).sort((a,b)=>practiceRank(a,topic)-practiceRank(b,topic)||String(a.id).localeCompare(String(b.id)));
 const pick=(phase,candidates)=>{
  const assigned=journey.assignments?.[phase],retained=assigned&&candidates.find(row=>row.id===assigned.id&&practiceReady(row,topic)&&!acceptedOriginals.has(original(row)));
  return retained||candidates.find(unseen);
 };
 const coverage={lectures:topic.lectures.length,experiment:Boolean(course),guided:guided.length,implementation:Boolean(template),independent:independent.filter(unseen).length,retention:'跨日陌生题独立检验'};
 const learningComplete=basicTopic(topic)&&topic.lectures.every(id=>array(prefs.learnedLectures).includes(id))&&(!array(topic.practiceOriginals).length||rows.some(row=>curated(row,topic)&&row.accepted));
 const nextBasic=learningComplete&&KNOWLEDGE_TOPICS.filter(item=>basicTopic(item)&&item.id!==topic.id&&!['mastered','completed'].includes(state.journeys?.[item.id]?.status)&&item.lectures.some(id=>!array(prefs.learnedLectures).includes(id))).sort((a,b)=>a.order-b.order)[0];
 const continuation=nextBasic?{topicId:nextBasic.id,rows,templates,now}:null;
 let action=null,phase='learn',waiting=false;
 const prerequisite=requiredKnowledgeLessons(topic,prefs,rows,evidence,exposure)[0];
 const offerLecture=(id,reason)=>({kind:'lecture',page:'lectures',id,title:prerequisiteTitle(id),reason});
 if(prerequisite)action=offerLecture(prerequisite,`学习「${topic.title}」先补 ${prerequisiteTitle(prerequisite)}；已读只是先修安排，不代表掌握。`);
 else if(course&&prefs.learningPaths?.[topic.course]?.mode!=='guided'&&!journey.initialCourse&&!checkpoints['course:'+topic.course]&&!successes.length){
  action={kind:'course',page:'paths',id:topic.course,title:topic.title,first:course.first,resume:true,reason:`继续「${topic.title}」的课堂与实验，保留章节、草稿和检查记录。`};
 }else if(!course&&topic.lectures.some(id=>!array(prefs.learnedLectures).includes(id))&&!successes.length){
  const id=topic.lectures.find(id=>!array(prefs.learnedLectures).includes(id));action=offerLecture(id,`先读「${topic.title}」的概念与例子，再独立应用。`);
 }else if(guided.length&&guidePassed<Math.min(2,guided.length)&&!successes.length){
  phase='guided';const row=pick(phase,guided.filter(row=>studyRank(row)!=null&&studyRank(row)<=cap));
  if(row)action={kind:'guided',page:'paths',id:topic.course,problemId:row.id,guidedIndex:course.problems.findIndex(item=>pidKey(item)===original(row)),title:row.title,resume:true,reason:`「${topic.title}」的配套例题；先使用已有指导理解条件和变化，跟做通过与独立掌握分别记录。`};
 }else if(topic.template&&!templatesReady&&!successes.length){
  phase='implementation';action={kind:'template',page:'templates',id:topic.template,title:topic.title,reason:`继续「${topic.title}」的实现练习；模板进度正在读取，保留当前步骤。`};
 }else if(template&&!implemented(template)&&!successes.length){
  phase='implementation';action={kind:'template',page:'templates',id:template.id,title:template.title,reason:`练习「${topic.title}」的实现与边界；已有操作练习通过后继续陌生题。`};
 }
 if(!action){
  phase=successes.length>=KNOWLEDGE_POLICY.independentProblems?'retention':'application';
  waiting=phase==='retention'&&(!first||now-first<KNOWLEDGE_POLICY.minimumRetentionHours*3600000||trainingDay(first)===day);
  const row=!waiting&&pick(phase,independent);
  if(row)action={kind:phase==='retention'?'knowledge-review':'problem',page:'mine',id:row.id,title:row.title,reason:phase==='retention'?`与初次应用间隔至少一天，用一道未做过的「${topic.title}」题独立检验保留与迁移；查看题解后的 AC 不算独立检验。`:`用这道未做过的「${topic.title}」题独立实现；原题别名不会重复计入。`};
  else if(!waiting&&!mastered)action={...offerLecture(topic.lectures[0],`「${topic.title}」当前没有满足难度和内容条件的陌生练习，先回顾要点；练习覆盖仍待补齐，不标记掌握。`),reviewOnly:true};
 }
 if(action&&!allowed(action.page))action={kind:'navigation',page:'settings',id:'learning-visibility',title:'恢复学习入口',reason:`「${topic.title}」所需入口已隐藏，可在设置中恢复。`};
 const dailyCompleted=Object.entries(todayPoints).filter(([key,item])=>/^(lecture|course|template|guided|official):/.test(key)&&trainingDay(item.at)===day).length;
 if(action)action={...action,journeyTopicId:topic.id,journeyPhase:phase,reason:`${action.reason} 今日默认 ${KNOWLEDGE_POLICY.dailyTasks} 项，已完成 ${dailyCompleted} 项；可以分多天完成。`};
 const doneForToday=mastered||waiting||dailyCompleted>=KNOWLEDGE_POLICY.dailyTasks;
 const completed=doneForToday?{kind:'knowledge',id:topic.id,page:'lectures',title:topic.title,topic,completed:true,mastered,rawAction:action,reason:mastered?'已有多道不同原题的独立通过及跨日陌生题检验。':waiting?`今天的「${topic.title}」安排已完成；到下一次间隔检验前，可选择其它练习。`:`今天的「${topic.title}」学习量已完成，进度保留；可以继续其他练习。`}:null;
 return {topic,journey,suggestion:mastered?suggestion:null,options:mastered?alternatives:[],rawAction:action,action:doneForToday?null:action,completed,events,successes,mastered,masteredAt:mastered?iso(successes.at(-1).time):null,learningComplete,continuation,now,phase,doneForToday,budget,spent,dailyTarget:KNOWLEDGE_POLICY.dailyTasks,dailyCompleted,coverage};
}

export function optionalLearningActions({rows=[],prefs={},availablePages=[],evidence,now=Date.now(),deferTopic=null}={}){
 const allowed=page=>availablePages.includes(page),cap=Math.min(2300,Math.max(1100,Number(evidence?.assessment?.abilityScore)||1100)+100);
 const attempted=new Set(rows.filter(row=>!fresh(row)).map(original));
 const supported=new Set(['输入输出','顺序结构']);
 for(const topic of KNOWLEDGE_TOPICS)if(topic.lectures.every(id=>array(prefs.learnedLectures).includes(id))||evidence?.forTopics(topic.tags).prerequisite)for(const tag of topic.tags)supported.add(canonicalKnowledgeName(tag));
 const broad=new Set(['基础算法','数据结构','图论','数学','数学与计数','动态规划','搜索','思维与策略','专题方法','进阶技巧','杂项','综合练习']);
 const candidates=distinct(rows.filter(row=>{
  const tags=[...rowKnowledgeNames(row)].filter(tag=>!broad.has(tag));
  return usable(row)&&fresh(row)&&!attempted.has(original(row))&&!row.knowledgeReviewRequired&&studyRank(row)!=null&&studyRank(row)<=cap&&tags.length&&tags.every(tag=>supported.has(tag))&&(!deferTopic||!topicMatches(row,deferTopic));
 }));
 const choices=[];
 if(candidates.length){const seed=[...trainingDay(now)].reduce((sum,char)=>sum+char.charCodeAt(0),0),row=candidates[seed%candidates.length];choices.push({kind:'random',page:allowed('library')?'library':'mine',id:row.id,title:row.title,reason:'当前安排之外，可选一道内容完整、难度在练习范围内的随机题。'});}
 const topic=deferTopic?null:KNOWLEDGE_BY_ID[knowledgeState(prefs).activeTopicId];
 if(allowed('mock'))choices.push({kind:'specialized',page:'mock',id:'topic-training',title:topic?topic.title+'专项训练':'专项训练',tags:topic?.tags||[],reason:'选择当前要巩固的知识点，核对难度与题数后开始一场专项训练。'}, {kind:'replay',page:'mock',id:'contest-replay',title:'重现赛',reason:'选择一份已有完整题目的比赛，按自己的时间练习识别与取舍。'});
 return choices;
}

export function knowledgeCoverage(topic,rows=[],templates=[]){
 if(!topic)return null;
 const course=LEARNING_COURSES[topic.course],keys=new Set(array(course?.problems).map(pidKey));
 const attempted=new Set(rows.filter(row=>!fresh(row)).map(original));
 return {lectures:topic.lectures.filter(id=>FOUNDATION_BY_ID[id]).length,experiment:Boolean(course),guided:distinct(rows.filter(row=>keys.has(original(row))&&usable(row))).length,
  implementation:topic.template?templates.some(item=>item.id===topic.template):null,independent:distinct(rows.filter(row=>usable(row)&&fresh(row)&&!attempted.has(original(row))&&topicMatches(row,topic)&&!row.knowledgeReviewRequired&&studyRank(row)!=null&&!keys.has(original(row)))).length};
}
