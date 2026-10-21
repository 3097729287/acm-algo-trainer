import ThemedSelect from '@/components/ThemedSelect.jsx';
import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Award, Clock3, ImagePlus, Palette, Sparkles, Trophy, X } from 'lucide-react';
import RankingMedal from './RankingMedal.jsx';
import '../styles/decorations.css';
import '../styles/surfaces.css';

export { default as AppearanceSettings } from './VisualStyleSettings.jsx';

export function TopbarClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const tick = () => { if (!document.hidden) setNow(new Date()); };
    const timer = setInterval(tick, 15000);
    document.addEventListener('visibilitychange', tick);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', tick); };
  }, []);
  return <span className="topbar-clock" aria-label="北京时间" title={now.toLocaleDateString('zh-CN', {timeZone:'Asia/Shanghai',year:'numeric',month:'long',day:'numeric',weekday:'long'})}><Clock3 size={15}/><time dateTime={now.toISOString()}>{now.toLocaleTimeString('zh-CN', {timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',hour12:false})}</time></span>;
}

export function MiniLeaderboard({ api, onOpen }) {
  const [snapshot, setSnapshot] = useState(null);
  useEffect(() => {
    let active=true, pending=false;
    const read=async () => { if (pending || document.hidden) return; pending=true; try {const value=await api('leaderboard?period=daily'); if(active)setSnapshot(value);} catch {} finally {pending=false;} };
    read(); const timer=setInterval(read,60000); const visible=()=>read(); document.addEventListener('visibilitychange',visible);
    return ()=>{active=false;clearInterval(timer);document.removeEventListener('visibilitychange',visible);};
  }, [api]);
  const entries=(snapshot?.entries || []).slice(0,4), self=snapshot?.self;
  const own=(snapshot?.entries || []).find(item => item.userId===self?.userId);
  return <section className="progress-section mini-leaderboard" aria-label="今日排行榜速览"><div className="progress-section-heading"><h2><Trophy size={17}/>今日同行</h2><button className="progress-text-button" onClick={onOpen}>查看榜单<ArrowUpRight size={14}/></button></div>
    <p className="progress-small">{own?.count > 0 ? `你今天已通过 ${own.count} 题，当前第 ${own.rank} 名。` : '从今天的第一道题开始，和大家一起进步。'}</p>
    <div className="mini-board-list">{entries.length ? entries.map(item => <div key={item.userId} className={item.userId===self?.userId ? 'mini-board-self' : ''}><span className="mini-board-rank">{item.count > 0 && item.rank<=3 ? <RankingMedal period="daily" rank={item.rank}/> : item.rank}</span><div><strong>{item.nickname || '训练者'}</strong><small>{item.publicProgress ? `Lv.${item.publicProgress.level} · ${item.publicProgress.tier}` : '成长资料待同步'}</small></div><span><b>{item.count}</b>题</span></div>) : <div className="mini-board-empty"><Sparkles size={21}/><span>{snapshot ? '今天的榜单正在等待新的足迹' : '正在读取今日训练榜…'}</span></div>}</div>
    <div className="mini-board-footer"><Award size={14}/><span>每日前三名奖励 100 / 60 / 30 XP</span></div>
  </section>;
}
