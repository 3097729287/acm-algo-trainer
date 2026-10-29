import {useEffect,useMemo,useState} from 'react';
import {ArrowLeft,Network,Search} from 'lucide-react';
import PageSearch from './PageSearch.jsx';
import {canonicalKnowledgeName,knowledgeAliases,indexKnowledgeRows,knowledgeFilterNames} from '@/lib/knowledgeNames.js';
import {combineKnowledgeEvidence} from '@/lib/knowledgeMastery.js';
import {radarLabels} from '@/lib/radarLabels.js';
import {radarTopicGroups} from '@/lib/radarTopicGroups.js';
import PagePagination from './PagePagination.jsx';
const EMPTY_LIST=[],EMPTY_MODEL={};
export const KNOWLEDGE_DOMAINS = [
  { name: '基础技巧', topics: [['前缀和',900],['差分',1100],['二分查找',1300],['双指针',1300],['位运算',1200],['离散化',1400],['倍增',1800]] },
  { name: '数据结构', topics: [['栈',900],['队列',900],['单调栈',1500],['单调队列',1700],['并查集',1500],['堆',1400],['树状数组',1800],['线段树',2100]] },
  { name: '图论', topics: [['拓扑排序',1700],['最短路',1900],['生成树',1900],['二分图判定',2000],['LCA',2100],['树的直径',1700],['DFS 序',1800]] },
  { name: '动态规划', topics: [['线性 DP',1500],['背包 DP',1700],['区间 DP',2000],['树形 DP',2100],['状压 DP',2100],['记忆化搜索',1600]] },
  { name: '搜索', topics: [['DFS',1300],['BFS',1300]] },
  { name: '数学与计数', topics: [['快速幂',1300],['素数',1500],['组合计数',1800],['取模与同余',1500],['最大公约数',1000],['容斥',2000]] },
  { name: '字符串', topics: [['KMP',1900],['字典树',1800],['Z 函数',1900],['Manacher',2100]] },
  { name: '思维与策略', topics: [['模拟',800],['枚举',900],['排序',900],['贪心',1400],['构造',1700],['折半枚举',2000]] },
  { name: '计算几何', topics: [['计算几何',1800],['扫描线',2100]] },
];

export function topicTags(name){return knowledgeAliases(name);}
export function estimatedDifficulty(name){if(/流|后缀|自动机|多项式|FFT|NTT|生成函数|分治优化|可持久化|可撤销|莫队|莫比乌斯|杜教|Pólya|斯特林|虚树/.test(name))return 2400;const found=KNOWLEDGE_DOMAINS.flatMap(domain=>domain.topics).filter(([topic])=>topicTags(topic).some(tag=>String(name).toLowerCase().includes(tag.toLowerCase())));if(found.length)return Math.max(...found.map(([,value])=>value));return /图|树|DP|动态规划|几何/.test(name)?2100:1600;}
export default function KnowledgeRadar({knowledge=EMPTY_LIST,knowledgeEvidence=EMPTY_LIST,knowledgeModel=EMPTY_MODEL,categories=EMPTY_LIST,rows=EMPTY_LIST,onTopic,onTrain}) {
 const [domain,setDomain]=useState(null),[query,setQuery]=useState(''),[page,setPage]=useState(1);
 const availableIndex=useMemo(()=>indexKnowledgeRows(rows),[rows]);
 const domains=useMemo(()=>{
   const leaves=node=>node.children?.length?node.children.flatMap(leaves):[node.name];
   const fallback=rows.length?new Map():new Map(knowledge.map(item=>[canonicalKnowledgeName(item.name),item.available||0]));
   const source=categories.length?categories.map(node=>({name:node.name,scope:knowledgeFilterNames(node),topics:[...new Set(leaves(node).map(canonicalKnowledgeName))].map(name=>[name,estimatedDifficulty(name)])})):KNOWLEDGE_DOMAINS;
   return source.map(node=>({...node,topics:radarTopicGroups(node.topics,availableIndex,fallback)})).filter(node=>node.topics.length);
 },[categories,availableIndex,knowledge,rows.length]);
 useEffect(()=>setPage(1),[domain?.name,query]);
 useEffect(()=>{if(!domain)return;const back=event=>{if(event.key!=='Escape'||event.defaultPrevented||document.querySelector('dialog[open],.tb-select-menu,.filter-popover,.tooltip-popover'))return;event.preventDefault();setDomain(null);setQuery('');};document.addEventListener('keydown',back);return()=>document.removeEventListener('keydown',back);},[domain]);
 const summaries=useMemo(()=>{
   const difficultyById=new Map(rows.map(row=>[row.url||row.id,row.difficulty]));
   const byName=new Map(),pool=new Map(knowledgeEvidence.map(item=>[item.id,item]));
   for(const item of knowledge){const name=canonicalKnowledgeName(item.name);if(!byName.has(name))byName.set(name,[]);byName.get(name).push(item);}
   const evidence=names=>names.flatMap(name=>byName.get(canonicalKnowledgeName(name))||[]);
   const available=names=>[...new Set(names.flatMap(name=>[...(availableIndex.get(canonicalKnowledgeName(name))||[])]))];
   const facts=(names,groups=[],scope=names)=>{const entries=evidence(scope),maximum=key=>Math.max(0,...entries.map(item=>Number(item[key])||0)),children=groups.map(group=>({name:group.name,ids:evidence(group.members).flatMap(item=>item.evidenceIds||[]),availableIds:available(group.members),difficulties:Object.fromEntries(available(group.members).map(id=>[id,difficultyById.get(id)]))}));return {...combineKnowledgeEvidence(entries.flatMap(item=>item.evidenceIds||[]),pool,knowledgeModel,children),available:rows.length?available(scope).length:maximum('available'),due:entries.some(item=>item.dueIds)?new Set(entries.flatMap(item=>item.dueIds||[])).size:maximum('due'),failures:maximum('failures'),suggested:entries.flatMap(item=>item.suggestedIds||[])[0]};};
   return domains.map(item=>({...item,...facts(item.topics.flatMap(topic=>topic.members),item.topics,item.scope||item.topics.flatMap(topic=>topic.members)),nodes:item.topics.map(topic=>({...topic,...facts(topic.members)}))}));
 },[domains,knowledge,knowledgeEvidence,knowledgeModel,availableIndex,rows.length]);
 const allNodes=domain?summaries.find(item=>item.name===domain.name)?.nodes||[]:summaries;
 const filtered=allNodes.filter(node=>[node.name,...node.members||[]].flatMap(topicTags).some(tag=>tag.toLowerCase().includes(query.trim().toLowerCase())));
 const pages=Math.max(1,Math.ceil(filtered.length/12)),currentPage=Math.min(page,pages),nodes=filtered.slice((currentPage-1)*12,currentPage*12);
 const position=(index,radius)=>{const angle=-Math.PI/2+index*Math.PI*2/nodes.length;return [340+Math.cos(angle)*radius,245+Math.sin(angle)*radius];};
 const polygon=radius=>nodes.map((_,i)=>position(i,radius).join(',')).join(' ');
 const select=node=>{if(domain)onTopic?.({name:node.name==='杂项'?`${domain.name} · 杂项`:node.name,tags:node.tags||topicTags(node.name)});else setDomain(domains.find(item=>item.name===node.name));};
 const shown=nodes;
 const valueText=node=>node.value===null?'?%':`${node.value}%`;
 const allKnown=nodes.every(node=>node.value!==null);
 const labels=radarLabels(nodes.map(node=>node.name));
 return <section className="progress-section knowledge-radar" aria-label="知识点雷达图">
 <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索知识点" value={query} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>
 <header className="progress-section-heading"><h2>{!domain&&<Network size={19}/>} {domain?.name||'知识点雷达'}</h2>{domain&&<button type="button" className="icon-button radar-back" aria-label="返回一级雷达" onClick={()=>{setDomain(null);setQuery('');}}><ArrowLeft size={18}/></button>}</header>
 <svg viewBox="0 0 680 500" role="group" aria-label={domain?`${domain.name}二级雷达`:'一级知识雷达'}>
 {[.25,.5,.75,1].map(ratio=><polygon key={ratio} className="radar-grid" points={polygon(163*ratio)}/>)}
 {labels.map(label=>{const [x,y]=label.axis;return <g key={label.name}><path className="radar-axis" d={`M340 245L${x} ${y}`}/><text x={label.x} y={label.y} textAnchor={label.side===0?'middle':label.side>0?'start':'end'} dominantBaseline="middle" data-knowledge-name={label.name}>{label.lines.map((line,i)=><tspan key={i} x={label.x} y={label.y+(i-(label.lines.length-1)/2)*18}>{line}</tspan>)}</text></g>;})}
 {allKnown&&<polygon className="radar-value" points={nodes.map((node,i)=>position(i,163*node.value/100).join(',')).join(' ')}/>}
 {!allKnown&&nodes.map((node,i)=>{const next=nodes[(i+1)%nodes.length];return node.value!==null&&next.value!==null?<path key={node.name} className="radar-value radar-partial" d={`M${position(i,163*node.value/100).join(' ')}L${position((i+1)%nodes.length,163*next.value/100).join(' ')}`}/>:null;})}
 {nodes.map((node,i)=>{const [x,y]=position(i,163),[mx,my]=position(i,163*(node.value??0)/100);return <g key={node.name}>{node.value!==null&&<circle className="radar-data-dot" cx={mx} cy={my} r={3}/>}<circle className="radar-node" data-unknown={node.value===null} cx={x} cy={y} r={8} tabIndex={0} role="button" aria-label={`${node.name}，掌握 ${valueText(node)}，${domain?'筛选题目':'进入二级雷达'}`} onClick={()=>select(node)} onKeyDown={event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();select(node);}}}><title>{node.reason}</title></circle></g>;})}
 </svg>
 <div className="radar-knowledge-details" role="region" tabIndex={0} aria-label="雷达知识掌握与缺口"><div className="radar-detail-heading"><span>知识点</span><span>掌握指数</span><span>作答 / 可用</span><span>AC</span><span>待练</span></div>{shown.map(node=><div className="radar-detail-row" key={node.name}><button type="button" title={node.name==='杂项'?node.members.join('、'):undefined} onClick={()=>select(node)}>{node.name}{domain&&node.difficulty!=null&&<small>{node.difficulty}</small>}</button><span className="mastery-estimate" title={node.reason}><b data-unknown={node.value===null}>{valueText(node)}</b>{node.interval&&<small aria-label={node.intervalKind==='coverage'?'含未练部分的参考范围':'95%模型区间'}>{node.interval[0]}–{node.interval[1]}</small>}</span><span>{node.participated} / {node.available}</span><span>{node.officialAccepted}</span><span>{node.suggested&&onTrain?<button type="button" onClick={()=>onTrain(node.suggested)}>{node.due||'练习'}</button>:node.due}</span></div>)}</div>
 {pages>1&&<PagePagination label="知识点分页" count={`${filtered.length} 个知识点`} page={currentPage} pages={pages} onPageChange={setPage} onPrevious={()=>setPage(currentPage-1)} onNext={()=>setPage(currentPage+1)}/>}
 </section>;
}
