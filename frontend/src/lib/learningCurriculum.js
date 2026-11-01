import SOURCE from '../../../backend/resources/learning-curriculum.json' with {type:'json'};
import {canonicalKnowledgeName} from './knowledgeNames.js';

export const KNOWLEDGE_TOPICS=SOURCE.topics;
export const KNOWLEDGE_BY_ID=Object.fromEntries(KNOWLEDGE_TOPICS.map(topic=>[topic.id,topic]));
export const FOUNDATION_LESSONS=SOURCE.lessons;
export const FOUNDATION_BY_ID=Object.fromEntries(FOUNDATION_LESSONS.map(item=>[item.id,item]));
export const LEARNING_COURSES=SOURCE.courses;
export const LECTURE_ROLES={language:'语言与工具',algorithm:'通用算法',application:'题目中的应用',topic:'专题阅读'};
const levelNames={1:'入门',2:'进阶',3:'深入'};
const lesson=id=>'lecture:foundation-'+id;
const topicLessons=new Map(KNOWLEDGE_TOPICS.flatMap(topic=>topic.tags.map(tag=>[canonicalKnowledgeName(tag),topic.lectures[0]])));
for(const [tag,id] of Object.entries({'数论':'number-theory','整数':'integer','位运算':'bitwise','组合计数':'counting','计数':'counting','概率与期望':'probability','取模与同余':'modular','线性 DP':'dp','树形 DP':'trees','计算几何':'geometry','贪心':'greedy','构造':'construction','单调栈':'monotonic','单调队列':'monotonic','哈希':'hashing','堆':'heap','拓扑排序':'topology','生成树':'topology','DFS 序':'trees'}))topicLessons.set(canonicalKnowledgeName(tag),lesson(id));
const deep=/可撤销|回滚并查集|线段树分治|可持久化|莫比乌斯|生成函数|FFT|NTT|网络流|自动机|多项式|虚树|线性基|斯特林|Li\s*Chao|李超/i;
const special=[
 [/可撤销|回滚并查集|线段树分治/,[lesson('dsu'),lesson('segment-tree'),lesson('recursion')]],
 [/可持久化/,[lesson('segment-tree'),lesson('recursion')]],
 [/FFT|NTT|生成函数|多项式/,[lesson('counting'),lesson('modular')]],
 [/虚树/,[lesson('trees'),lesson('binary-lifting')]],
 [/自动机/,[lesson('strings'),lesson('trie')]],
 [/斯特林/,[lesson('counting'),lesson('dp')]],
];
export function lectureCurriculum(lecture={}){
 const reviewed=FOUNDATION_BY_ID[lecture.id];
 if(reviewed)return {...reviewed,levelLabel:levelNames[reviewed.level],roleLabel:LECTURE_ROLES[reviewed.kind],reviewed:true};
 const text=[lecture.concept,lecture.title,...(lecture.tags||[])].join(' '),primary=String(lecture.concept||'').split('：')[0];
 const known=[primary,...(lecture.tags||[])].map(canonicalKnowledgeName).map(tag=>topicLessons.get(tag)).filter(Boolean);
 const rule=special.find(([pattern])=>pattern.test(text));
 const prerequisites=[...new Set(rule?.[1]||known)].filter(id=>id!==lecture.id);
 const level=deep.test(text)?3:known.length?Math.max(...known.map(id=>FOUNDATION_BY_ID[id]?.level||2)):null;
 const kind=lecture.sourceProblemIds?.length||lecture.sourceProblem||lecture.sourceContest?'application':'topic';
 return {id:lecture.id,kind,level,levelLabel:levelNames[level]||'未分级',roleLabel:LECTURE_ROLES[kind],prerequisites,order:9999,reviewed:Boolean(rule||known.length)};
}
export function orderedLectures(entries){
 const roles=['language','algorithm','application','topic'];
 return entries.map((item,index)=>({...item,curriculum:lectureCurriculum(item),listIndex:index})).sort((a,b)=>
  roles.indexOf(a.curriculum.kind)-roles.indexOf(b.curriculum.kind)
  ||(a.curriculum.level??4)-(b.curriculum.level??4)||a.curriculum.order-b.curriculum.order
  ||String(a.displayTitle||a.concept||a.title).localeCompare(String(b.displayTitle||b.concept||b.title),'zh-CN'));
}
export function foundationNext(preferences={}){
 const learned=new Set(preferences.learnedLectures||[]);
 const next=FOUNDATION_LESSONS.find(item=>item.kind==='language'&&item.level===1&&!learned.has(item.id)&&item.prerequisites.every(id=>learned.has(id)));
 return next||FOUNDATION_LESSONS.find(item=>item.kind==='language'&&item.level===1&&!learned.has(item.id))||FOUNDATION_LESSONS[0];
}
export function prerequisiteTitle(id){return (FOUNDATION_BY_ID[id]?.title||id).replace(/^从零讲[：:]\s*/,'').split('：')[0];}
