const LUOGU_LEVELS=['未定级','入门','普及-','普及','普及+/提高-','提高','提高+/省选-','省选/NOI-','NOI/NOI+/CTS'];
export function difficultyPresentation(row={}) {
  if(row.difficultyHidden)return {label:'—',kind:'hidden'};
  const value=Number(row.difficulty),known=row.difficulty!=null&&Number.isFinite(value)&&value>0;
  const source=String(row.difficultySource||'');
  const official=(row.platform==='Codeforces'||row.platform==='codeforces')
    && row.difficultyEstimated!==true && /官方|official/i.test(source) && !/未提供|无官方/.test(source);
  if(official&&known)return {label:String(Math.round(value/100)*100),kind:'official',scale:'CF'};
  const single=row.source==='luogu-training'||row.problemKind==='standalone';
  if(single&&['洛谷','luogu'].includes(row.platform)) {
    const native=row.nativeDifficultyLabel||row.nativeDifficulty?.label;
    if(native)return {label:String(native),kind:'native',scale:'洛谷'};
    const level=Number(row.nativeDifficulty);
    if(Number.isInteger(level)&&LUOGU_LEVELS[level])return {label:LUOGU_LEVELS[level],kind:'native',scale:'洛谷'};
  }
  if(!known)return {label:'待评估',kind:'unknown'};
  const level=value<1000?'入门':value<1400?'基础':value<1800?'进阶':value<2200?'困难':'高难';
  return {label:`${level} · ${Math.round(value/100)*100}`,kind:'estimate',scale:'训练参考'};
}

export function lessonLevel(lesson={}) {
  const names=`${lesson.category||''} ${(lesson.tags||[]).join(' ')} ${lesson.concept||lesson.title||''}`;
  if(/语言与标准库|C\+\+.*语言/.test(names))return /lambda|迭代器|递归|捕获|生命周期|模板|unordered/.test(names)?'进阶':'基础';
  if(/莫比乌斯|生成函数|FFT|NTT|网络流|自动机|可持久化|多项式|虚树/.test(names))return '深入';
  return /模拟|枚举|前缀和|排序|二分|并查集|DFS|BFS|输入|输出/.test(names)?'基础':'进阶';
}
