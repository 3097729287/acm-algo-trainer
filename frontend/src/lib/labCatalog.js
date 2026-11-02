import {ALGORITHM_TOPICS} from './algorithmLearning.js';
import SORTING_COURSES from '../../../backend/resources/sorting-lab.json';
import GRAPH_COURSES from '../../../backend/resources/graph-lab.json';

const COURSE_ORDER = ['sorting-basics','prefix-difference','two-pointers','binary-search','window-extrema','divide-sort','bucket-sort','bfs','dfs','dsu','fenwick','segment-tree','binary-lifting','li-chao','dijkstra','dinic','trie','linear-basis','knapsack'];
const COURSE_GROUPS=[['基础算法',COURSE_ORDER.slice(0,7)],['搜索', ['bfs','dfs']],['数据结构',['dsu','fenwick','segment-tree','binary-lifting','li-chao']],['图论',['dijkstra','dinic']],['字符串',['trie']],['数学',['linear-basis']],['动态规划',['knapsack']]];
export const LAB_CATALOG = [
  {id:'binary-search',title:'整数二分',search:'binary search 二分答案 lower_bound upper_bound',first:'0'},
  {id:'window-extrema',title:'单调队列',search:'window deque 单调栈 滑动窗口 最小值 最大值',first:'0'},
  ...ALGORITHM_TOPICS.filter(topic=>topic.id!=='dsu').map(topic=>({id:topic.id,title:topic.title,search:topic.id+' '+topic.operations.map(op=>op[0]).join(' '),first:'0'})),
  ...Object.entries(SORTING_COURSES).map(([id,c])=>({id,title:c.title,search:id+' 冒泡 插入 选择 归并 快速 随机 桶 基数 排序',description:c.description,meta:`${c.chapters.length} 节互动课 · 5 道跟做题`,first:c.chapters[0].id})),
  ...Object.entries(GRAPH_COURSES).map(([id,c])=>({id,title:c.title,search:id,description:c.description,meta:"7 节互动课 · 5 道跟做题",first:"0"})),
  { id: 'prefix-difference', title: '前缀和与差分', search: 'prefix sum difference', description: '从区间总账走到边界事件。亲手把累计量与变化量互相还原，分清何时只用其中一个、何时组合使用。', meta: '7 节互动课 · 一维与二维 · 5 道跟做题', first: 'sum' },
  { id: 'two-pointers', title: '双指针算法', search: 'two pointers sliding window 滑动窗口 快慢指针 相向指针', description: '移动之前，先证明不会漏掉答案。从排除候选，到伸缩窗口与原地保留，再用负数亲手检验移动的依据。', meta: '7 节互动课 · 相向、滑窗、快慢 · 5 道跟做题', first: 'pair' },
  { id: 'knapsack', title: '背包 DP', search: '动态规划 knapsack', description: '从一次装包开始，学会定义小问题、推导选择、辨认倒序更新背后的旧状态。', meta: '7 节互动课 · 状态、选择与读写顺序 · 5 道跟做题', first: 'pack' },
].sort((a,b)=>COURSE_ORDER.indexOf(a.id)-COURSE_ORDER.indexOf(b.id));
