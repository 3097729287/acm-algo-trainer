import {useCallback,useEffect,useRef,useState} from 'react';
import {ArrowDown,RefreshCw,Trophy} from 'lucide-react';
import PresenceLabel from './PresenceLabel.jsx';
import './DuelCommunity.css';
export default function DuelCommunity({api,owner,mode,revision}){
 const [view,setView]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),request=useRef(0),live=useRef(owner);live.current=owner;
 const load=useCallback(async(more=false)=>{
  if(!api||!owner)return;const seq=++request.current;setBusy(true);
  const next=more?view?.next:null;
  try{const answer=await api(`duel/board?mode=${mode}${next?'&before='+next.before+'&beforeId='+encodeURIComponent(next.beforeId):''}`);if(seq!==request.current||live.current!==owner||answer.owner!==owner||answer.mode!==mode)return;setView(previous=>more&&previous?.date===answer.date&&previous.mode===mode?{...answer,records:[...previous.records,...answer.records.filter(row=>!previous.records.some(old=>old.id===row.id))]}:answer);setError('');}
  catch(issue){if(seq===request.current&&live.current===owner)setError(issue.message);}
  finally{if(seq===request.current)setBusy(false);}
 },[api,owner,mode,view?.next]);
 const current=useRef(load);current.current=load;
 useEffect(()=>{request.current++;setView(null);setError('');void current.current();const timer=setInterval(()=>{if(!document.hidden)void current.current();},25000);return()=>{request.current++;clearInterval(timer);};},[api,owner,mode,revision]);
 if(!api)return null;
 const time=stamp=>new Date(stamp).toLocaleTimeString('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit'});
 return <section className="duel-community" aria-label="排位排行榜与对战记录">
  <section className="duel-ranking"><header><h2><Trophy size={17}/>排行榜</h2><button type="button" className="icon-button" aria-label="刷新排位排行榜" disabled={busy} onClick={()=>load()}><RefreshCw size={16}/></button></header>
   <table><thead><tr><th>名次</th><th>用户</th><th>排位分</th></tr></thead><tbody>{view?.entries.map(item=><tr key={item.userId} data-self={item.userId===owner}><td>{item.rank}</td><td><strong>{item.nickname}</strong><PresenceLabel online={item.online} activity={item.activity}/></td><td>{item.rating}</td></tr>)}</tbody></table>
   {view&&!view.entries.length&&<p>暂无对战记录</p>}
  </section>
  <section className="duel-public-records"><header><h2>对战记录</h2><time>{view?.date}</time></header>
   {view?.records.map(room=><article key={room.id} className="duel-public-record"><time>{time(room.finishedAt)}</time><div>{room.players.map((player,i)=><span key={player.userId}>{i>0&&<small>vs</small>}<strong data-winner={room.winner===player.userId}>{player.nickname}</strong><b data-loss={player.change<0}>{player.change>0?'+':''}{player.change}</b></span>)}</div><span className="duel-record-result">{room.judgeFailed?'判分失败':room.winner?`${room.players.find(p=>p.userId===room.winner)?.nickname||'—'} 胜`:'平局'}</span></article>)}
   {view&&!view.records.length&&<p>暂无对战记录</p>}
   {view?.next&&<button type="button" className="icon-button" disabled={busy} aria-label="更早的对战记录" onClick={()=>load(true)}><ArrowDown size={18}/></button>}
  </section>
  {error&&<p className="connection-error" role="alert">{error}</p>}
 </section>;
}
