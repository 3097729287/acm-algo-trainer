const LUOGU_LEVELS=['未定级','入门','普及-','普及','普及+/提高-','提高','提高+/省选-','省选/NOI-','NOI/NOI+/CTS'];
import {lectureCurriculum} from './learningCurriculum.js';
export function difficultyPresentation(row={},mode='number') {
  if(row.difficultyHidden)return {label:'—',kind:'hidden'};
  const value=Number(row.difficulty),known=row.difficulty!=null&&Number.isFinite(value)&&value>0;
  const source=String(row.difficultySource||'');
  const level=known?(value<1000?'入门':value<1400?'基础':value<1800?'进阶':value<2200?'困难':'高难'):'待评估';
  const number=known?String(Math.round(value/100)*100):'—';
  const label=text=>mode==='text'?text:number;
  const official=(row.platform==='Codeforces'||row.platform==='codeforces')
    && row.difficultyEstimated!==true && /官方|official/i.test(source) && !/未提供|无官方/.test(source);
  if(official&&known)return {label:label(level),kind:'official',scale:'CF'};
  const single=row.source==='luogu-training'||row.problemKind==='standalone';
  if(single&&['洛谷','luogu'].includes(row.platform)) {
    const native=row.nativeDifficultyLabel||row.nativeDifficulty?.label;
    if(native)return {label:label(String(native)),kind:'native',scale:'洛谷'};
    const level=Number(row.nativeDifficulty);
    if(Number.isInteger(level)&&LUOGU_LEVELS[level])return {label:label(LUOGU_LEVELS[level]),kind:'native',scale:'洛谷'};
  }
  if(!known)return {label:mode==='text'?'待评估':'—',kind:'unknown'};
  return {label:label(level),kind:'estimate',scale:'训练参考'};
}

export function lessonLevel(lesson={}) {
  return lectureCurriculum(lesson).levelLabel;
}
