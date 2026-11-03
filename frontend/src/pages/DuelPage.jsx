import {useEffect,useState} from 'react';
import {ArrowLeft,Check,Clock,ExternalLink,LoaderCircle,Play,RefreshCw,Swords,WifiOff,X} from 'lucide-react';
import './DuelPage.css';
import ProfileBadge from '../components/ProfileBadge.jsx';
import TierIcon from '../components/TierIcon.jsx';
export default function DuelPage({duel,rows,onTrain,account,profile,growth,avatar}){
 const {state,error,busy,act,reload,clock}=duel,[tick,setTick]=useState(0);
 useEffect(()=>{void reload();},[reload]);
 useEffect(()=>{const timer=setInterval(()=>setTick(value=>value+1),1000);return()=>clearInterval(timer);},[]);
 const room=['active','finished'].includes(state?.status)?state.match:null,now=clock.current?clock.current.server+performance.now()-clock.current.local:state?.serverNow;
 const remaining=room?Math.max(0,Math.ceil((room.deadline-now)/1000)):0;
 const row=room&&rows.find(item=>item.id===room.problem.libraryId||item.url===room.problem.url);
 const queued=state?.status==='queued',ready=state?.status==='ready',cancelled=state?.status==='cancelled';
 const elapsed=queued?Math.max(0,Math.floor((now-state.queuedAt)/1000)):0;
 const nickname=account?.nickname||profile?.nickname||'—',rank=growth?.ranked;
 const time=value=>`${Math.floor(value/60).toString().padStart(2,'0')}:${(value%60).toString().padStart(2,'0')}`;
 return <section className="list-page duel-page" aria-label="对战">
  <header className="duel-toolbar"><Swords size={22}/><strong>对战</strong><span>800–1500</span><button type="button" className="icon-button" aria-label="刷新对战" disabled={busy} onClick={reload}><RefreshCw size={17}/></button></header>
  {!room?<div className={'duel-lobby'+(queued?' is-queued':'')}>
   {(queued||ready)&&<div className="duel-queue-status" role="status"><LoaderCircle size={18} className="progress-spin"/><span>{ready?'已找到对手':'匹配中'}</span>{queued&&<time role="timer" aria-label="已匹配时间">{time(elapsed)}</time>}</div>}
   <div className="duel-lobby-identity"><ProfileBadge compact={false} growth={growth} avatar={avatar} nickname={nickname} showXp={false}/>{rank&&<div className="duel-lobby-rank"><TierIcon rank={rank} size={76}/></div>}</div>
   <div className="duel-lobby-actions">{queued?<><button type="button" className="duel-find" disabled aria-label="正在寻找对局"><LoaderCircle size={19} className="progress-spin"/><span>匹配中</span></button><button type="button" className="icon-button duel-cancel" aria-label="取消匹配" title="取消匹配" disabled={busy} onClick={()=>act('cancel',{ticket:state.ticket})}><X size={20}/></button></>:<button type="button" className="primary duel-find" aria-label="开始匹配" disabled={busy||ready||!state} onClick={()=>act('join')}><Swords size={21}/><span>{cancelled?'重新寻找对局':'寻找对局'}</span></button>}</div>
   {cancelled&&<p className="duel-lobby-result" role="status">{state.match.cancelReason==='timeout'?'接受对局超时':state.match.cancelledBy===state.owner?'已拒绝本轮对局':'对手已拒绝本轮对局'}</p>}
  </div>:<>
   <div className="duel-clock" role="timer" aria-label="对战剩余时间"><Clock size={20}/>{Math.floor(remaining/60).toString().padStart(2,'0')}:{(remaining%60).toString().padStart(2,'0')}</div>
   <div className="duel-players">{room.players.map(player=><article key={player.owner} className={'duel-player'+(room.winner===player.owner?' duel-winner':'')}><strong>{player.handle}</strong>{player.online?null:<WifiOff size={16} aria-label="已掉线"/>}<b>{player.acceptedAt?<Check size={32}/>:player.attempts}</b><small>{player.acceptedAt?`${Math.max(0,Math.floor((player.acceptedAt-room.startedAt)/1000))}s`:'—'}</small>{player.syncError&&<WifiOff size={16} aria-label="成绩待核验"/>}</article>)}</div>
   <div className="duel-problem"><strong>{room.problem.title}</strong><span>{room.problem.difficulty}</span>{row&&<button type="button" className="icon-button" aria-label="进入对战题目" onClick={()=>onTrain(row.id)}><Play size={21}/></button>}<a className="icon-button" aria-label="查看原题" href={room.problem.url} target="_blank" rel="noreferrer"><ExternalLink size={18}/></a></div>
   {room.status==='finished'&&<button type="button" className="icon-button duel-again" aria-label="返回匹配" disabled={busy} onClick={()=>act('dismiss',{matchId:room.id})}><ArrowLeft size={20}/></button>}
  </>}
  {error&&<p className="connection-error" role="alert">{error}</p>}
 </section>;
}
