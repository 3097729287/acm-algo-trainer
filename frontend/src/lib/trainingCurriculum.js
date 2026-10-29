import {problemDifficulty} from './problemOrder.js';

// Stages describe prerequisites, not a promise that a topic has one CF rating.
export const CURRICULUM_STAGES=['01 编程基础','02 基础解题方法','03 搜索与图','04 动态规划','05 数据结构进阶','06 数学与字符串','07 CF 2300 综合训练','08 专题加练','09 高阶拓展'];
const UNITS=[
 ['01 编程基础','输入输出与顺序结构',/顺序结构|输入输出/,1200],
 ['01 编程基础','分支与循环',/分支结构|循环结构/,1200],
 ['01 编程基础','数组与字符串',/数组|基础字符串|入门5/,1300],
 ['01 编程基础','函数、结构体与 STL',/函数|结构体|线性表与容器|STL|标准库/,1400],
 ['02 基础解题方法','模拟与枚举',/模拟与枚举|枚举|暴力/,1500],
 ['02 基础解题方法','排序与复杂度',/排序/,1600],
 ['02 基础解题方法','前缀和与差分',/前缀和|差分/,1700],
 ['02 基础解题方法','二分查找与二分答案',/二分与三分|二分|三分/,1800],
 ['02 基础解题方法','双指针与滑动窗口',/双指针|尺取|滑动窗口/,1800],
 ['02 基础解题方法','贪心与构造',/贪心|构造/,1900],
 ['02 基础解题方法','递推、递归与分治',/递推与分治|递归|递推|分治/,1800],
 ['03 搜索与图','DFS 与回溯',/深度优先|DFS|回溯|搜索/,1800],
 ['03 搜索与图','BFS 与最少步数',/广度优先|BFS/,1800],
 ['03 搜索与图','并查集',/并查集/,1900],
 ['03 搜索与图','拓扑排序与 DAG',/拓扑排序/,2000],
 ['03 搜索与图','最短路',/最短路/,2100],
 ['03 搜索与图','最小生成树',/生成树/,2100],
 ['03 搜索与图','树的遍历、倍增与 LCA',/树上算法|LCA|倍增|树形结构/,2200],
 ['04 动态规划','状态定义与线性 DP',/线性动态规划|新手动态规划|动态规划.*入门|动态规划.*基础/,1900],
 ['04 动态规划','背包 DP',/背包/,2100],
 ['04 动态规划','区间 DP',/区间动态规划|区间DP/,2200],
 ['04 动态规划','树形 DP',/树形动态规划|树形DP/,2300],
 ['04 动态规划','状态压缩 DP',/状态压缩|状压/,2300],
 ['04 动态规划','数位 DP',/数位动态规划|数位DP/,2300],
 ['05 数据结构进阶','堆与单调结构',/堆与二叉树|单调栈|单调队列|二叉堆/,2000],
 ['05 数据结构进阶','树状数组',/树状数组/,2200],
 ['05 数据结构进阶','线段树',/线段树/,2300],
 ['05 数据结构进阶','分块与离线处理',/分块|莫队|离线/,2300],
 ['06 数学与字符串','整除、质数与模运算',/数论|最大公约数|素数|快速幂|乘法逆元|取模与同余/,2100],
 ['06 数学与字符串','组合计数与基础概率',/组合与计数|组合计数|概率与期望|期望与概率/,2300],
 ['06 数学与字符串','基础博弈',/博弈/,2200],
 ['06 数学与字符串','字符串哈希与字典树',/字符串哈希|字典树/,2200],
 ['06 数学与字符串','KMP 与 Z 函数',/模式匹配|KMP|Z函数/,2300],
 ['06 数学与字符串','基础计算几何',/计算几何/,2200],
 ['07 CF 2300 综合训练','图的连通性与综合建模',/连通性|2-SAT|图论.*综合/,2300],
 ['07 CF 2300 综合训练','动态规划综合',/动态规划.*综合|动态规划优化/,2300],
 ['07 CF 2300 综合训练','数学与字符串综合',/数学.*综合|字符串.*综合|回文算法/,2300],
 ['07 CF 2300 综合训练','区域赛与思维综合',/赛事真题|综合训练|思维训练|XCPC|ICPC|CCPC/,2300],
];
const ADVANCED=/后缀结构|后缀与回文综合|后缀自动机|后缀数组|\bSAM\b|多项式|生成函数|FFT|NTT|莫比乌斯|杜教筛|洲阁筛|Min_25|动态树|可持久化|主席树|圆方树|点分治|点分树|虚树|轮廓线|Slope Trick|wqs|李超树|线性基|半平面交|网络流与匹配|网络流|费用流|最大流/i;
const keyOf=(item,row)=>row?.id||item.problemId||item.url||item.pid;
// Scope is limited to collections; the public library and private evidence stay
// intact. Resolve original IDs, aliases and URL entries before reading ratings.
export function filterTrainingListsScope(lists,rows) {
 const byId=new Map(),byUrl=new Map();
 for(const row of rows){for(const id of [row.id,...row.aliasIds||[]])byId.set(id,row);if(row.url)byUrl.set(row.url.replace(/\/$/,''),row);}
 return lists.map(list=>{
  const event=list.topicPath?.includes('赛事真题')||list.displayTitle==='赛事真题'||list.title==='赛事真题';
  const problems=(list.problems||[]).filter(item=>{
   const row=byId.get(item.problemId)||byUrl.get(item.url?.replace(/\/$/,''));
   const rating=row?problemDifficulty(row):null;
   return rating==null||rating<=2500&&(!event||rating!==900);
  });
  return {...list,problems,problemCount:problems.length};
 });
}
// Classify the source topic first. Substring matching alone sends 树状数组 to
// 数组, 拓扑排序 to 排序, and BFS to the generic 搜索/DFS unit.
function classify(list,row) {
 const [category,topic='']=list.topicPath||[];
 const title=[list.displayTitle,list.title].join(' '),tags=[row.knowledge,...row.tags||[]].join(' ').replace(/\s+/g,'');
 const exact={
  '基础算法':{'模拟与枚举':4,'排序':5,'前缀和与差分':6,'二分与三分':7,'双指针':8,'贪心与构造':9,'递推与分治':10},
  '数据结构':{'线性表与容器':3,'并查集':13,'树状数组':25,'线段树':26,'单调栈与单调队列':24,'分块与莫队':27},
  '图论':{'最短路':15,'生成树':16,'树上算法':17,'连通性':34},
  '动态规划':{'入门':18,'线性动态规划':18,'背包':19,'区间动态规划':20,'树形动态规划':21,'状态压缩':22,'数位动态规划':23,'动态规划优化':35,'综合练习':35},
  '数学':{'数论':28,'组合与计数':29,'概率与期望':29,'博弈':30,'综合练习':36},
  '字符串':{'字符串基础':2,'字典树':31,'字符串哈希':31,'模式匹配':32,'回文算法':36,'综合练习':36},
 };
 if(category==='语言入门')return /顺序结构|输入输出/.test(title)?0:/分支|循环/.test(title)?1:/函数|结构体|STL/.test(title)?3:2;
 if(category==='搜索')return /BFS|广度优先/.test(title)||/BFS|广度优先/.test(tags)&&!/DFS|深度优先/.test(tags)?12:11;
 if(category==='图论'&&topic==='拓扑排序与 2-SAT')return /2.?SAT/i.test(tags)||/2.?SAT/i.test(title)&&!/拓扑/.test(title)?34:14;
 if(category==='数据结构'&&/堆与/.test(topic))return /树状数组/.test(tags)?25:/堆|优先队列/.test(tags)||/堆与树状数组/.test(topic)?24:17;
 if(exact[category]?.[topic]!=null)return exact[category][topic];
 if(category==='计算几何')return 33;
 // Mixed collections only fill a topic when the problem itself names it.
 const precise=[[23,/数位DP/],[22,/状压DP|状态压缩/],[21,/树形DP/],[20,/区间DP/],[19,/背包/],[25,/树状数组/],[26,/线段树/],[14,/拓扑排序/],[13,/并查集/],[16,/生成树/],[15,/最短路/],[17,/LCA|树的遍历/],[12,/BFS|广度优先/],[11,/DFS|深度优先/],[24,/单调栈|单调队列|堆/],[32,/KMP|Z函数/],[31,/字典树|字符串哈希/],[8,/双指针|滑动窗口/],[6,/前缀和|差分/],[7,/二分/],[18,/线性DP/],[28,/素数|质数|取模|最大公约数/],[29,/排列组合|组合计数/]];
 const matched=precise.find(([,pattern])=>pattern.test(tags));
 if(matched)return matched[0];
 return category==='赛事真题'||category==='综合训练'&&topic==='思维训练'?37:null;
}
export function buildTrainingCurriculum(lists,rows) {
 const byId=new Map(),byUrl=new Map();
 for(const row of rows){for(const id of [row.id,...row.aliasIds||[]])byId.set(id,row);if(row.url)byUrl.set(row.url.replace(/\/$/,''),row);}
 const candidates=new Map();
 for(const list of lists){
  if(!list.available)continue;
  const text=[...(list.topicPath||[]),list.displayTitle,list.title].join(' ');
  const advanced=ADVANCED.test(text);
  for(const original of list.problems||[]){
   const row=byId.get(original.problemId)||byUrl.get(original.url?.replace(/\/$/,''));
   if(!row)continue;
   const tags=[row.knowledge,...row.tags||[]].join(' ').replace(/\s+/g,'');
   const unit=classify(list,row);
   const specific=(['教材配套','综合训练','待补充信息','赛事真题'].includes(list.topicPath?.[0])?0:6)+(!/综合/.test(list.topicPath?.[1]||'')?2:0)+(unit!=null&&UNITS[unit][2].test(tags)?2:0);
   const key=keyOf(original,row),previous=candidates.get(key);
   // A precise introductory source wins over a broad collection of advanced tasks.
   if(!previous||specific>previous.specific)candidates.set(key,{item:{...original,sections:[]},row,unit,advanced,specific,category:list.topicPath?.[0]||'综合练习',sources:[list.id]});
  }
 }
 const grouped=UNITS.map(()=>[]),extra=new Map(),advanced=new Map();
 const put=(map,title,value)=>{if(!map.has(title))map.set(title,[]);map.get(title).push(value);};
 for(const value of candidates.values()){
  const difficulty=problemDifficulty(value.row);
  if(value.advanced||difficulty>2300){put(advanced,value.category,value);continue;}
  if(value.unit==null||difficulty==null||difficulty>UNITS[value.unit][3]||(value.unit>=34&&difficulty<1800)){put(extra,value.category,value);continue;}
  grouped[value.unit].push(value);
 }
 const result=[];
 const make=(id,title,path,values,order)=>({id,title,displayTitle:title,originalTitle:title,topicPath:path,sourceLabel:'',curriculumOrder:order,available:true,aggregateChildren:false,children:[],categories:[],problems:values.map(v=>v.item),url:null});
 grouped.forEach((values,index)=>{
  values.sort((a,b)=>problemDifficulty(a.row)-problemDifficulty(b.row)||String(a.row.id).localeCompare(String(b.row.id),'en',{numeric:true}));
  // Sample across the available range; a large source should not drown the route.
  const chosen=new Set();const count=Math.min(18,values.length);
  for(let i=0;i<count;i++)chosen.add(Math.floor(i*(values.length-1)/Math.max(1,count-1)));
  const selected=values.filter((v,i)=>chosen.has(i));
  for(const [i,value] of values.entries())if(!chosen.has(i))put(extra,value.category,value);
  if(selected.length)result.push(make(`curriculum:${index}`,UNITS[index][1],[UNITS[index][0]],selected,index));
 });
 for(const [kind,groups] of [['08 专题加练',extra],['09 高阶拓展',advanced]])for(const [category,values] of groups)if(values.length)result.push(make(`curriculum:${kind.slice(0,2)}:${category}`,category,[kind],values,100+result.length));
 return consolidateSmallCurriculum(result);
}

// Public generated routes only: private/source collections retain their identity.
// Prefer the same stage's general practice; keep every original problem once.
export function consolidateSmallCurriculum(lists){
 const result=lists.map(list=>({...list,problems:[...(list.problems||[])]})),removed=new Set();
 for(const list of result){
  if(!list.id?.startsWith('curriculum:')||list.problems.length>2||removed.has(list.id))continue;
  if(!list.problems.length){removed.add(list.id);continue;}
  const sameStage=result.filter(other=>other!==list&&!removed.has(other.id)&&other.problems.length>2&&other.topicPath?.[0]===list.topicPath?.[0]);
  const target=sameStage.find(other=>other.title==='综合训练')||sameStage.find(other=>other.title==='基础算法')||sameStage.sort((a,b)=>b.problems.length-a.problems.length)[0];
  if(!target)continue;
  const identities=new Set(target.problems.map(item=>keyOf(item)));
  for(const item of list.problems)if(!identities.has(keyOf(item))){target.problems.push(item);identities.add(keyOf(item));}
  target.problemCount=target.problems.length;removed.add(list.id);
 }
 return result.filter(list=>!removed.has(list.id));
}
