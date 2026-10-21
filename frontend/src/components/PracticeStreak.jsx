import Tooltip from './Tooltip.jsx';
import {Flame} from 'lucide-react';
export const FLAME_STAGES=[1,2,4,7,15,30,60];
export default function PracticeStreak({days=0}) {
 const count=Math.max(0,Math.floor(Number(days)||0)),stage=Math.max(0,FLAME_STAGES.findLastIndex(value=>count>=value));
 return <Tooltip text={`连续练习 ${count} 天 · 每天至少完成一次正式提交，按北京时间统计。`}><span className={`practice-streak flame-stage-${stage}${count?'':' flame-inactive'}`} tabIndex={0} aria-label={`连续练习 ${count} 天`} data-stage={stage+1}>
 <Flame className="streak-flame" size={20} strokeWidth={1.8} aria-hidden="true"/><b>{count}</b></span></Tooltip>;
}
