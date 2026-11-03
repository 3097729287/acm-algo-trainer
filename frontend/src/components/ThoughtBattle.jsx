import {useEffect,useState} from 'react';
import {ArrowLeft,Check,Clock,History,LoaderCircle,RefreshCw,Send,Swords,Trophy,Upload,UserRound,WifiOff,X} from 'lucide-react';
import ProfileBadge from './ProfileBadge.jsx';
import SolutionMarkdown from './SolutionMarkdown.jsx';
import usePublicAvatar from '../lib/usePublicAvatar.js';

const dimensions=[['correctness','正确性',40],['complexity','复杂度',20],['edge_case','边界与反例',15],['constant','常数与工程可行性',10],['clarity','表达清晰',10],['innovation','创新',5]];
export const duelTime=value=>`${Math.floor(value/60).toString().padStart(2,'0')}:${(value%60).toString().padStart(2,'0')}`;
function Player({player,api,ownAvatar,own,submitted,score,change,winner}){
 const image=usePublicAvatar(api,player.owner,own?null:player.avatarHash);
 return <article className={'thought-player'+(own?' is-self':'')+(winner?' is-winner':'')}>
  <span className="thought-avatar">{(own?ownAvatar:image)?<img src={own?ownAvatar:image} alt=""/>:<UserRound size={28}/>}</span>
  <span className="thought-player-name"><strong>{player.nickname}</strong><small>{player.rating}{change!==undefined&&<b className={change<0?'is-loss':''}>{change>0?'+':''}{change}</b>}</small></span>
  {!player.online&&<WifiOff size={16} aria-label="已掉线"/>}
  {score!==undefined?<b className="thought-total">{score}<small>/ 100</small></b>:submitted&&<Check size={21} aria-label="已交卷"/>}
 </article>;
}
function Result({room,owner,api,avatar,onBack}){
 const verdict=room.verdict;
 return <div className="thought-result">
  <div className="thought-result-title"><Trophy size={24}/><h2>{room.judgeFailed?'本局平局':!room.winner?'平局':room.winner===owner?'本局获胜':'本局结束'}</h2><button className="icon-button" type="button" aria-label="返回匹配" onClick={onBack}><ArrowLeft size={20}/></button></div>
  <p role="status">{verdict.reason}</p>
  {!room.judgeFailed&&<div className="thought-score-grid">{room.players.map((p,i)=>{
   const score=verdict[i===0?'player_a':'player_b'];
   return <section key={p.owner} className="thought-score-card" aria-label={`${p.nickname}的评分`}>
    <Player player={p} api={api} own={p.owner===owner} ownAvatar={avatar} score={score.final_score} change={room.ratingChanges[p.owner]} winner={room.winner===p.owner}/>
    <dl className="thought-dimensions">{dimensions.map(([key,label,max])=><div key={key}><dt>{label}</dt><dd><progress value={score.scores[key]} max={max} aria-label={`${label}得分`}/><span>{score.scores[key]} / {max}</span></dd></div>)}</dl>
    <p>{score.feedback}</p>{score.fatal_flaws.length>0&&<ul>{score.fatal_flaws.map((flaw,index)=><li key={index}>{flaw}</li>)}</ul>}
    <details><summary>作答思路</summary><SolutionMarkdown text={p.text||'未作答'}/></details>
   </section>;
  })}</div>}
  {room.judgeFailed&&<div className="thought-score-grid">{room.players.map(p=><section key={p.owner} className="thought-score-card"><Player player={p} api={api} own={p.owner===owner} ownAvatar={avatar} change={0}/><details><summary>作答思路</summary><SolutionMarkdown text={p.text||'未作答'}/></details></section>)}</div>}
  {!room.judgeFailed&&verdict.problem_analysis.optimal_algorithm&&<details className="thought-analysis"><summary>题目分析</summary><p>{verdict.problem_analysis.optimal_algorithm}</p><p>{verdict.problem_analysis.optimal_time_complexity} · {verdict.problem_analysis.optimal_space_complexity}</p><ul>{verdict.problem_analysis.key_edges.map((edge,i)=><li key={i}>{edge}</li>)}</ul></details>}
 </div>;
}
export default function ThoughtBattle({thought,range,account,profile,growth,avatar}){
 const {state,error,busy,saving,uncertain,act,reload,clock,editor,setText,loadServer,keepLocal,api}=thought;
 const [tick,setTick]=useState(0),[history,setHistory]=useState(null),[record,setRecord]=useState(null),[historyError,setHistoryError]=useState(''),[historyBusy,setHistoryBusy]=useState(false),[original,setOriginal]=useState(false);
 useEffect(()=>{const timer=setInterval(()=>setTick(v=>v+1),250);return()=>clearInterval(timer);},[]);
 useEffect(()=>{setOriginal(false);setHistory(null);setRecord(null);setHistoryError('');},[state?.owner]);
 const room=state?.match,owner=state?.owner,now=clock.current?clock.current.server+performance.now()-clock.current.local:state?.serverNow??0;
 const me=room?.players.find(p=>p.owner===owner),queued=state?.status==='queued',remaining=room?Math.max(0,Math.ceil((room.deadline-now)/1000)):0;
 const locked=state?.status!=='active'||me?.submittedAt!==null||remaining===0||uncertain;
 const nickname=account?.nickname||profile?.nickname||'—';
 useEffect(()=>{if(room&&room.status!=='finished'){setHistory(null);setRecord(null);}},[room?.id,room?.status]);
 const showHistory=async id=>{
  if(!api||historyBusy)return;setHistoryBusy(true);setHistoryError('');
  try{const result=await api('pk/v1/history'+(id?'/'+id:''));if(result.owner!==owner)return;id?setRecord(result.match):setHistory(result.records);}
  catch(issue){setHistoryError(issue.message);}finally{setHistoryBusy(false);}
 };
 if(record)return <Result room={record} owner={owner} api={api} avatar={avatar} onBack={()=>setRecord(null)}/>;
 if(history)return <div className="thought-history"><header><h2>对局记录</h2><button type="button" className="icon-button" aria-label="返回思维对决" onClick={()=>setHistory(null)}><ArrowLeft size={20}/></button></header>{history.length===0?<p>暂无对局记录</p>:history.map(item=><button key={item.id} type="button" className="thought-history-row" disabled={historyBusy} onClick={()=>showHistory(item.id)}><strong>{item.problem}</strong><span>{item.judgeFailed||!item.winner?'平局':item.winner===owner?'获胜':'结束'}</span><time>{new Date(item.finishedAt).toLocaleString()}</time><b>{item.ratingChange>0?'+':''}{item.ratingChange}</b></button>)}{historyError&&<p role="alert" className="connection-error">{historyError}</p>}</div>;
 if(room?.status==='finished')return <Result room={room} owner={owner} api={api} avatar={avatar} onBack={()=>act('dismiss')}/>;
 return <>
  {!room?<div className={'duel-lobby'+(queued?' is-queued':'')}>
   {queued&&<div className="duel-queue-status" role="status"><LoaderCircle size={18} className="progress-spin"/><span>匹配中</span><time role="timer" aria-label="已匹配时间">{duelTime(Math.max(0,Math.floor((now-state.queuedAt)/1000)))}</time></div>}
   <div className="duel-lobby-identity"><ProfileBadge compact={false} growth={growth} avatar={avatar} nickname={nickname} showXp={false}/><div className="thought-rating" aria-label={`思维积分 ${state?.rating??1000}`}><Trophy size={23}/>{state?.rating??1000}</div></div>
   <div className="duel-lobby-actions">{queued?<div className="duel-find duel-queued" role="status"><LoaderCircle size={19} className="progress-spin"/><span>匹配中</span><button className="icon-button duel-cancel" type="button" aria-label="取消匹配" title="取消匹配" disabled={busy} onClick={()=>act('cancel')}><X size={18}/></button></div>:<button className="primary duel-find" type="button" aria-label="开始思维匹配" disabled={busy||!state?.enabled} onClick={()=>act('join',{minDifficulty:range.min,maxDifficulty:range.max})}><Swords size={21}/><span>寻找对局</span></button>}<button type="button" className="icon-button" aria-label="对局记录" title="对局记录" disabled={!state||queued||historyBusy} onClick={()=>showHistory()}><History size={20}/></button></div>
   {state&&!state.enabled&&<p className="duel-lobby-result" role="status">思维对决服务尚未启用</p>}
  </div>:room.status==='countdown'?<section className="thought-countdown duel-ready-dialog" role="alert" aria-label="已找到对手"><Swords size={44}/><h2>已找到对手</h2><div className="thought-opponents">{room.players.map(p=><Player key={p.owner} player={p} api={api} own={p.owner===owner} ownAvatar={avatar}/>)}</div><time role="timer" aria-label="开局倒计时">{Math.max(0,Math.ceil((room.startedAt-now)/1000))}</time></section>:<div className={'thought-game'+(remaining<=180?' is-urgent':'')}>
   <div className="thought-matchbar"><Player player={room.players[0]} api={api} own={room.players[0].owner===owner} ownAvatar={avatar} submitted={room.players[0].submittedAt!==null}/><div className="thought-clock" role="timer" aria-label="思维对决剩余时间">{room.status==='judging'?<><LoaderCircle size={20} className="progress-spin"/><span>AI 裁判中</span></>:<><Clock size={19}/><time>{duelTime(remaining)}</time></>}</div><Player player={room.players[1]} api={api} own={room.players[1].owner===owner} ownAvatar={avatar} submitted={room.players[1].submittedAt!==null}/></div>
   <div className="thought-workspace"><section className="thought-statement" aria-label="对战题目"><header><strong>{room.problem.title}</strong><span>{room.problem.difficulty}</span>{room.problem.originalMarkdown!==room.problem.markdown&&<button type="button" className="icon-button" aria-label={original?'查看中文题面':'查看原题面'} title={original?'查看中文题面':'查看原题面'} onClick={()=>setOriginal(v=>!v)}><RefreshCw size={17}/></button>}</header><SolutionMarkdown text={original?room.problem.originalMarkdown:room.problem.markdown}/></section>
    <section className="thought-answer" aria-label="作答思路"><header><strong>作答思路</strong><span aria-live="polite">{saving?'保存中':editor?.dirty?'待保存':me?.submittedAt!==null?'已交卷':'已保存'}</span></header><p>请独立完成，提交后不可修改。</p><textarea aria-label="思维对决答卷" value={editor?.text||''} disabled={locked||busy} onChange={e=>setText(e.target.value)} spellCheck={false}/><footer><span aria-label="答卷字数">{[...(editor?.text||'')].length} / 2000</span>{editor?.conflict?<><span role="alert">答卷已在其他窗口更新</span><button type="button" className="icon-button" aria-label="保留本机答卷" title="保留本机答卷" onClick={keepLocal}><Upload size={19}/></button><button type="button" className="icon-button" aria-label="载入服务端答卷" title="载入服务端答卷" onClick={loadServer}><RefreshCw size={19}/></button></>:<button type="button" className="icon-button primary" aria-label="提交思路" title="提交思路" disabled={locked||busy||saving||uncertain} onClick={()=>act('submit')}><Send size={20}/></button>}</footer>{me?.submittedAt!==null&&room.status==='active'&&<p role="status">已交卷，等待对手作答或时间结束</p>}</section>
   </div>
  </div>}
  {(error||historyError)&&<p className="connection-error" role="alert">{error||historyError}</p>}
 </>;
}
