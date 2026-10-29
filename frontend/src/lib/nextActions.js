import {organizeTrainingLists} from './trainingListCatalog.js';
import {buildTrainingCurriculum,filterTrainingListsScope} from './trainingCurriculum.js';
import {canonicalKnowledgeName,rowKnowledgeNames} from './knowledgeNames.js';

// Real shipped lessons, with explicit prerequisites and template associations.
// A broad shared tag never implies that an unrelated advanced template is next.
export const LAB_ACTIONS=[
 {id:'sorting-basics',title:'排序基础',tags:['排序'],requires:['数组'],first:'order'},
 {id:'prefix-difference',title:'前缀和与差分',tags:['前缀和','差分'],requires:['数组'],first:'sum',template:'builtin:prefix-difference'},
 {id:'two-pointers',title:'双指针算法',tags:['双指针','滑动窗口'],requires:['数组','排序'],first:'pair'},
 {id:'divide-sort',title:'分治与随机化',tags:['分治'],requires:['排序'],first:'split'},
 {id:'bucket-sort',title:'桶与按位处理',tags:['桶排序'],requires:['排序'],first:'keys'},
 {id:'bfs',title:'BFS 广度优先搜索',tags:['BFS'],requires:['模拟','数组'],first:'0',template:'builtin:bfs'},
 {id:'dfs',title:'DFS 深度优先搜索',tags:['DFS'],requires:['递归'],first:'0'},
 {id:'dsu',title:'并查集',tags:['并查集'],requires:['数组'],first:'0',template:'builtin:dsu'},
 {id:'dijkstra',title:'Dijkstra 最短路',tags:['最短路'],requires:['BFS','堆'],first:'0',template:'builtin:dijkstra'},
 {id:'knapsack',title:'背包 DP',tags:['背包 DP'],requires:['数组','递推'],first:'pack',template:'builtin:knapsack'},
];
export const NEXT_ACTION_POLICY=Object.freeze({maxActions:6,recentDays:90,topicSuccesses:3,prerequisiteSuccesses:2,minimumSpanHours:24,
 minimumDays:2,minimumWeight:.75,maximumFailureRatio:1/3,minimumFirstPassRatio:.5});
const TEMPLATE_REQUIRES={
 'builtin:dsu':['数组'],'builtin:dijkstra':['BFS','堆'],'builtin:kruskal':['并查集','排序'],
 'builtin:bfs':['模拟','数组'],'builtin:zero-one-bfs':['BFS'],'builtin:bellman-ford':['BFS'],
 'builtin:topological':['BFS'],'builtin:scc':['DFS'],'builtin:lca':['DFS'],
 'builtin:fenwick':['前缀和'],'builtin:segment-tree':['前缀和','递归'],'builtin:sparse-table':['数组'],
 'builtin:compression':['排序','二分查找'],'builtin:prefix-difference':['数组'],
 'builtin:window-extrema':['双指针'],'builtin:binary-search':['排序'],
 'builtin:kmp':['字符串'],'builtin:z-function':['字符串'],'builtin:trie':['字符串'],
 'builtin:mod-combination':['数论'],'builtin:linear-sieve':['数论'],'builtin:extended-gcd':['数论'],
 'builtin:knapsack':['数组','递推'],'builtin:lis':['数组','二分查找'],
};
const BASICS=['数组','模拟','枚举','字符串','输入输出','顺序结构','分支','循环','函数'];
const finite=value=>typeof value==='number'&&Number.isFinite(value);
const list=value=>Array.isArray(value)?value:[];
const ready=row=>row?.catalogContentReady===true&&!row.locked;
// The catalog sets solutionAvailable from actual bundled solution records;
// statement readiness alone never promises an explanation is available.
const explained=row=>row?.solutionAvailable===true&&row.solutionState!=='missing';
const names=row=>rowKnowledgeNames(row);
const matches=(row,wanted)=>wanted.some(name=>names(row).has(canonicalKnowledgeName(name)));
const compare=(a,b)=>a.difficulty-b.difficulty||String(a.id).localeCompare(String(b.id));
const stamp=value=>typeof value==='string'?Date.parse(value):NaN;
const day=value=>new Date(value+8*3600000).toISOString().slice(0,10);
const dueDate=row=>row.reviewTask?.due||row.reviewDueAt||row.dueAt;
const isDue=(value,now)=>{
 if(!value)return true; // The server already selected queue=review/check.
 if(/^\d{4}-\d{2}-\d{2}$/.test(value))return finite(stamp(value))&&new Date(stamp(value)).toISOString().startsWith(value)&&value<=day(now);
 return finite(stamp(value))&&stamp(value)<=now;
};
const broad=new Set(['基础算法','数据结构','图论','数学','数学与计数','动态规划','搜索','思维与策略','专题方法','进阶技巧','杂项','综合练习']);
const requiredTopics=row=>[...new Set([...list(row.tags),...list(row.knowledgeCategories).map(path=>path.split(/\s*\/\s*/).at(-1))].map(canonicalKnowledgeName))].filter(tag=>tag&&!broad.has(tag));
const topicMatches=(row,wanted)=>!row.knowledgeReviewRequired&&requiredTopics(row).some(tag=>wanted.map(canonicalKnowledgeName).includes(tag));
function verifiedPaper(paper){
 const expected=paper.map(row=>row.contestProblemCount).filter(value=>Number.isInteger(value)&&value>0);
 if(paper.length<3||!expected.length||new Set(expected).size!==1||expected[0]!==paper.length)return false;
 if(paper.some(row=>row.contestRoster!==true||!row.contestId||!row.platform))return false;
 if(new Set(paper.map(row=>String(row.contestId))).size!==1||new Set(paper.map(row=>row.contestVariant||'')).size!==1
  ||new Set(paper.map(row=>row.source||'')).size!==1)return false;
 const letters=paper.map(row=>String(row.contestLetter||row.problem||'').toUpperCase());
 if(letters.some(letter=>!letter)||new Set(letters).size!==paper.length)return false;
 // The schema supplies a roster flag/count, not an arbitrary expected ID array.
 // Reject missing/repeated indices and unfamiliar numbering rather than guess.
 if(letters.every(letter=>/^[A-Z](?:[1-9]\d*)?$/.test(letter))){
  const bases=[...new Set(letters.map(letter=>letter[0]))].sort();
  if(bases.some((letter,index)=>letter!==String.fromCharCode(65+index)))return false;
  for(const base of bases){
   const parts=letters.filter(letter=>letter[0]===base);
   if(parts.length>1||parts[0].length>1){
    if(parts.some(part=>part.length===1))return false;
    const numbers=parts.map(part=>Number(part.slice(1))).sort((a,b)=>a-b);
    if(numbers.some((number,index)=>number!==index+1))return false;
   }
  }
  return true;
 }
 return letters.every(letter=>/^[1-9]\d*$/.test(letter))&&letters.map(Number).sort((a,b)=>a-b).every((value,index)=>value===index+1);
}

function original(row){
 try{
  const url=new URL(row.url),host=url.hostname.toLowerCase().replace(/^www\./,''),path=url.pathname.replace(/\/+$/,'');
  if(!['http:','https:'].includes(url.protocol))return row.id;
  if(/^(?:m[12]\.)?codeforces\.com$/.test(host)){
   const found=path.match(/^\/(?:contest\/(\d+)\/problem|problemset\/problem\/(\d+))\/([A-Za-z0-9]+)$/);
   if(found)return `codeforces.com/contest/${found[1]||found[2]}/problem/${found[3].toUpperCase()}`;
  }
  if(host==='qoj.ac'){
   const found=path.match(/^\/(?:contest\/\d+\/)?problem\/(\d+)(?:\/statement\/(?:default|zh_cn))?$/);
   if(found)return 'qoj.ac/problem/'+found[1];
  }
  return host+(host==='atcoder.jp'?path.toLowerCase():path);
 }catch{return row.id;}
}
export function trustedDifficulty(row){
 if(!finite(row?.difficulty)||row.difficulty<=0||row.difficultyHidden)return false;
 const source=String(row.difficultySource||'');
 if(!source||/未知|待核|未提供|无官方|unknown/i.test(source))return false;
 return /官方|official/i.test(source)&&/^codeforces$/i.test(row.platform||'')&&row.difficultyEstimated!==true
  ||['HIGH','MEDIUM'].includes(row.difficultyConfidence);
}
function statistics(items){
 const solved=items.filter(item=>item.solved),days=new Set(solved.map(item=>day(item.time)));
 const weight=solved.reduce((sum,item)=>sum+item.weight,0),firstPass=solved.filter(item=>item.failures===0).length;
 const spanHours=solved.length?(Math.max(...solved.map(item=>item.time))-Math.min(...solved.map(item=>item.time)))/3600000:0;
 const failureRatio=items.length?(items.length-solved.length)/items.length:0;
 return {attempted:items.length,solved:solved.length,days:days.size,spanHours,weight,firstPass,failureRatio,
  stable:solved.length>=NEXT_ACTION_POLICY.topicSuccesses&&days.size>=NEXT_ACTION_POLICY.minimumDays
   &&spanHours>=NEXT_ACTION_POLICY.minimumSpanHours&&weight>=NEXT_ACTION_POLICY.minimumWeight&&failureRatio<=NEXT_ACTION_POLICY.maximumFailureRatio
   &&firstPass/solved.length>=NEXT_ACTION_POLICY.minimumFirstPassRatio,
  prerequisite:solved.length>=NEXT_ACTION_POLICY.prerequisiteSuccesses&&days.size>=NEXT_ACTION_POLICY.minimumDays
   &&spanHours>=NEXT_ACTION_POLICY.minimumSpanHours&&weight>=NEXT_ACTION_POLICY.minimumWeight&&failureRatio<=NEXT_ACTION_POLICY.maximumFailureRatio};
}
export function learningEvidence(rows,insights={},now=Date.now()){
 const byId=new Map();
 for(const row of rows)for(const id of [row.id,original(row),...list(row.aliasIds)])byId.set(id,row);
 // Only this versioned assessment comes from strict backend.from_records:
 // completed official receipts, known independence/source, one episode per
 // original. AC counts, saved chapters, local samples and XP cannot replace it.
 const assessment=[insights.assessment,insights.growth?.ranked].find(value=>value?.model?.method==='rasch-practice-evidence-v2');
 const unique=new Map();
 for(const item of list(assessment?.evidence)){
  const row=byId.get(item.problemId)||byId.get(item.id),time=stamp(item.date);
  if(!row||!trustedDifficulty(row)||!finite(time)||time>now||now-time>NEXT_ACTION_POLICY.recentDays*86400000
   ||typeof item.solved!=='boolean'||!finite(item.weight)||item.weight<=0||item.weight>1
   ||!finite(item.difficulty)||item.difficulty<=0||item.independentKnown===false||item.independent===false
   ||item.scope&&item.scope!=='official')continue;
  const key=original(row),candidate={...item,row,time,key,failures:Number.isInteger(item.failures)&&item.failures>=0?item.failures:1};
  const prior=unique.get(key);
  if(!prior||candidate.time<prior.time||candidate.time===prior.time&&!candidate.solved)unique.set(key,candidate);
 }
 const evidence=[...unique.values()],cache=new Map();
 const forTopics=wanted=>{
  const key=wanted.map(canonicalKnowledgeName).sort().join('\0');
  if(!cache.has(key))cache.set(key,statistics(evidence.filter(item=>topicMatches(item.row,wanted))));
  return cache.get(key);
 };
 return {byId,evidence,all:statistics(evidence),forTopics,forIds:ids=>{
  const keys=new Set(ids.map(id=>byId.get(id)).filter(row=>row&&!row.knowledgeReviewRequired&&requiredTopics(row).length).map(original));return statistics(evidence.filter(item=>keys.has(item.key)));
 }};
}
function implementationPosition(course,saved){
 // A saved position authorizes a diagnostic exercise, never a mastery claim.
 return saved?.mode==='guided'||['code','debug','transfer','practice','test','apply','summary'].includes(saved?.labV1?.chapter)
  ||['bfs','dfs','dsu','dijkstra'].includes(course.id)&&['5','6'].includes(saved?.labV1?.chapter);
}
const proof=stats=>`近 90 天 ${stats.attempted} 道不同原题中独立通过 ${stats.solved} 道，分布在 ${stats.days} 天`;

export function nextActions({rows=[],training=[],insights={},prefs={},lists=[],templates=[],availablePages=[],activeContest=null,reviewPlan={},now=Date.now()}={}){
 now=now instanceof Date?now.getTime():now;if(!finite(now))return [];
 const allowed=id=>availablePages.includes(id),answer=[],used=new Set();
 if(activeContest)return allowed('mock')?[{kind:'contest',page:'mock',id:activeContest.id,title:activeContest.name,
  reason:'已有正在进行的模拟赛，先继续当前试卷，避免同时开启新的训练。'}]:[];
 const {byId,...evidence}=learningEvidence(rows,insights,now);
 const push=item=>{
  if(!item||!allowed(item.page)||answer.length>=NEXT_ACTION_POLICY.maxActions)return false;
  const key=['course','template','list'].includes(item.kind)?item.kind+':'+item.id:original(byId.get(item.id)||item);
  if(!used.has(key)){used.add(key);answer.push(item);return true;}return false;
 };
 const offerProblems=(tasks,reason,maximum=3)=>{
  let added=0;
  for(const task of tasks){
   if(push({kind:'problem',page:'mine',id:task.id,title:task.title,reason:typeof reason==='function'?reason(task):reason}))added++;
   if(added>=maximum||answer.length>=NEXT_ACTION_POLICY.maxActions)break;
  }
  return added;
 };
 const accepted=new Set([...rows,...training].filter(row=>row.accepted).map(row=>original(byId.get(row.id)||row)));
 const candidates=rows.filter(row=>ready(row)&&explained(row)&&!row.catalogHidden&&!accepted.has(original(row))&&trustedDifficulty(row)&&row.difficulty<=2300).sort(compare);
 const due=training.filter(row=>['review','check'].includes(row.queue)&&ready({...byId.get(row.id),...row})
  &&isDue(dueDate(row),now)).sort((a,b)=>Number(Boolean(b.reviewTask?.openedAt))-Number(Boolean(a.reviewTask?.openedAt))
   ||(stamp(dueDate(a))||0)-(stamp(dueDate(b))||0)||String(a.id).localeCompare(String(b.id)));
 if(due.length)push({kind:'review',page:'mine',id:due[0].id,title:due[0].title||byId.get(due[0].id)?.title,
  reason:`训练队列已有 ${due.length} 道到期复习；先独立重写检验隔日保留。到期是复习安排，不等于已经掌握，也不重复计算首次学习结论。`});
 if(reviewPlan?.reviewOnly===true||finite(reviewPlan?.newMinutes)&&reviewPlan.newMinutes<15)return answer;
 const sourceLists=filterTrainingListsScope(organizeTrainingLists(lists.filter(item=>!item.custom&&!String(item.id).startsWith('custom:')&&item.available!==false)),rows);
 const units=buildTrainingCurriculum(sourceLists,rows).filter(unit=>unit.topicPath?.[0]?.startsWith('01'));
 const foundational=evidence.forTopics(BASICS);
 const assessment=insights.assessment?.model?.method==='rasch-practice-evidence-v2'?insights.assessment:insights.growth?.ranked;
 const supportedBasics=['数组','模拟','枚举','字符串','排序','前缀和','递归','二分查找'].filter(tag=>evidence.forTopics([tag]).prerequisite);
 // Representative independent work can demonstrate basic programming across
 // source lists. Never demand clearing every spare introductory question.
 const equivalentBasics=assessment?.qualified===true&&evidence.all.solved>=5&&evidence.all.stable&&supportedBasics.length>=2;
 const unitTopics={0:['输入输出','顺序结构'],1:['分支','循环','枚举'],2:['数组','字符串'],3:['函数','结构体','STL']};
 const foundationTopics=new Set([...BASICS,'结构体','STL','排序']);
 const frontier=units.slice().sort((a,b)=>a.curriculumOrder-b.curriculumOrder).map(unit=>({unit,stats:evidence.forIds(unit.problems.map(item=>item.problemId)),
  remaining:unit.problems.map(item=>byId.get(item.problemId)).filter(row=>candidates.includes(row)&&row.difficulty<=1400&&!row.knowledgeReviewRequired
   &&requiredTopics(row).every(tag=>foundationTopics.has(tag)||evidence.forTopics([tag]).prerequisite))}))
  .find(item=>!equivalentBasics&&!item.stats.stable&&!evidence.forTopics(unitTopics[item.unit.curriculumOrder]||[]).stable);
 if(frontier){
  const {unit,stats,remaining}=frontier;
  // An absent or unavailable prerequisite is a content gap, not completion.
  // Never invent a curriculum ID or send a beginner to a later available unit.
  const missingEarlier=Array.from({length:unit.curriculumOrder},(_,order)=>order).some(order=>
   !units.some(candidate=>candidate.curriculumOrder===order)&&!evidence.forTopics(unitTopics[order]||[]).stable);
  if(missingEarlier)return answer;
  const gap=stats.solved<3?'还需补充独立成功':stats.spanHours<24?'还缺隔日验证':stats.weight<.75?'可信难度证据仍少':'还需减少重试并巩固';
  const availability=remaining.length?`还有 ${remaining.length} 道未通过且题面、样例和内置题解完整的已定级题；卡住时先用题内一级帮助。`
   :'本单元暂没有同时具备完整题面、样例、内置题解和可信难度的未通过练习；先查看当前单元，补齐内容前不跳到后续单元。';
  const reason=`先补「${unit.displayTitle||unit.title}」：${proof(stats)}，${gap}。${availability}`;
  if(allowed('training-lists'))push({kind:'list',page:'training-lists',id:unit.id,title:unit.displayTitle||unit.title,reason});
  offerProblems(remaining,task=>`${reason}这道 ${task.difficulty} 分题来自同一当前基础单元，可直接练习；这些备选不要求同时完成。`);
  return answer;
 }
 if(!foundational.stable&&!equivalentBasics){
  // Until source-list metadata arrives, only explicitly supported first-step
  // language tasks are safe. A broad "basic" tag cannot authorize arrays,
  // functions or STL for a learner without the earlier programming evidence.
  const firstTopics=['输入输出','顺序结构'];
  offerProblems(candidates.filter(row=>row.difficulty<=1100&&topicMatches(row,firstTopics)
   &&requiredTopics(row).every(tag=>firstTopics.includes(tag)||evidence.forTopics([tag]).prerequisite)),
   task=>`${proof(foundational)}，近期独立证据还不足；先用这道 ${task.difficulty} 分完整基础题诊断并巩固。卡住时先用题内一级帮助。`);
  return answer;
 }
 const prerequisite=tag=>evidence.forTopics([tag]).prerequisite;
 const canStudy=(row,wanted)=>{
  const target=new Set(wanted.map(canonicalKnowledgeName));
  return !row.knowledgeReviewRequired&&requiredTopics(row).every(tag=>target.has(tag)||prerequisite(tag));
 };
 const missing=course=>course.requires.filter(tag=>!prerequisite(tag));
 const templateById=new Map(templates.filter(item=>item.builtin).map(item=>[item.id,item]));
 const courseCandidates=LAB_ACTIONS.filter(course=>!evidence.forTopics(course.tags).stable
  &&(prefs.learningPaths?.[course.id]||candidates.some(row=>matches(row,course.tags))));
 let course=courseCandidates.find(item=>prefs.learningPaths?.activePath===item.id)||courseCandidates.find(item=>prefs.learningPaths?.[item.id])||courseCandidates.find(item=>!missing(item).length),prerequisiteContext='';
 if(course&&missing(course).length){
  const tag=missing(course)[0],replacement=LAB_ACTIONS.find(item=>item!==course&&item.tags.includes(tag)&&!missing(item).length);
  if(replacement){prerequisiteContext=`先补「${course.title}」需要的 ${tag}；`;course=replacement;}
  else{
   const tasks=candidates.filter(row=>matches(row,[tag])&&row.difficulty<=1300&&canStudy(row,[tag]));
   if(tasks.length){offerProblems(tasks,task=>`「${course.title}」还缺 ${tag} 的前置独立证据：${proof(evidence.forTopics([tag]))}；先用这道 ${task.difficulty} 分完整题验证基础，再进入该课程。`);return answer;}
   course=courseCandidates.find(item=>!missing(item).length);
   if(!course)return answer;
  }
 }
 const level=assessment?.qualified&&finite(assessment.abilityScore)?assessment.abilityScore:null;
 const ceiling=Math.min(2300,Math.max(1300,(level??1100)+100));
 const independent=(wanted,context)=>{
  return offerProblems(candidates.filter(row=>matches(row,wanted)&&row.difficulty<=ceiling&&canStudy(row,wanted)),
   task=>`${context}；${proof(evidence.forTopics(wanted))}。用这道尚未通过、题面与样例完整的 ${task.difficulty} 分官方题，独立实现并检查边界。`)>0;
 };
 const templateTask=(template,context,afterLesson=false)=>{
  if(!template||!allowed('templates'))return false;
  const ids=list(template.practiceIds),passed=list(template.practicePassed),pending=ids.map((id,index)=>({row:byId.get(id),passed:passed[index]===true})).filter(item=>!item.passed&&ready(item.row)&&!accepted.has(original(item.row)));
  if(!pending.length)return false;
  if(afterLesson||passed.some(value=>value===true)){
   let added=0;
   for(const {row} of pending){
    if(push({kind:'template-problem',page:'templates',id:row.id,title:row.title,
     reason:`${context}；「${template.title}」还有 ${pending.length} 道未完成的配套操作题。先检验实现，再用独立官方题巩固。`}))added++;
    if(added>=3||answer.length>=NEXT_ACTION_POLICY.maxActions)break;
   }
  }else push({kind:'template',page:'templates',id:template.id,title:template.title,
    reason:`${context}；当前没有这份模板的操作通过记录，先学习适用条件与实现，再做配套操作题。`});
  return true;
 };
 const offerCourse=item=>{
  const saved=prefs.learningPaths?.[item.id],stats=evidence.forTopics(item.tags);
  const prerequisites=item.requires.map(tag=>`${tag} ${evidence.forTopics([tag]).solved} 道`).join('、');
  return push({kind:'course',page:'paths',id:item.id,title:item.title,first:item.first,
   reason:`${item===course?prerequisiteContext:''}前置已有跨日独立证据（${prerequisites}）；${proof(stats)}。先${saved?'按保存章节继续学习':'学习这门互动课'}，随后用实际练习检验理解。`});
 };
 const offerReadyAlternatives=()=>{
  // Alternatives remain at the learner's current qualified frontier. A saved
  // chapter, XP or opening a template cannot waive a missing prerequisite.
  let added=0;
  for(const item of courseCandidates){
   if(item===course||missing(item).length||implementationPosition(item,prefs.learningPaths?.[item.id])
    ||!candidates.some(row=>matches(row,item.tags)&&row.difficulty<=ceiling&&canStudy(row,item.tags)))continue;
   if(offerCourse(item))added++;
   if(added>=2||answer.length>=NEXT_ACTION_POLICY.maxActions)break;
  }
  for(const item of templates){
   if(answer.length>=NEXT_ACTION_POLICY.maxActions)break;
   if(!item.builtin||!TEMPLATE_REQUIRES[item.id]||!TEMPLATE_REQUIRES[item.id].every(prerequisite)
    ||evidence.forTopics(list(item.tags)).stable)continue;
   const linked=LAB_ACTIONS.find(lesson=>lesson.template===item.id);
   if(linked&&!implementationPosition(linked,prefs.learningPaths?.[linked.id]))continue;
   templateTask(item,'已有对应前置的跨日独立题证据；可选择这一实现练习巩固当前基础',Boolean(linked));
  }
 };
 if(course){
  const saved=prefs.learningPaths?.[course.id];
  if(!implementationPosition(course,saved)){
   if(allowed('paths'))offerCourse(course);
   else independent(course.tags,'算法实验室当前未显示，先在可见入口做有题面与难度依据的独立诊断');
  }else if(!templateTask(templateById.get(course.template),'课程已保存到实现或跟做位置，这只是练习起点',true)){
   independent(course.tags,'已到实现或跟做位置，优先用真实题目独立巩固');
  }
  offerReadyAlternatives();
  return answer;
 }
 // The other templates have teaching text, but no assumed interactive course.
 const template=templates.find(item=>item.builtin&&TEMPLATE_REQUIRES[item.id]
  &&TEMPLATE_REQUIRES[item.id].every(prerequisite)&&!evidence.forTopics(list(item.tags)).stable
  &&list(item.practiceIds).some((id,index)=>item.practicePassed?.[index]!==true&&ready(byId.get(id))));
 if(template&&templateTask(template,'已有对应前置的跨日独立题证据；本算法暂不假定存在单独互动课程'))return answer;
 const implemented=templates.find(item=>item.builtin&&TEMPLATE_REQUIRES[item.id]
  &&TEMPLATE_REQUIRES[item.id].every(prerequisite)&&!evidence.forTopics(list(item.tags)).stable
  &&list(item.practiceIds).length&&item.practiceIds.every((id,index)=>item.practicePassed?.[index]===true)
  &&candidates.some(row=>matches(row,list(item.tags))&&row.difficulty<=ceiling&&canStudy(row,list(item.tags))));
 if(implemented&&independent(list(implemented.tags),`「${implemented.title}」的配套操作题已通过，下一步用官方题验证实现与应用`))return answer;
 const weakness=candidates.find(row=>[...names(row)].some(tag=>evidence.forTopics([tag]).attempted&&!evidence.forTopics([tag]).stable)&&row.difficulty<=ceiling);
 if(weakness){
  const topic=[...names(weakness)].find(tag=>evidence.forTopics([tag]).attempted&&!evidence.forTopics([tag]).stable);
  if(independent([topic],'已有尝试的专题尚未稳定，先补巩固'))return answer;
 }
 const stats=evidence.all;
 if(allowed('mock')&&finite(level)&&stats.solved>=8&&stats.stable){
  const supported=new Set(evidence.evidence.filter(item=>item.solved&&!item.row.knowledgeReviewRequired)
   .flatMap(item=>requiredTopics(item.row).filter(tag=>evidence.forTopics([tag]).stable)));
  if(supported.size>=3){
   const groups=new Map();
   for(const row of rows){
    if(!row.contest||row.catalogHidden)continue;
    const key=String(row.platform||'')+'\0'+row.contest;
    if(!groups.has(key))groups.set(key,new Map());groups.get(key).set(original(row),row);
   }
   const papers=[...groups.values()].map(group=>[...group.values()]).filter(paper=>{
    if(!verifiedPaper(paper))return false;
    const topics=new Set(paper.flatMap(requiredTopics));
    if(topics.size<3||[...topics].some(tag=>!supported.has(tag)))return false;
    return paper.every(row=>ready(row)&&trustedDifficulty(row)&&!row.knowledgeReviewRequired&&requiredTopics(row).length
     &&!accepted.has(original(row))&&row.difficulty<=Math.min(2300,level+100)
     &&!matches(row,['交互题','通信题','提交答案题'])&&!/interactive|communication|output.?only|交互|通信|提交答案/i.test(row.problemKind||''))
     &&Math.max(...paper.map(row=>row.difficulty))>=level-200
     &&paper.reduce((sum,row)=>sum+row.difficulty,0)/paper.length>=level-400;
   }).sort((a,b)=>Math.abs(a.reduce((sum,row)=>sum+row.difficulty,0)/a.length-level)
    -Math.abs(b.reduce((sum,row)=>sum+row.difficulty,0)/b.length-level)||String(a[0].contest).localeCompare(String(b[0].contest)));
   if(papers.length){
    const paper=papers[0];push({kind:'mixed',page:'mock',id:paper[0].contest,contest:paper[0].contest,title:'混合限时训练',
     reason:`${proof(stats)}，已有多个技术的跨日独立证据。「${paper[0].contest}」共 ${paper.length} 道未做的完整题，难度在当前训练带内；去模拟赛选择这份试卷，练习限时独立识别与取舍。`});
    return answer;
   }
  }
 }
 if(allowed('library')&&finite(level)&&stats.solved>=5&&stats.stable){
  const task=candidates.find(row=>row.difficulty>level&&row.difficulty<=Math.min(2300,level+200)
   &&!row.knowledgeReviewRequired&&requiredTopics(row).length&&requiredTopics(row).every(tag=>evidence.forTopics([tag]).stable));
  if(task)push({kind:'stretch',page:'library',id:task.id,title:task.title,
   reason:`${proof(stats)}；题目涉及的具体技术均有独立作答支持。选这道 ${task.difficulty} 分完整题，在 ${level} 分保守训练参考上提高一档。`});
 }
 return answer;
}
