import {useEffect,useMemo,useState} from 'react';
import {ArrowLeft,Network,Search} from 'lucide-react';
import PageSearch from './PageSearch.jsx';
import FilterMenu from './FilterMenu.jsx';
import {canonicalKnowledgeName,knowledgeAliases,matchesKnowledge} from '@/lib/knowledgeNames.js';
import {combineKnowledgeEvidence} from '@/lib/knowledgeMastery.js';
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
export default function KnowledgeRadar({knowledge=[],knowledgeEvidence=[],knowledgeModel={},categories=[],rows=[],onTopic,onTrain}) {
 const [domain,setDomain]=useState(null),[query,setQuery]=useState(''),[gaps,setGaps]=useState(false);
 const domains=useMemo(()=>{
   const leaves=node=>node.children?.length?node.children.flatMap(leaves):[node.name];
   return categories.length?categories.map(node=>({name:node.name,topics:[...new Set(leaves(node))].map(name=>[canonicalKnowledgeName(name),estimatedDifficulty(name)]).filter(([,difficulty])=>difficulty<2200)})).filter(node=>node.topics.length):KNOWLEDGE_DOMAINS.map(node=>({...node,topics:node.topics.map(([name,difficulty])=>[canonicalKnowledgeName(name),difficulty])}));
 },[categories]);
 useEffect(()=>{if(!domain)return;const back=event=>{if(event.key!=='Escape'||event.defaultPrevented||document.querySelector('dialog[open],.tb-select-menu,.filter-popover,.tooltip-popover'))return;event.preventDefault();setDomain(null);setQuery('');};document.addEventListener('keydown',back);return()=>document.removeEventListener('keydown',back);},[domain]);
 const evidence=names=>{const tags=new Set(names.map(canonicalKnowledgeName));return knowledge.filter(item=>tags.has(canonicalKnowledgeName(item.name)));};
 const facts=(names,parent=false)=>{const entries=evidence(names),maximum=key=>Math.max(0,...entries.map(item=>Number(item[key])||0)),pool=new Map(knowledgeEvidence.map(item=>[item.id,item])),children=parent?names.map(name=>({name,ids:evidence([name]).flatMap(item=>item.evidenceIds||[])})):[];return {...combineKnowledgeEvidence(entries.flatMap(item=>item.evidenceIds||[]),pool,knowledgeModel,children),available:rows.length?new Set(rows.filter(row=>matchesKnowledge(row,names)).map(row=>row.url||row.id)).size:maximum('available'),due:entries.some(item=>item.dueIds)?new Set(entries.flatMap(item=>item.dueIds||[])).size:maximum('due'),failures:maximum('failures'),suggested:entries.flatMap(item=>item.suggestedIds||[])[0]};};
 const nodes=useMemo(()=>domain?domain.topics.map(([name,difficulty])=>({name,difficulty,...facts([name])})):domains.map(item=>({...item,...facts(item.topics.map(([name])=>name),true)})),[domain,domains,knowledge,knowledgeEvidence,knowledgeModel,rows]);
 const position=(index,radius)=>{const angle=-Math.PI/2+index*Math.PI*2/nodes.length;return [340+Math.cos(angle)*radius,245+Math.sin(angle)*radius];};
 const polygon=radius=>nodes.map((_,i)=>position(i,radius).join(',')).join(' ');
 const select=node=>{if(domain)onTopic?.({name:node.name,tags:topicTags(node.name)});else setDomain(domains.find(item=>item.name===node.name));};
 const shown=nodes.filter(node=>(!gaps||node.due>0||node.failures>0||node.value===null||node.value<50)&&topicTags(node.name).some(tag=>tag.toLowerCase().includes(query.trim().toLowerCase())));
 const valueText=node=>node.value===null?'?%':`${node.value}%`;
 const allKnown=nodes.every(node=>node.value!==null);
 return <section className="progress-section knowledge-radar" aria-label="知识点雷达图">
 <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索知识点" value={query} onChange={event=>setQuery(event.target.value)}/></label><FilterMenu label="雷达筛选" active={gaps}><label className="filter-field"><span>只看待加强</span><input type="checkbox" checked={gaps} onChange={event=>setGaps(event.target.checked)}/></label></FilterMenu></PageSearch>
 <header className="progress-section-heading"><h2>{domain?<button className="icon-button" aria-label="返回一级雷达" onClick={()=>{setDomain(null);setQuery('');}}><ArrowLeft size={18}/></button>:<Network size={19}/>} {domain?.name||'知识点雷达'}</h2></header>
 <svg viewBox="0 0 680 500" role="group" aria-label={domain?`${domain.name}二级雷达`:'一级知识雷达'}>
 {[.25,.5,.75,1].map(ratio=><polygon key={ratio} className="radar-grid" points={polygon(163*ratio)}/>)}
 {nodes.map((node,i)=>{const [x,y]=position(i,163),dx=(x-340)/163,dy=(y-245)/163,horizontal=Math.abs(dx)>.25;return <g key={node.name}><path className="radar-axis" d={`M340 245L${x} ${y}`}/><text x={x+(horizontal?Math.sign(dx)*20:0)} y={y+(horizontal?dy*16:Math.sign(dy)*30)} textAnchor={horizontal?(dx>0?'start':'end'):'middle'} dominantBaseline="middle" data-knowledge-name={node.name}>{node.name}</text></g>;})}
 {allKnown&&<polygon className="radar-value" points={nodes.map((node,i)=>position(i,163*node.value/100).join(',')).join(' ')}/>}
 {!allKnown&&nodes.map((node,i)=>{const next=nodes[(i+1)%nodes.length];return node.value!==null&&next.value!==null?<path key={node.name} className="radar-value radar-partial" d={`M${position(i,163*node.value/100).join(' ')}L${position((i+1)%nodes.length,163*next.value/100).join(' ')}`}/>:null;})}
 {nodes.map((node,i)=>{const [x,y]=position(i,163),[mx,my]=position(i,163*(node.value??0)/100);return <g key={node.name}>{node.value!==null&&<circle className="radar-data-dot" cx={mx} cy={my} r={3}/>}<circle className="radar-node" data-unknown={node.value===null} cx={x} cy={y} r={8} tabIndex={0} role="button" aria-label={`${node.name}，掌握 ${valueText(node)}，${domain?'筛选题目':'进入二级雷达'}`} onClick={()=>select(node)} onKeyDown={event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();select(node);}}}><title>{node.reason}</title></circle></g>;})}
 </svg>
 <div className="radar-knowledge-details" aria-label="雷达知识掌握与缺口"><div className="radar-detail-heading"><span>知识点</span><span>掌握</span><span>作答 / 可用</span><span>AC</span><span>待练</span></div>{shown.map(node=><div className="radar-detail-row" key={node.name}><button type="button" onClick={()=>select(node)}>{node.name}{domain&&<small>{node.difficulty}</small>}</button><b title={node.reason} data-unknown={node.value===null}>{valueText(node)}</b><span>{node.participated} / {node.available}</span><span>{node.officialAccepted}</span><span>{node.suggested&&onTrain?<button type="button" onClick={()=>onTrain(node.suggested)}>{node.due||'练习'}</button>:node.due}</span></div>)}</div>
 </section>;
}
