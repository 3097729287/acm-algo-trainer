// Values match the public library dictionary; broad subjects never imply a technique.
const ALIASES={
 '二分查找':['二分'],'DFS':['深度优先搜索','深搜'],'BFS':['广度优先搜索','广搜'],
 '最短路':['最短路径','Dijkstra'],'生成树':['最小生成树'],'LCA':['最近公共祖先'],
 '素数':['素数筛','质数筛','筛法','埃氏筛','线性筛'],'取模与同余':['模运算'],
 '容斥':['容斥原理'],'KMP':['KMP 字符串匹配'],'字典树':['Trie 字典树','Trie'],
 '哈希':['哈希表','hashing'],'字符串':['字符串基础'],'数论':['数论基础'],
 '二分图判定':['二分图'],'背包 DP':['背包','01背包','完全背包'],
 '线性 DP':['线性DP'],'树形 DP':['树形DP'],'区间 DP':['区间DP'],'状压 DP':['状态压缩DP','状态压缩 DP'],
 '最小公倍数':['lcm','least common multiple','最小公倍数 lcm'],'最大公约数':['gcd','最大公约数 gcd'],
 '离散化':['坐标压缩','coordinate compression'],'链表':['linked list','双向链表','静态链表'],
 '交互题':['interactive','交互式题目'],'点积与叉积':['点积','叉积','向量叉积'],
 '多边形面积':['鞋带公式'],'距离与投影':['欧氏距离','曼哈顿距离','切比雪夫距离']
};
const SCOPE_ALIASES={'数学与计数':['数学','计数']};
const key = name => String(name || '').replace(/\s+/g,'').toLowerCase();
const CANONICAL = new Map(Object.entries(ALIASES).flatMap(([standard,values])=>[standard,...values].map(value=>[key(value),standard])));
export function canonicalKnowledgeName(name){return CANONICAL.get(key(name))||String(name||'').trim();}
export function knowledgeAliases(name){const standard=canonicalKnowledgeName(name);return [standard,...(ALIASES[standard]||[]),...(SCOPE_ALIASES[standard]||[])];}
export function knowledgeFilterNames(node){return [...new Set([...knowledgeAliases(node.name),...(node.tags||[]),...(node.children||[]).flatMap(knowledgeFilterNames)])];}
export function rowKnowledgeNames(row){return new Set([...(row.tags||[]),...String(row.knowledge||'').split(/\s*\+\s*|[;,，；]/),...(row.knowledgeCategories||[]).flatMap(path=>path.split(/\s*\/\s*/))].filter(Boolean).map(canonicalKnowledgeName));}
export function compileKnowledge(tags=[]){const wanted=new Set(tags.map(canonicalKnowledgeName));return row=>{for(const name of rowKnowledgeNames(row))if(wanted.has(name))return true;return false;};}
export function matchesKnowledge(row,tags=[]){return compileKnowledge(tags)(row);}
export function indexKnowledgeRows(rows){
 const index=new Map();
 for(const row of rows){const identity=row.url||row.id;for(const name of rowKnowledgeNames(row)){if(!index.has(name))index.set(name,new Set());index.get(name).add(identity);}}
 return index;
}
