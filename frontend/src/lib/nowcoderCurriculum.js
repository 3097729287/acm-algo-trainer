// A navigation projection of the existing public collections. Original IDs,
// source links and underlying problem identities remain available separately.
export const NOWCODER_STAGES=['01 编程基础','02 基础解题方法','03 搜索与图论','04 动态规划','05 数据结构','06 数学与字符串','07 计算几何','08 综合训练'];
const ROOTS=['nowcoder-817596','nowcoder-926597','nowcoder-828697'];
const unit=(stage,name)=>[NOWCODER_STAGES[stage-1],name];
const UNITS={
 '18839':unit(1,'01 输入输出与顺序结构'),'19304':unit(1,'02 分支结构'),'19305':unit(1,'03 循环结构'),'19306':unit(1,'04 数组与字符串'),'19859':unit(1,'05 函数与递归'),'19850':unit(1,'06 STL 与基本容器'),
 '19851':unit(2,'01 模拟、枚举与贪心'),'20960':unit(2,'01 模拟、枚举与贪心'),'21763':unit(2,'02 递归与分治'),'22353':unit(2,'03 二分、三分与分数规划'),'19483':unit(2,'04 前缀和与差分'),
 '23156':unit(3,'01 搜索与剪枝'),'26077':unit(3,'02 最短路与最小生成树'),'27836':unit(3,'03 树上倍增与 LCA'),'collection-1090':unit(3,'04 二分图'),'collection-1107':unit(3,'05 图的连通性'),'collection-1126':unit(3,'06 网络流'),
 '24213':unit(4,'01 线性、背包与区间 DP'),'25022':unit(4,'02 树形与状态压缩 DP'),'28258':unit(4,'02 树形与状态压缩 DP'),'28259':unit(4,'02 树形与状态压缩 DP'),'28260':unit(4,'02 树形与状态压缩 DP'),'28261':unit(4,'02 树形与状态压缩 DP'),
 '28262':unit(4,'03 数位 DP'),'28264':unit(4,'03 数位 DP'),'28263':unit(4,'04 概率 DP'),'28265':unit(4,'04 概率 DP'),'28267':unit(4,'05 动态规划优化'),'28266':unit(4,'06 动态规划综合'),
 '22669':unit(5,'01 栈、队列与单调结构'),'22904':unit(5,'02 堆与并查集'),'26896':unit(5,'03 树状数组与线段树'),'19684':unit(5,'04 树状数组与线段树进阶'),'19917':unit(5,'04 树状数组与线段树进阶'),'20160':unit(5,'05 平衡树与伸展树'),'20376':unit(5,'06 分块与莫队'),'20647':unit(5,'07 可持久化数据结构'),'20888':unit(5,'08 CDQ 分治'),'22131':unit(5,'09 树上数据维护'),'22681':unit(5,'10 动态树'),
 '26656':unit(6,'01 数学基础'),'21094':unit(6,'02 整数分解与筛法'),'21289':unit(6,'03 同余、逆元与中国剩余定理'),'21791':unit(6,'04 排列组合'),'22529':unit(6,'05 容斥原理'),'22769':unit(6,'06 积性函数与莫比乌斯反演'),'24157':unit(6,'07 矩阵与高斯消元'),'24710':unit(6,'08 生成函数'),'26757':unit(6,'08 生成函数'),'26013':unit(6,'09 FFT 与 NTT'),
 '27589':unit(6,'10 KMP'),'28576':unit(6,'11 字符串哈希'),'28737':unit(6,'12 字典树'),'29086':unit(6,'13 AC 自动机'),'33548':unit(6,'14 回文算法'),'34974':unit(6,'15 后缀数组'),'37092':unit(6,'16 后缀自动机'),'32183':unit(6,'17 组合博弈'),'34655':unit(6,'17 组合博弈'),
 '27249':unit(7,'01 平面几何基础'),'27675':unit(7,'02 极角排序'),'28513':unit(7,'03 凸包'),'28770':unit(7,'03 凸包'),'29764':unit(7,'04 半平面交'),'36088':unit(7,'05 扫描线'),'40275':unit(7,'06 圆'),
 'collection-1266':unit(8,'01 基础综合练习'),'52826':unit(8,'02 专题综合练习'),
};
const CHAPTERS=['模拟、枚举与贪心','递归与分治','二分、三分与分数规划','栈、队列与单调结构','堆与并查集','搜索与剪枝','线性、背包与区间 DP','树形与状态压缩 DP','最短路与最小生成树','数学基础','树状数组与线段树','树上倍增与 LCA'];
const CHAPTER_UNITS=['19851','21763','22353','22669','22904','23156','24213','25022','26077','26656','26896','27836'];
const CHINESE=['一','二','三','四','五','六','七','八','九','十','十一','十二'];
const clean=value=>String(value||'').normalize('NFKC').replace(/[：:,，、\s]+$/g,'').replace(/二位费用/g,'二维费用').replace(/01\s*背包/g,'0/1 背包').replace(/01\s*分数规划/g,'0/1 分数规划').replace(/线性\s*dp/ig,'线性 DP').replace(/树[型形]\s*dp/ig,'树形 DP').replace(/状压\s*dp/ig,'状态压缩 DP').replace(/区间\s*dp/ig,'区间 DP').replace(/map\/set/ig,'Map 与 Set').replace(/stl/ig,'STL').trim();
const key=list=>list.id.replace(/^nowcoder-contest-/,'').replace(/^nowcoder-collection-/,'collection-');
const refKey=p=>p.problemId||String(p.url||p.pid).replace(/\/$/,'');

function numbered(items){
 const siblings=new Map();
 return items.map(item=>{
  const path=[];
  for(const raw of item.sections||[]){
   const title=clean(raw);if(!title)continue;
   const parent=path.join('\0');if(!siblings.has(parent))siblings.set(parent,new Map());
   const names=siblings.get(parent);if(!names.has(title))names.set(title,names.size+1);
   path.push(`${String(names.get(title)).padStart(2,'0')} ${title}`);
  }
  return {...item,originalSections:item.originalSections||item.sections||[],sections:path};
 });
}

export function normalizeNowcoderChapters(list){
 if(list.id!=='nowcoder-926597')return list;
 let chapter=0;
 const problems=list.problems.map(item=>{
  let sections=[...(item.originalSections||item.sections||[])];
  const found=sections.findIndex(s=>/^第[一二三四五六七八九十]+章/.test(s));
  if(found>=0){const match=sections[found].match(/^第([一二三四五六七八九十]+)章/);chapter=CHINESE.indexOf(match[1]);sections=sections.slice(found+1);}
  if(chapter===2&&clean(sections[0])==='二分答案')sections=['二分',...sections];
  return {...item,originalSections:item.originalSections||item.sections||[],nowcoderChapter:chapter,sections:[CHAPTERS[chapter],...sections.map(clean)]};
 });
 return {...list,learningSequence:true,problems:numbered(problems)};
}

function placement(list,item){
 if(list.id==='nowcoder-926597')return UNITS[CHAPTER_UNITS[item.nowcoderChapter||0]];
 if(list.id==='nowcoder-817596-sequential-verified')return UNITS['18839'];
 if(UNITS[key(list)])return UNITS[key(list)];
 const text=(item.originalSections||item.sections||[]).join(' ');
 const map=[[/顺序/,'18839'],[/选择|分支/,'19304'],[/循环/,'19305'],[/数组|字符串/,'19306'],[/函数|递归/,'19859'],[/STL|stl/,'19850'],[/模拟|枚举|贪心/,'19851'],[/分治/,'21763'],[/二分|三分/,'22353'],[/单调|队列|堆栈/,'22669'],[/并查|优先/,'22904'],[/搜索/,'23156'],[/动态规划1/,'24213'],[/动态规划2/,'25022'],[/最短|图论/,'26077'],[/数学/,'26656'],[/线段树|树状/,'26896']];
 return UNITS[map.find(([pattern])=>pattern.test(text))?.[1]]||unit(8,'01 基础综合练习');
}

export const nowcoderUnitId=path=>'nowcoder-curriculum:unit:'+encodeURIComponent(path.join('/'));

export function buildNowcoderCurriculum(lists,rows=[]){
 const byId=new Map(lists.map(list=>[list.id,list])),parents=new Map();
 for(const id of ROOTS)for(const child of byId.get(id)?.children||[])parents.set(child,id);
 const byProblem=new Map(),byUrl=new Map(),urlKey=url=>String(url||'').replace(/[?#].*$/,'').replace(/\/$/,'');
 for(const row of rows){for(const id of [row.id,...row.aliasIds||[]])byProblem.set(id,row);if(row.url)byUrl.set(urlKey(row.url),row);}
 const identity=item=>(byProblem.get(item.problemId)||byUrl.get(urlKey(item.url)))?.id||refKey(item);
 const inherited=new Set();for(const id of byId.get(ROOTS[0])?.children||[])for(const p of byId.get(id)?.problems||[])inherited.add(refKey(p));
 const groups=new Map(),standalone=[];
 for(const list of lists){
  if(list.id===ROOTS[2])continue;
  if(!ROOTS.includes(list.id)&&!parents.has(list.id)&&!UNITS[key(list)]&&list.id!=='nowcoder-817596-sequential-verified'){
   standalone.push({...list,catalogHidden:false,topicPath:['牛客'],directoryRow:false});continue;
  }
  for(const item of list.problems||[]){
   if(list.id===ROOTS[0]&&inherited.has(refKey(item)))continue;
   const path=placement(list,item),groupId=JSON.stringify(path);
   if(!groups.has(groupId))groups.set(groupId,{list,path,legacyIds:new Set(),sources:new Set(),problems:new Map()});
   const group=groups.get(groupId),id=identity(item),previous=group.problems.get(id);
   group.legacyIds.add(`nowcoder-curriculum:${list.id}:${encodeURIComponent(path.join('/'))}`);group.sources.add(list.id);
   if(previous){previous.sourceListIds=[...new Set([...previous.sourceListIds,list.id])];continue;}
   group.problems.set(id,{...item,originalSections:item.originalSections||item.sections||[],sections:[],membershipSource:item.membershipSource||list.url,sourceListId:list.id,sourceListIds:[list.id]});
  }
 }
 const curriculum=[];
 for(const {list,path,legacyIds,sources,problems} of groups.values()){
  const name=path[1].replace(/^\d+\s+/,''),order=NOWCODER_STAGES.indexOf(path[0])*100+Number.parseInt(path[1],10);
  curriculum.push({...list,id:nowcoderUnitId(path),legacyIds:[...legacyIds],title:name,displayTitle:name,sourceListId:list.id,sourceListIds:[...sources],sourceLabel:'',
   originalTitle:list.originalTitle||list.title,topicPath:['牛客',path[0]],catalogHidden:false,directoryRow:false,hideSectionFolders:true,learningSequence:true,aggregateChildren:false,children:[],problems:[...problems.values()],problemCount:problems.size,curriculumOrder:order});
 }
 const visible=new Set(standalone.map(list=>list.id));
 return [...lists.filter(list=>!visible.has(list.id)).map(list=>({...list,catalogHidden:true})),...standalone,...curriculum];
}
