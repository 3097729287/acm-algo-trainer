const ALIASES={
 '二分查找':['二分'],'深度优先搜索':['DFS','深搜'],'广度优先搜索':['BFS','广搜'],
 '最短路径':['最短路','Dijkstra'],'最小生成树':['生成树'],'最近公共祖先':['LCA'],
 '素数筛':['质数筛','素数','筛法','埃氏筛','线性筛'],'取模与同余':['模运算'],
 '容斥原理':['容斥'],'KMP 字符串匹配':['KMP'],'Trie 字典树':['字典树','Trie'],
 '字符串哈希':['哈希'],'数论基础':['数论'],'字符串基础':['字符串'],
 '前缀和':['前缀和与差分'],'差分':['前缀和与差分'],'背包 DP':['背包','01背包','完全背包'],
 '线性 DP':['线性DP'],'树形 DP':['树形DP'],'区间 DP':['区间DP'],'DAG DP':['DAG动态规划']
};
export function canonicalKnowledgeName(name){return Object.entries(ALIASES).find(([key,values])=>key===name||values.includes(name))?.[0]||name;}
export function knowledgeAliases(name){const key=canonicalKnowledgeName(name);return [key,...(ALIASES[key]||[])];}
