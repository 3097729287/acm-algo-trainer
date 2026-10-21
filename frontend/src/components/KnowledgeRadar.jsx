import { useMemo, useState } from 'react';
import { ArrowLeft, Network } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
export const KNOWLEDGE_DOMAINS = [
  { name: '基础技巧', topics: [['前缀和',900],['差分',1100],['二分',1300],['双指针',1300],['位运算',1200],['离散化',1400],['倍增',1800]] },
  { name: '数据结构', topics: [['栈',900],['队列',900],['单调栈',1500],['单调队列',1700],['并查集',1500],['堆',1400],['树状数组',1800],['线段树',2100]] },
  { name: '图论', topics: [['图的存储',1100],['DFS',1300],['BFS',1300],['拓扑排序',1700],['最短路',1900],['最小生成树',1900],['二分图',2000],['LCA',2100]] },
  { name: '动态规划', topics: [['线性 DP',1500],['背包 DP',1700],['区间 DP',2000],['树形 DP',2100],['DAG DP',2000]] },
  { name: '搜索', topics: [['枚举',900],['递归',1100],['回溯',1400],['DFS',1300],['BFS',1300],['剪枝',1800],['折半枚举',2000]] },
  { name: '数学', topics: [['数论基础',1300],['快速幂',1300],['质数筛',1500],['组合计数',1800],['模运算',1500],['最大公约数',1000],['容斥',2000]] },
  { name: '字符串', topics: [['字符串基础',900],['字符串哈希',1700],['KMP',1900],['字典树',1800]] },
  { name: '思维与策略', topics: [['模拟',800],['排序',900],['贪心',1400],['构造',1700],['递推',1300]] },
];
const aliases = { '前缀和': ['前缀和与差分'], '差分': ['前缀和与差分'], 'DFS': ['深度优先搜索','深搜'], 'BFS': ['广度优先搜索','广搜'], '背包 DP': ['背包','01背包','完全背包'], '线性 DP': ['线性DP'], '树形 DP': ['树形DP'], '区间 DP': ['区间DP'], '最短路': ['Dijkstra','最短路径'], 'LCA': ['最近公共祖先'], '数论基础': ['数论'], '字符串基础': ['字符串'] };
export function topicTags(name) { return [name, ...(aliases[name] || [])]; }
export function estimatedDifficulty(name) {
  const found = KNOWLEDGE_DOMAINS.flatMap(domain => domain.topics).filter(([topic]) => topicTags(topic).some(tag => String(name).toLowerCase().includes(tag.toLowerCase())));
  if (found.length) return Math.max(...found.map(([,value]) => value));
  if (/流|后缀|自动机|多项式|FFT|NTT|生成函数|分治优化|可持久化|莫队/.test(name)) return 2400;
  if (/图|树|DP|动态规划|几何/.test(name)) return 2100;
  return 1600;
}
export default function KnowledgeRadar({ knowledge = [], onTopic }) {
  const [domain, setDomain] = useState(null);
  const mastery = name => {
    const tags = topicTags(name), entries = knowledge.filter(item => tags.includes(item.name));
    return entries.length ? Math.max(...entries.map(item => Math.max(0, Math.min(100, Number(item.mastery) || 0)))) : 0;
  };
  const nodes = useMemo(() => domain ? domain.topics.map(([name, difficulty]) => ({ name, difficulty, value: mastery(name) })) : KNOWLEDGE_DOMAINS.map(item => ({ ...item, value: item.topics.reduce((sum,[name]) => sum + mastery(name),0) / item.topics.length })), [domain, knowledge]);
  const position = (index, radius) => { const angle = -Math.PI / 2 + index * Math.PI * 2 / nodes.length; return [220 + Math.cos(angle)*radius, 190 + Math.sin(angle)*radius]; };
  const polygon = radius => nodes.map((_,i) => position(i,radius).join(',')).join(' ');
  const select = node => domain ? onTopic?.({ name: node.name, tags: topicTags(node.name) }) : setDomain(KNOWLEDGE_DOMAINS.find(item => item.name === node.name));
  return <section className="progress-section knowledge-radar" aria-label="知识点雷达图"><header className="progress-section-heading"><h2>{domain ? <button type="button" className="icon-button" aria-label="返回一级雷达" onClick={() => setDomain(null)}><ArrowLeft size={17}/></button> : <Network size={18}/>} {domain?.name || '知识点雷达'}</h2><Tooltip label="雷达说明" text="半径代表真实训练记录中的掌握程度；暂无证据时为 0。点击专题进入二级雷达，点击具体知识点筛选题目。难度为估计值，仅收录基础至常见图论层次（约 2200 以内）的知识点。"/></header>
    <svg viewBox="0 0 440 380" role="group" aria-label={domain ? `${domain.name}二级雷达` : '一级知识雷达'}>
      {[.25,.5,.75,1].map(ratio => <polygon key={ratio} className="radar-grid" points={polygon(132*ratio)}/>)}
      {nodes.map((node,i) => { const [x,y] = position(i,132), [tx,ty] = position(i,161); return <g key={node.name}><path className="radar-axis" d={`M220 190L${x} ${y}`}/><text x={tx} y={ty} textAnchor="middle" dominantBaseline="middle">{node.name}</text></g>; })}
      <polygon className="radar-value" points={nodes.map((node,i) => position(i,132*node.value/100).join(',')).join(' ')}/>
      {nodes.map((node,i) => { const [x,y] = position(i,132), [mx,my] = position(i,132*node.value/100); return <g key={node.name}><circle className="radar-data-dot" cx={mx} cy={my} r={3}/><circle className="radar-node" cx={x} cy={y} r={9} tabIndex={0} role="button" aria-label={`${node.name}，掌握 ${Math.round(node.value)}%，${domain ? '筛选题目' : '进入二级雷达'}`} onClick={() => select(node)} onKeyDown={event => { if (['Enter',' '].includes(event.key)) { event.preventDefault(); select(node); } }}><title>{node.name} · {Math.round(node.value)}%{domain ? ` · 估计难度 ${node.difficulty}` : ' · 查看知识点'}</title></circle></g>; })}
    </svg><div className="radar-legend">{nodes.map(node => <button type="button" key={node.name} onClick={() => select(node)}><span>{node.name}</span><b>{Math.round(node.value)}%</b>{domain && <small>≈{node.difficulty}</small>}</button>)}</div>
  </section>;
}
