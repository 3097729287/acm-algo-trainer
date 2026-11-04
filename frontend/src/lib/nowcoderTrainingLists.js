import {normalizeNowcoderChapters} from './nowcoderCurriculum.js';
const ROOTS={
 'nowcoder-817596':['语法与算法入门',0],
 'nowcoder-926597':['算法基础精选',1],
 'nowcoder-828697':['算法进阶',2],
};
const TITLES={
 '18839':'顺序结构','19304':'分支结构','19305':'循环结构','19306':'数组与字符串','19859':'函数与递归','19850':'栈、队列与 STL',
 '19851':'模拟、枚举与贪心 · 第 1 组','20960':'模拟、枚举与贪心 · 第 2 组','21763':'递归与分治','22353':'二分、三分与 01 分数规划','22669':'堆、栈与单调队列','22904':'优先队列与并查集','23156':'搜索与剪枝',
 '24213':'动态规划 · 线性、背包与区间','25022':'动态规划 · 树形与状态压缩','26077':'图论基础 · 最短路与最小生成树','26656':'数学基础','26896':'线段树与树状数组','27836':'RMQ 与 LCA',
 '28258':'树形 DP · 例题','28259':'状态压缩 DP · 例题','28260':'树形 DP · 练习','28261':'状态压缩 DP · 练习','28262':'数位 DP · 例题','28263':'概率 DP · 例题','28264':'数位 DP · 练习','28265':'概率 DP · 练习','28267':'动态规划 · 优化思路与技巧','28266':'动态规划 · 综合练习',
 '19483':'前缀和与差分 · 进阶应用','19684':'树状数组与线段树 · 进阶应用','19917':'线段树 · 李超树与复杂度分析','20160':'平衡树与伸展树','20376':'分块与莫队','20647':'可持久化数据结构','20888':'CDQ 分治','22131':'树上数据维护 · DSU on Tree 与长链剖分','22681':'动态树（LCT）',
 '21094':'整数分解与筛法','21289':'同余、逆元与中国剩余定理','21791':'排列组合基础','22529':'容斥原理','22769':'积性函数与莫比乌斯反演','24157':'矩阵与高斯消元','24710':'生成函数 · 基础与线性递推','26013':'原根与 FFT / NTT','26757':'生成函数 · 组合计数与快速计算',
 '27589':'KMP · 基础与应用','28576':'字符串哈希','28737':'字典树（Trie）','29086':'AC 自动机','33548':'回文算法 · PAM 与 Manacher','34974':'后缀数组（SA）','37092':'后缀自动机（SAM）',
 '27249':'平面几何基础','27675':'极角排序','28513':'凸包 · 基础','28770':'凸包 · 进阶','29764':'半平面交','36088':'扫描线','40275':'圆','52826':'综合专题',
 '32183':'组合博弈 · 基础与对抗搜索','34655':'组合博弈 · SG 函数与 Nim 和',
 'collection-1266':'综合练习','collection-1090':'二分图 · 例题与练习','collection-1107':'连通性 · 例题与练习','collection-1126':'网络流 · 例题与练习',
};
export function organizeNowcoderTrainingLists(lists){
 const parents=new Map();
 for(const list of lists)if(ROOTS[list.id])for(const [index,id]of(list.children||[]).entries())parents.set(id,{root:list.id,index});
 return lists.map(list=>{
  if(!list.id?.startsWith('nowcoder-'))return list;
  const root=ROOTS[list.id],parent=parents.get(list.id),key=list.id.replace(/^nowcoder-contest-/,'').replace(/^nowcoder-collection-/,'collection-');
  const displayTitle=root?.[0]||TITLES[key]||(list.id==='nowcoder-817596-sequential-verified'?'顺序结构 · 精选练习':list.displayTitle||list.title);
  return normalizeNowcoderChapters({...list,displayTitle,directoryRow:true,learningSequence:true,hideSectionFolders:Boolean(root&&list.children?.length),sourceLabel:root?'牛客公开题单':parent?ROOTS[parent.root][0]:list.sourceLabel,
   curriculumOrder:root?root[1]:parent?parent.index:1000,
   catalogHidden:Boolean((parent||list.id==='nowcoder-817596-sequential-verified'&&lists.some(item=>item.id==='nowcoder-817596'))),
   originalTitle:list.originalTitle||list.title});
 });
}
