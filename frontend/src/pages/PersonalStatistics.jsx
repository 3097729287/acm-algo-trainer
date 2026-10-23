import {useEffect,useState} from 'react';
import {ArrowRight,CalendarDays,ChartNoAxesCombined,Clock,Flame,Mountain,Timer} from 'lucide-react';
import Tooltip from '@/components/Tooltip.jsx';

const number=value=>value==null?'—':Number(value).toLocaleString('zh-CN');
function duration(seconds){if(seconds==null)return '未记录';const minutes=Math.floor(seconds/60);return minutes>=60?`${Math.floor(minutes/60)} 小时 ${minutes%60} 分钟`:`${minutes} 分钟`;}
export default function PersonalStatistics({api,insights,account,onTrain}) {
  const [usage,setUsage]=useState(null),[error,setError]=useState('');
  useEffect(()=>{let alive=true;const refresh=()=>api('usage').then(value=>{if(alive){setUsage(value);setError('');}}).catch(()=>{if(alive)setError('使用时长暂未读取');});refresh();const timer=setInterval(refresh,30000);return()=>{alive=false;clearInterval(timer);};},[api]);
  const summary=insights?.summary||{},stats=insights?.personalStatistics||{},hardest=stats.hardestSolved;
  const registration=account?.createdAt&&Number.isFinite(Date.parse(account.createdAt))?new Date(account.createdAt).toLocaleDateString('zh-CN',{timeZone:'Asia/Shanghai'}):'—';
  const facts=[
    ['AC',number(summary.totalSolved??summary.officialSolved),'累计通过',null],
    [Flame,number(summary.longestStreak),'最长连续训练','按正式提交日期统计连续训练天数。'],
    [Flame,number(stats.longestAcStreak),'最长连续 AC','按北京时间统计连续有原站 AC 的日期。'],
    [Mountain,number(stats.maxDailyAc),'最高单日 AC',stats.maxDailyAcDate||null],
    [CalendarDays,number(summary.activeDays),'活跃天数',null],
    [CalendarDays,registration,'注册时间',null],
    [Clock,duration(usage?.totalSeconds),'累计使用时长','仅统计有记录的前台使用时间；历史未记录时段不推算。'],
    [Timer,duration(usage?.maxDailySeconds),'最长单日使用时长',usage?.maxDailyDate||'仅统计有记录的前台使用时间。'],
  ];
  return <section className="personal-statistics" aria-label="个人数据统计"><h2><ChartNoAxesCombined size={19}/>数据统计</h2><div className="personal-stat-grid">{facts.map(([Icon,value,label,tip])=><div className="personal-stat" key={label}><span className="personal-stat-label">{typeof Icon==='string'?<b className="personal-stat-ac">{Icon}</b>:<Icon size={18}/>}<span>{label}</span>{tip&&<Tooltip label={`${label}说明`} text={tip}/>}</span><strong>{value}</strong></div>)}</div><div className="personal-hardest"><span><Mountain size={18}/>通过的最难题目<Tooltip text="在已确认原站 AC 且题库有难度记录的题目中统计。"/></span>{hardest?<button type="button" disabled={!onTrain} onClick={()=>onTrain?.(hardest.id)}><strong>{hardest.title}</strong><span>{hardest.contest} · {hardest.problem}</span><b>{hardest.difficulty}</b><ArrowRight size={15}/></button>:<span className="progress-muted">暂无已知难度的原站 AC 记录</span>}</div>{error&&<p className="progress-muted" role="status">{error}</p>}</section>;
}
