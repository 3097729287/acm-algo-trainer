import {organizeTrainingLists} from './trainingListCatalog.js';
import {buildTrainingCurriculum,filterTrainingListsScope} from './trainingCurriculum.js';

// Actual shipped lab IDs, prerequisites are observed solved-topic counts.
export const LAB_ACTIONS=[
 {id:'sorting-basics',title:'排序基础',tags:['排序'],requires:[],first:'order'},
 {id:'prefix-difference',title:'前缀和与差分',tags:['前缀和','差分'],requires:['数组'],first:'sum'},
 {id:'two-pointers',title:'双指针算法',tags:['双指针','滑动窗口'],requires:['数组','排序'],first:'pair'},
 {id:'divide-sort',title:'分治与随机化',tags:['分治','排序'],requires:['排序'],first:'split'},
 {id:'bucket-sort',title:'桶与按位处理',tags:['排序','桶排序'],requires:['排序'],first:'keys'},
 {id:'bfs',title:'BFS 广度优先搜索',tags:['BFS'],requires:['模拟','数组'],first:'0'},
 {id:'dfs',title:'DFS 深度优先搜索',tags:['DFS'],requires:['递归'],first:'0'},
 {id:'dsu',title:'并查集',tags:['并查集'],requires:['数组'],first:'0'},
 {id:'dijkstra',title:'Dijkstra 最短路',tags:['最短路'],requires:['BFS','图论'],first:'0'},
 {id:'knapsack',title:'背包 DP',tags:['背包','动态规划'],requires:['数组','递推'],first:'pack'},
];
const finite=value=>typeof value==='number'&&Number.isFinite(value);
const ready=row=>row?.catalogContentReady===true&&!row.locked;
const tags=row=>Array.isArray(row?.tags)?row.tags:[];
const compare=(a,b)=>(a.difficulty??9999)-(b.difficulty??9999)||String(a.id).localeCompare(String(b.id));
export function nextActions({rows=[],training=[],insights={},prefs={},lists=[],templates=[],availablePages=[],activeContest=null}={}) {
 const allowed=id=>availablePages.includes(id),byId=new Map();
 for(const row of rows)for(const id of [row.id,...row.aliasIds||[]])byId.set(id,row);
 const solved=new Set(rows.filter(row=>row.accepted).map(row=>row.id));
 const answer=[];
 if(activeContest){if(allowed('mock'))answer.push({kind:'contest',page:'mock',id:activeContest.id,title:activeContest.name,reason:'已有正在进行的模拟赛，先继续当前试卷，避免同时开启新的训练。'});return answer;}
 const due=training.filter(row=>['review','check'].includes(row.queue)&&!row.locked).sort((a,b)=>String(a.reviewDueAt||a.dueAt||'').localeCompare(String(b.reviewDueAt||b.dueAt||''))||compare(a,b));
 if(due.length)answer.push({kind:'review',page:'mine',id:due[0].id,title:due[0].title,reason:`有 ${due.length} 道已到期的复习，先独立重写这道题，检验上次练习是否留下了可复用的方法。`});
 const counts=new Map();for(const row of rows.filter(row=>row.accepted))for(const tag of new Set(tags(row)))counts.set(tag,(counts.get(tag)||0)+1);
 const weak=new Map((insights.knowledge||[]).filter(item=>item.evidenceCount>0&&finite(item.mastery)).map(item=>[item.name,{value:item.mastery,count:item.evidenceCount}]));
 const rank=insights.growth?.ranked||{},independent=rank.recentPerformance?.independentSolved??rank.evidenceCount??0;
 const sourceLists=filterTrainingListsScope(organizeTrainingLists(lists.filter(list=>!list.custom&&list.available!==false)),rows);
 if(allowed('training-lists')){
  const units=buildTrainingCurriculum(sourceLists,rows).filter(list=>list.problems?.length>=3&&list.topicPath?.[0]?.startsWith('01'));
  const unit=units.map(list=>({list,remaining:list.problems.map(item=>byId.get(item.problemId)).filter(row=>row&&!row.accepted&&ready(row)&&finite(row.difficulty)&&row.difficulty<=1300)})).find(item=>item.remaining.length);
  if(unit)answer.push({kind:'list',page:'training-lists',id:unit.list.id,title:unit.list.displayTitle||unit.list.title,reason:`编程基础题单中仍有 ${unit.remaining.length} 道未通过、题面与样例完整的基础题，先补齐这段学习路线。`});
 }
 const eligible=rows.filter(row=>ready(row)&&!row.catalogHidden&&!row.accepted&&finite(row.difficulty)&&row.difficulty>=800&&row.difficulty<=2300);
 const level=finite(insights.assessment?.recommendationLevel)?insights.assessment.recommendationLevel:null;
 if(!answer.some(item=>item.kind==='list')){
  const target=eligible.filter(row=>row.difficulty<=Math.min(1300,level??1100)).sort(compare)[0];
  if(target)answer.push({kind:'problem',page:'mine',id:target.id,title:target.title,reason:level?`这道 ${target.difficulty} 分题位于当前 ${level} 分参考训练带内，尚未通过，题面和样例已完整。`:`独立定级证据尚不足；这道 ${target.difficulty} 分基础题题面和样例完整，适合先积累可验证的作答。`});
 }
 if(allowed('paths')){
  const courses=LAB_ACTIONS.filter(course=>course.requires.every(tag=>(counts.get(tag)||0)>0));
  const started=courses.find(course=>prefs.learningPaths?.activePath===course.id)||courses.find(course=>prefs.learningPaths?.[course.id]);
  const observed=courses.map(course=>({course,weak:course.tags.map(tag=>weak.get(tag)).filter(Boolean).sort((a,b)=>a.value-b.value)[0]})).filter(item=>item.weak).sort((a,b)=>a.weak.value-b.weak.value)[0];
  const course=started||observed?.course||courses[0];
  if(course){const evidence=observed?.course===course?observed.weak:null;answer.push({kind:'course',page:'paths',id:course.id,title:course.title,first:course.first,reason:started?`上次已开始这门课，继续保存的学习位置；${course.requires.length?'已有前置知识题目的正式通过记录。':'本课从基础排序操作开始。'}`:evidence?`${course.tags.join(' / ')} 已有 ${evidence.count} 道作答证据，当前掌握指数 ${evidence.value}%；可先用这门互动课补齐方法。`:course.requires.length?`已有 ${course.requires.join('、')} 相关题目的正式通过记录，满足这门课的前置要求。`:'这门课不要求进阶算法基础，先通过具体数组操作理解排序，再进入跟做题。'});}
 }
 if(allowed('templates')){
  const matching=templates.filter(item=>item.builtin&&(item.tags||[]).some(tag=>counts.has(tag))&&item.practiceIds?.some(id=>ready(byId.get(id))&&!byId.get(id).accepted));
  const template=matching.find(item=>(item.tags||[]).some(tag=>weak.has(tag)))||matching.find(item=>(item.tags||[]).some(tag=>counts.has(tag)));
  if(template){answer.push({kind:'template',page:'templates',id:template.id,title:template.title,reason:`已有 ${((template.tags||[]).filter(tag=>counts.has(tag))).join('、')||'相关知识点'} 的作答记录，可对照模板的适用条件与实现；配套练习题已在本机核对可用。`});const task=template.practiceIds.map(id=>byId.get(id)).find(row=>ready(row)&&!row.accepted);if(task)answer.push({kind:'template-problem',page:'templates',id:task.id,title:task.title,reason:`这是「${template.title}」明确关联的模板练习，尚未通过；用完整评测验证实现，避免只复制代码。`});}
 }
 const performance=rank.recentPerformance;
 if(allowed('library')&&independent>=5&&finite(level)&&performance?.attempted>=5&&performance.firstPass/performance.attempted>=.5){
  const stretch=eligible.filter(row=>row.difficulty>level&&row.difficulty<=Math.min(2300,level+200)&&['HIGH','MEDIUM'].includes(row.difficultyConfidence)&&tags(row).some(tag=>counts.has(tag))).sort(compare)[0];
  if(stretch)answer.push({kind:'stretch',page:'library',id:stretch.id,title:stretch.title,reason:`近期 ${performance.attempted} 道有效作答中 ${performance.firstPass} 道一遍通过；这道 ${stretch.difficulty} 分题比 ${level} 分参考训练带高一档，且包含已练过的知识点。`});
 }
 return answer;
}
