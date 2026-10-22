// Values match the public library dictionary; broad subjects never imply a technique.
const ALIASES={
 '二分查找':['二分'],'DFS':['深度优先搜索','深搜'],'BFS':['广度优先搜索','广搜'],
 '最短路':['最短路径','Dijkstra'],'生成树':['最小生成树'],'LCA':['最近公共祖先'],
 '素数':['素数筛','质数筛','筛法','埃氏筛','线性筛'],'取模与同余':['模运算'],
 '容斥':['容斥原理'],'KMP':['KMP 字符串匹配'],'字典树':['Trie 字典树','Trie'],
 '哈希':['哈希表','hashing'],'字符串':['字符串基础'],'数论':['数论基础'],
 '二分图判定':['二分图'],'背包 DP':['背包','01背包','完全背包'],
 '线性 DP':['线性DP'],'树形 DP':['树形DP'],'区间 DP':['区间DP'],'状压 DP':['状态压缩DP','状态压缩 DP']
};
const key = name => String(name || '').replace(/\s+/g,'').toLowerCase();
export function canonicalKnowledgeName(name){return Object.entries(ALIASES).find(([standard,values])=>[standard,...values].some(value=>key(value)===key(name)))?.[0]||String(name||'').trim();}
export function knowledgeAliases(name){const standard=canonicalKnowledgeName(name);return [standard,...(ALIASES[standard]||[])];}
export function matchesKnowledge(row,tags=[]){const wanted=new Set(tags.map(canonicalKnowledgeName));if((row.tags||[]).some(tag=>wanted.has(canonicalKnowledgeName(tag))))return true;const broad=new Set(['字符串','图论','动态规划','数据结构','数学','数论','搜索','计算几何']);return (row.knowledgeCategories||[]).some(path=>path.split(/\s*\/\s*/).some(name=>broad.has(name)&&wanted.has(name)));}
