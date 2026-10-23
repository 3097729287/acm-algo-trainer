import {useEffect,useState} from 'react';
import {ArrowUpRight,CalendarClock,Check,CloudOff,LoaderCircle,RefreshCw,TriangleAlert} from 'lucide-react';
import Tooltip from '@/components/Tooltip.jsx';
import {trainingDay} from '@/lib/trainingDate.js';
import './ContestCalendar.css';

const dayFormat=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'long',day:'numeric'});
const weekdayFormat=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',weekday:'short'});
const timeFormat=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',hour12:false});
const labels={codeforces:'Codeforces',atcoder:'AtCoder',nowcoder:'牛客',luogu:'洛谷'};
export default function ContestCalendar({api}) {
 const [snapshot,setSnapshot]=useState(null),[error,setError]=useState(''),[revision,setRevision]=useState(0),[now,setNow]=useState(Date.now);
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer);},[]);
 useEffect(()=>{let stopped=false,timer;async function load(force=false){try{const value=await api('contest-calendar'+(force?'?refresh=1':''));if(stopped)return;setSnapshot(value);setError('');if(value.refreshing)timer=setTimeout(()=>load(),700);}catch(issue){if(!stopped)setError(issue.message);}}load(revision>0);return()=>{stopped=true;clearTimeout(timer);};},[api,revision]);
 const today=trainingDay(now),tomorrow=trainingDay(new Date(`${today}T00:00:00+08:00`).getTime()+86400000);
 const groups=new Map();for(const contest of snapshot?.contests||[]){const day=trainingDay(contest.startAt);if(!groups.has(day))groups.set(day,[]);groups.get(day).push(contest);}
 return <section className="contest-calendar" aria-label="即将开始的比赛"><div className="contest-calendar-toolbar"><div className="contest-calendar-providers">{snapshot?.providers?.map(provider=>{const Icon=provider.status==='refreshing'?LoaderCircle:provider.status==='error'?TriangleAlert:provider.status==='offline'?CloudOff:Check;return <Tooltip key={provider.platform} text={provider.error||`${provider.label} · ${provider.status==='refreshing'?'正在更新':provider.status==='offline'?'离线缓存':'已更新'}`}><span className={'calendar-provider '+provider.status}><Icon size={13} className={provider.status==='refreshing'?'spin':''}/>{provider.label}</span></Tooltip>;})}</div><Tooltip text="北京时间"><span className="contest-calendar-zone">UTC+8</span></Tooltip><Tooltip text="刷新赛程"><button type="button" className="icon-button" aria-label="刷新赛程" disabled={snapshot?.refreshing} onClick={()=>setRevision(value=>value+1)}><RefreshCw size={16} className={snapshot?.refreshing?'spin':''}/></button></Tooltip></div>
 {error&&<p role="alert">{error}</p>}{[...groups].map(([day,contests])=>{const date=new Date(`${day}T00:00:00+08:00`);return <div className="contest-calendar-day" key={day}><h3>{(day===today||day===tomorrow)&&<strong>{day===today?'今天':'明天'}</strong>}<time dateTime={day}>{dayFormat.format(date)}</time><span>{weekdayFormat.format(date)}</span></h3>{contests.map(contest=><a className="contest-calendar-row" key={contest.id} href={contest.url} target="_blank" rel="noreferrer"><time dateTime={contest.startAt}>{timeFormat.format(new Date(contest.startAt))}</time><strong>{contest.title}</strong><span>{labels[contest.platform]}</span><Tooltip text={`时长 ${Math.round((new Date(contest.endAt)-new Date(contest.startAt))/60000)} 分钟`}><CalendarClock size={17}/></Tooltip><ArrowUpRight size={15}/></a>)}</div>;})}
 {!groups.size&&<div className="contest-calendar-empty">{!snapshot||snapshot.refreshing?<><LoaderCircle size={23} className="spin"/><span role="status">正在读取赛程</span></>:<><CalendarClock size={25}/><span>{snapshot.offline?'离线，暂无缓存赛程':snapshot.providers?.every(provider=>provider.status==='error')?'赛程暂不可用':'暂无即将开始的比赛'}</span></>}</div>}</section>;
}
