// These folders organize list titles; they never assign evidence to a problem.
const TOPICS = [
  ['动态规划', '背包', /背包|knapsack/i],
  ['动态规划', '树形动态规划', /树.{0,3}(?:dp|动态规划)|(?:dp|动态规划).{0,3}树/i],
  ['动态规划', '区间动态规划', /区间.{0,3}(?:dp|动态规划)|环形动态规划/i],
  ['动态规划', '状态压缩', /状压|状态压缩|轮廓线/i],
  ['动态规划', '动态规划优化', /(?:dp|动态规划).{0,4}优化|斜率优化|决策单调/i],
  ['动态规划', '', /动态规划|\bdp\b|数位dp/i],
  ['图论', '最短路', /最短路|差分约束/],
  ['图论', '生成树', /生成树/],
  ['图论', '网络流与匹配', /网络流|费用流|最大流|二分图|匹配/],
  ['图论', '连通性', /连通|强连通|割点|割边|缩点/],
  ['图论', '树上算法', /树链|树剖|树上|点分治|LCA|倍增.*树/i],
  ['图论', '', /图论|图的|【图|\[图/],
  ['数据结构', '线段树', /线段树|主席树/],
  ['数据结构', '树状数组', /树状数组/],
  ['数据结构', '并查集', /并查集/],
  ['数据结构', '平衡树', /平衡树|splay|treap/i],
  ['数据结构', '分块与莫队', /分块|莫队/],
  ['数据结构', '', /数据结构|二叉树|二叉堆|线性表|链表|队列|单调栈|集合/],
  ['字符串', '', /字符串|KMP|AC自动机|后缀|回文|字典树|trie|哈希/i],
  ['数学', '数论', /数论|同余|素数|质数|莫比乌斯|欧拉|整除/],
  ['数学', '组合与计数', /组合|计数|容斥/],
  ['数学', '概率与期望', /概率|期望|统计/],
  ['数学', '多项式与线性代数', /多项式|FFT|NTT|线性代数|高斯|矩阵|线性基/i],
  ['数学', '博弈', /博弈/],
  ['计算几何', '', /几何|凸包/],
  ['数学', '', /数学/],
  ['搜索', '', /搜索|BFS|DFS|剪枝|A\*/i],
  ['基础算法', '前缀和与差分', /前缀和|差分|离散化/],
  ['基础算法', '二分与三分', /二分|三分/],
  ['基础算法', '贪心', /贪心/],
  ['基础算法', '排序', /排序/],
  ['基础算法', '双指针', /双指针|尺取|滑动窗口/],
  ['基础算法', '模拟与枚举', /模拟|枚举|高精度/],
  ['基础算法', '递推与分治', /递推|递归|分治|倍增/],
  ['基础算法', '', /基本算法|基础算法|构造|位运算/],
  ['语言入门', '', /入门[1-6]|顺序结构|分支结构|循环结构|数组基础|语言入门|函数与结构体/],
  ['赛事真题', '', /GESP|CSP|NOIP|蓝桥杯|月赛|真题|[12]\d{3}\s*年/i],
];

export function algorithmPath(title) {
  const match = TOPICS.find(([, , pattern]) => pattern.test(title));
  return match ? match.slice(0, 2).filter(Boolean) : ['综合训练'];
}

const urlKey = url => String(url || '').replace(/^https?:\/\/(?:www\.)?/, '').replace(/[?#].*$/, '').replace(/\/$/, '');
export const startsWithPath = (path, prefix) => prefix.every((part, i) => path[i] === part);

export function trainingIndex(lists, rows) {
  const byId = new Map(), byUrl = new Map(), byList = new Map(lists.map(list => [list.id, list]));
  for (const row of rows) {
    for (const id of [row.id, ...(row.aliasIds || [])]) byId.set(id, row);
    byUrl.set(urlKey(row.url), row);
  }
  const resolve = item => ({ ...item, row: byId.get(item.problemId) || byUrl.get(urlKey(item.url)) || null });
  const own = new Map(lists.map(list => {
    const unique = new Map();
    for (const item of list.problems.map(resolve)) {
      const key = item.row?.id || urlKey(item.url) || item.pid;
      if (!unique.has(key)) unique.set(key, item);
    }
    return [list.id, [...unique.values()]];
  }));
  const cache = new Map();
  function all(id) {
    if (cache.has(id)) return cache.get(id);
    const found = new Map(), visited = new Set();
    function visit(key) {
      if (visited.has(key)) return;
      visited.add(key);
      for (const item of own.get(key) || []) {
        const identity = item.row?.id || urlKey(item.url) || item.pid;
        if (!found.has(identity)) found.set(identity, item);
      }
      if (byList.get(key)?.aggregateChildren !== false) {
        for (const child of byList.get(key)?.children || []) visit(child);
      }
    }
    visit(id);
    const result = [...found.values()];
    cache.set(id, result);
    return result;
  }
  const categories = [...new Map(lists.flatMap(list => list.categories || []).map(category => [category.id, category])).values()].sort((a, b) => a.order - b.order);
  function stats(ids) {
    const unique = new Map();
    for (const id of ids) for (const item of all(id)) unique.set(item.row?.id || urlKey(item.url) || item.pid, item);
    return { total: unique.size, accepted: [...unique.values()].filter(item => item.row?.accepted).length };
  }
  return { byList, own, all, categories, stats };
}

export function matchesTrainingProblem(item, query, status = '') {
  const text = [item.pid, item.row?.title, ...(item.row?.tags || []), ...(item.sections || [])].join(' ').toLocaleLowerCase();
  return query.trim().toLocaleLowerCase().split(/\s+/).every(word => text.includes(word))
    && (status !== 'accepted' || item.row?.accepted)
    && (status !== 'pending' || !item.row?.accepted);
}
