import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Award, Clock3, ImagePlus, Mountain, Palette, Sparkles, Target, Trophy, X } from 'lucide-react';
import RankingMedal from './RankingMedal.jsx';
import TitleMedals from './TitleMedals.jsx';
import '../styles/decorations.css';

export function AppearanceSettings({ prefs, setPrefs, onError }) {
  const input = useRef(null);
  const [hasImage, setHasImage] = useState(() => Boolean(localStorage.getItem('tb.appearance.background')));
  async function imageSelected(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 12 * 1024 * 1024) throw new Error('请选择 12 MB 以内的 PNG、JPEG 或 WebP 图片');
      const bitmap = await createImageBitmap(file);
      const scale = Math.min(1, 1920 / Math.max(bitmap.width, bitmap.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(bitmap.width * scale)); canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height); bitmap.close();
      const value = canvas.toDataURL('image/jpeg', .8);
      localStorage.setItem('tb.appearance.background', value);
      document.documentElement.style.setProperty('--workspace-image', `url("${value}")`);
      setHasImage(true); setPrefs(previous => ({ ...previous, backdrop: 'custom' }));
    } catch (issue) { onError?.(issue.message || '背景图片未能保存，请换一张较小的图片'); }
    finally { event.target.value = ''; }
  }
  return <section className="appearance-studio" aria-label="工作台装饰"><h2><Palette size={18}/>工作台风格</h2>
    <p className="progress-small">边框、背景和小挂件均可单独选择，阅读区保持清晰。</p>
    <div className="style-preset-grid">{[
      ['minimal', '清简', '干净的实色面板'], ['outlined', '线框', '清晰边框与细节'], ['aurora', '极光', '柔和渐变与光点'], ['blueprint', '蓝图', '工程网格与标尺'],
    ].map(([id, title, note]) => <button type="button" key={id} aria-pressed={prefs.panelStyle === id} className={`style-preset style-${id}`} onClick={() => setPrefs(previous => ({ ...previous, panelStyle: id }))}><i aria-hidden="true"/><strong>{title}</strong><small>{note}</small></button>)}</div>
    <div className="settings-row"><div><strong>页面背景</strong><small>使用静态图案，减少动画开销</small></div><select aria-label="页面背景" value={prefs.backdrop} onChange={event => setPrefs(previous => ({ ...previous, backdrop: event.target.value }))}>{[['none','纯色'],['aurora','夜空极光'],['grid','细线网格'],['sunset','落日余晖'],...(hasImage ? [['custom','我的图片']] : [])].map(([id,name]) => <option value={id} key={id}>{name}</option>)}</select></div>
    <label className="settings-row appearance-opacity"><div><strong>面板不透明度</strong><small>降低后可透出更多背景</small></div><input type="range" aria-label="面板不透明度" min="25" max="100" step="1" value={prefs.panelOpacity ?? 76} onChange={event => setPrefs(previous => ({...previous,panelOpacity:Number(event.target.value)}))}/><output>{prefs.panelOpacity ?? 76}%</output></label>
    <div className="appearance-image-actions"><input ref={input} hidden type="file" accept="image/png,image/jpeg,image/webp" onChange={imageSelected}/><button className="secondary" onClick={() => input.current.click()}><ImagePlus size={15}/>选择背景图片</button>{hasImage && <button className="text-button" onClick={() => { localStorage.removeItem('tb.appearance.background'); document.documentElement.style.removeProperty('--workspace-image'); setHasImage(false); setPrefs(previous => ({...previous, backdrop:'none'})); }}><X size={14}/>清除图片</button>}<small>图片仅保存在本机，不上传到账号。</small></div>
    <label className="settings-row"><div><strong>训练小挂件</strong><small>显示专注时钟、训练进度与简约山景</small></div><input className="toggle" type="checkbox" aria-label="训练小挂件" checked={prefs.widgets} onChange={event => setPrefs(previous => ({...previous, widgets:event.target.checked}))}/></label>
  </section>;
}

export function TrainingPulse({ insights, workspace }) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const tick = () => { if (!document.hidden) setNow(new Date()); }; const id = setInterval(tick, 60000); document.addEventListener('visibilitychange',tick); return () => {clearInterval(id); document.removeEventListener('visibilitychange',tick);}; }, []);
  const summary = insights?.summary || {}, tasks = insights?.dailyTasks?.tasks || [];
  const remaining = tasks.filter(task => !task.completed && (task.progress || 0) < (task.target || 1)).length;
  const activity = new Map((insights?.activity || []).map(item=>[item.date,item.officialAccepted || 0]));
  const date = new Date(now.toLocaleDateString('en-CA',{timeZone:'Asia/Shanghai'})+'T00:00:00Z');
  const week = Array.from({length:7},(_,index)=>{const day=new Date(+date-(6-index)*86400000),key=day.toISOString().slice(0,10);return {key,count:activity.get(key)||0,label:['日','一','二','三','四','五','六'][day.getUTCDay()]};});
  const peak=Math.max(1,...week.map(day=>day.count));
  return <aside className="training-pulse" aria-label="训练小挂件"><div className="pulse-clock"><Clock3 size={14}/><time>{now.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',hour12:false})}</time><small>保持专注，每一步都算数</small></div><Mountain className="pulse-mountain" size={84} strokeWidth={.8} aria-hidden="true"/><div className="pulse-facts"><span><Trophy size={14}/><b>{summary.totalSolved ?? summary.officialSolved ?? workspace?.summary?.accepted ?? '—'}</b>累计 AC</span><span><Target size={14}/>{remaining ? `${remaining} 项待完成` : '今日任务已完成'}</span></div><div className="pulse-week" aria-label="近七日原站通过"><div className="pulse-week-heading"><span>近七日</span><b>{week.reduce((sum,day)=>sum+day.count,0)} 题次</b></div><div className="pulse-week-bars">{week.map(day=><div key={day.key} title={`${day.key} · ${day.count} 题`}><i style={{'--day-height':`${Math.max(8,day.count/peak*100)}%`}} data-active={day.count>0}/><small>{day.label}</small></div>)}</div></div></aside>;
}

export function NextMilestone({ insights, onOpen }) {
  const achievements=(insights?.achievements || []).filter(item=>/^official-\d+$/.test(item.id)).sort((a,b)=>(a.target||0)-(b.target||0));
  const next=achievements.find(item=>!item.unlocked),earned=achievements.filter(item=>item.unlocked).at(-1);
  const solved=insights?.summary?.totalSolved ?? insights?.summary?.officialSolved ?? 0;
  const percent=next ? Math.min(100,solved/next.target*100) : 100;
  return <button className="next-milestone" aria-label="下一个成就目标" onClick={onOpen}><div><Award size={18}/><span>下一个里程碑</span><ArrowUpRight size={15}/></div><strong>{next?.title || next?.name || '继续创造新纪录'}</strong><p>{next ? `再完成 ${Math.max(0,next.target-solved)} 题` : `已累计 AC ${solved} 题`}</p><div className="milestone-meter" role="progressbar" aria-label="成就目标进度" aria-valuenow={Math.round(percent)} aria-valuemin={0} aria-valuemax={100}><i style={{width:`${percent}%`}}/></div><small>{next ? `${solved} / ${next.target}` : earned?.title || earned?.name || '每一步都算数'}{next?.rewardTitle ? ` · 称号「${next.rewardTitle.name}」` : next?.rewardXp ? ` · +${next.rewardXp} XP` : ''}</small>{insights?.equippedTitles?.length>0&&<TitleMedals titles={insights.equippedTitles} compact/>}</button>;
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
