import {useMemo,useState} from 'react';
import {ArrowLeft,Network,Search} from 'lucide-react';
import PageSearch from './PageSearch.jsx';
import FilterMenu from './FilterMenu.jsx';
import {knowledgeAliases} from '@/lib/knowledgeNames.js';
export const KNOWLEDGE_DOMAINS = [
  { name: '基础技巧', topics: [['前缀和',900],['差分',1100],['二分查找',1300],['双指针',1300],['位运算',1200],['离散化',1400],['倍增',1800]] },
  { name: '数据结构', topics: [['栈',900],['队列',900],['单调栈',1500],['单调队列',1700],['并查集',1500],['堆',1400],['树状数组',1800],['线段树',2100]] },
  { name: '图论', topics: [['图的存储',1100],['深度优先搜索',1300],['广度优先搜索',1300],['拓扑排序',1700],['最短路径',1900],['最小生成树',1900],['二分图',2000],['最近公共祖先',2100]] },
  { name: '动态规划', topics: [['线性 DP',1500],['背包 DP',1700],['区间 DP',2000],['树形 DP',2100],['DAG DP',2000]] },
  { name: '搜索', topics: [['枚举',900],['递归',1100],['回溯',1400],['深度优先搜索',1300],['广度优先搜索',1300],['剪枝',1800],['折半枚举',2000]] },
  { name: '数学', topics: [['数论基础',1300],['快速幂',1300],['素数筛',1500],['组合计数',1800],['取模与同余',1500],['最大公约数',1000],['容斥原理',2000]] },
  { name: '字符串', topics: [['字符串基础',900],['字符串哈希',1700],['KMP 字符串匹配',1900],['Trie 字典树',1800]] },
  { name: '思维与策略', topics: [['模拟',800],['排序',900],['贪心',1400],['构造',1700],['递推',1300]] },
];

export function topicTags(name){return knowledgeAliases(name);}
export function estimatedDifficulty(name){const found=KNOWLEDGE_DOMAINS.flatMap(domain=>domain.topics).filter(([topic])=>topicTags(topic).some(tag=>String(name).toLowerCase().includes(tag.toLowerCase())));if(found.length)return Math.max(...found.map(([,value])=>value));if(/流|后缀|自动机|多项式|FFT|NTT|生成函数|分治优化|可持久化|莫队/.test(name))return 2400;return /图|树|DP|动态规划|几何/.test(name)?2100:1600;}
export default function KnowledgeRadar({knowledge=[],onTopic,onTrain}) {
 const [domain,setDomain]=useState(null),[query,setQuery]=useState(''),[gaps,setGaps]=useState(false);
 const evidence=names=>{const tags=new Set(names.flatMap(topicTags));return knowledge.filter(item=>tags.has(item.name));};
 const facts=names=>{const entries=evidence(names),maximum=key=>Math.max(0,...entries.map(item=>Number(item[key])||0));return {value:maximum('mastery'),available:maximum('available'),participated:maximum('participated'),officialAccepted:maximum('officialAccepted'),localAccepted:maximum('localAccepted'),due:maximum('due'),failures:maximum('failures'),suggested:entries.flatMap(item=>item.suggestedIds||[])[0]};};
 const nodes=useMemo(()=>domain?domain.topics.map(([name,difficulty])=>({name,difficulty,...facts([name])})):KNOWLEDGE_DOMAINS.map(item=>({...item,...facts(item.topics.map(([name])=>name)),value:item.topics.reduce((sum,[name])=>sum+facts([name]).value,0)/item.topics.length})),[domain,knowledge]);
 const position=(index,radius)=>{const angle=-Math.PI/2+index*Math.PI*2/nodes.length;return [340+Math.cos(angle)*radius,245+Math.sin(angle)*radius];};
 const polygon=radius=>nodes.map((_,i)=>position(i,radius).join(',')).join(' ');
 const select=node=>{if(domain)onTopic?.({name:node.name,tags:topicTags(node.name)});else setDomain(KNOWLEDGE_DOMAINS.find(item=>item.name===node.name));};
 const shown=nodes.filter(node=>(!gaps||node.due>0||node.failures>0||node.value<50)&&topicTags(node.name).some(tag=>tag.toLowerCase().includes(query.trim().toLowerCase())));
 return <section className="progress-section knowledge-radar" aria-label="知识点雷达图">
 <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索知识点" value={query} onChange={event=>setQuery(event.target.value)}/></label><FilterMenu label="雷达筛选" active={gaps}><label className="filter-field"><span>只看待加强</span><input type="checkbox" checked={gaps} onChange={event=>setGaps(event.target.checked)}/></label></FilterMenu></PageSearch>
 <header className="progress-section-heading"><h2>{domain?<button className="icon-button" aria-label="返回一级雷达" onClick={()=>{setDomain(null);setQuery('');}}><ArrowLeft size={18}/></button>:<Network size={19}/>} {domain?.name||'知识点雷达'}</h2></header>
 <svg viewBox="0 0 680 500" role="group" aria-label={domain?`${domain.name}二级雷达`:'一级知识雷达'}>
 {[.25,.5,.75,1].map(ratio=><polygon key={ratio} className="radar-grid" points={polygon(163*ratio)}/>)}
 {nodes.map((node,i)=>{const [x,y]=position(i,163),[tx,ty]=position(i,199);return <g key={node.name}><path className="radar-axis" d={`M340 245L${x} ${y}`}/><text x={tx} y={ty} textAnchor="middle" dominantBaseline="middle">{node.name}</text></g>;})}
 <polygon className="radar-value" points={nodes.map((node,i)=>position(i,163*Math.max(0,Math.min(100,node.value))/100).join(',')).join(' ')}/>
 {nodes.map((node,i)=>{const [x,y]=position(i,163),[mx,my]=position(i,163*node.value/100);return <g key={node.name}><circle className="radar-data-dot" cx={mx} cy={my} r={3}/><circle className="radar-node" cx={x} cy={y} r={8} tabIndex={0} role="button" aria-label={`${node.name}，掌握 ${Math.round(node.value)}%，${domain?'筛选题目':'进入二级雷达'}`} onClick={()=>select(node)} onKeyDown={event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();select(node);}}}/></g>;})}
 </svg>
 <div className="radar-knowledge-details" aria-label="雷达知识掌握与缺口"><div className="radar-detail-heading"><span>知识点</span><span>掌握</span><span>参与 / 可用</span><span>AC</span><span>待练</span></div>{shown.map(node=><div className="radar-detail-row" key={node.name}><button type="button" onClick={()=>select(node)}>{node.name}{domain&&<small>≈{node.difficulty}</small>}</button><b>{Math.round(node.value)}%</b><span>{node.participated} / {node.available}</span><span>{node.officialAccepted}</span><span>{node.suggested&&onTrain?<button type="button" onClick={()=>onTrain(node.suggested)}>{node.due||'练习'}</button>:node.due}</span></div>)}</div>
 </section>;
}
