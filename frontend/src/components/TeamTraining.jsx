import {lazy,Suspense,useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {Check,Copy,Flag,Gift,Hand,History,LogIn,LogOut,Play,RefreshCw,Save,UsersRound,X} from 'lucide-react';
import {StudyPaneContext} from '../lib/StudyPane.jsx';
import {readLocalSharedRecovery,saveBeforeUpdate} from '../app/Workbench.jsx';
import CodeEditor from './CodeEditor.jsx';
import './TeamTraining.css';

const Workbench=lazy(()=>import('../app/Workbench.jsx'));
const ignore=promise=>void promise?.catch(()=>undefined);
const running=room=>['countdown','active'].includes(room?.status);
const time=value=>new Date(value).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
const timer=seconds=>`${Math.floor(Math.max(0,seconds)/60)}:${String(Math.max(0,seconds)%60).padStart(2,'0')}`;
const readUi=key=>{try{const value=JSON.parse(localStorage.getItem(key));return value&&typeof value==='object'&&!Array.isArray(value)?value:{};}catch{return {};}};

function useRoomPane(owner,id){
 const key=`tb.team.ui.v1.${owner}.${id}`,[entry,setEntry]=useState(()=>({key,state:readUi(key)})),current=useRef(entry);current.current=entry;
 const remember=useCallback((name,value)=>{
  if(window.__tbAccountUserId!==owner)return;
  const previous=current.current.key===key?current.current.state:readUi(key);
  if(Object.is(previous[name],value))return;
  const next={key,state:{...previous,[name]:value}};current.current=next;setEntry(next);
  try{localStorage.setItem(key,JSON.stringify(next.state));}catch{/* Retain the in-memory layout. */}
 },[key,owner]);
 return useMemo(()=>({key,scope:'team',visible:true,focused:true,embedded:false,state:entry.key===key?entry.state:readUi(key),remember}),[key,entry,remember]);
}

export default function TeamTraining({controller,owner}){
 const teamRef=useRef(controller);teamRef.current=controller;
 const [name,setName]=useState(''),[invite,setInvite]=useState(''),[catalogue,setCatalogue]=useState([]),[contestId,setContest]=useState(''),[duration,setDuration]=useState(300),[history,setHistory]=useState(null),[record,setRecord]=useState(null),[standings,setStandings]=useState(null),[localError,setLocalError]=useState(''),[copied,setCopied]=useState(false),[section,setSection]=useState('team');
 const state=controller?.state,team=state?.team,room=state?.room,leader=team?.leader===owner,me=team?.members?.find(p=>p.owner===owner),live=running(room),busy=controller?.busy;
 const readLists=async()=>{
  try{const answer=await teamRef.current.read('catalogue');setCatalogue(answer.contests);setLocalError('');}
  catch(e){setLocalError(e.message);}
 };
 useEffect(()=>{if(state?.enabled)void readLists();},[owner,state?.enabled]);
 useEffect(()=>{setContest(team?.contestId||'');setDuration(team?.durationMinutes||300);},[team?.contestId,team?.durationMinutes]);
 const changed=contestId!==team?.contestId||Number(duration)!==team?.durationMinutes;
 const recovery=record&&readLocalSharedRecovery(owner,record.id,record.problemId);
 const act=(kind,value)=>ignore(controller.act(kind,value));
 const showHistory=async()=>{setSection('history');try{const value=await controller.read('history');setHistory(value.rooms);setLocalError('');}catch(e){setLocalError(e.message);}};
 const showStandings=async()=>{setSection('standings');try{const value=await controller.read('standings');setStandings(value.entries);setLocalError('');}catch(e){setLocalError(e.message);}};
 const openRecord=async(id,problemId)=>{try{const value=await controller.read(`history/${id}${problemId?'?problemId='+encodeURIComponent(problemId):''}`);setRecord(value.room);setLocalError('');}catch(e){setLocalError(e.message);}};
 if(!controller)return null;
 return <section className="team-training" aria-label="三人团队训练">
  <div className="team-training-tools">
   <button type="button" className="icon-button" aria-label="当前队伍" title="当前队伍" aria-pressed={section==='team'} onClick={()=>setSection('team')}><UsersRound size={17}/></button>
   <button type="button" className="icon-button" aria-label="团队训练记录" title="团队训练记录" aria-pressed={section==='history'} onClick={()=>ignore(showHistory())}><History size={17}/></button>
   <button type="button" className="icon-button" aria-label="团队训练排行榜" title="团队训练排行榜" aria-pressed={section==='standings'} onClick={()=>ignore(showStandings())}><Flag size={17}/></button>
   <button type="button" className="icon-button" aria-label="刷新团队训练" title="刷新" disabled={busy} onClick={()=>{ignore(controller.reload());if(section==='history')ignore(showHistory());if(section==='standings')ignore(showStandings());}}><RefreshCw size={16}/></button>
  </div>
  {(controller.error||localError)&&<div className="connection-error" role="alert">{localError||controller.error}</div>}
  {!state&&!controller.error&&<p role="status">正在连接团队训练…</p>}
  {state&&!state.enabled&&<p role="status">团队训练服务尚未就绪</p>}
  {state?.enabled&&section==='team'&&<>
   {!team?<div className="team-join-forms">
    <form onSubmit={event=>{event.preventDefault();act('create',{name});}}><input aria-label="队名" placeholder="队名" maxLength={32} value={name} onChange={event=>setName(event.target.value)} required/><button type="submit" className="icon-button" title="创建队伍" aria-label="创建队伍" disabled={busy||!name.trim()}><UsersRound size={18}/></button></form>
    <form onSubmit={event=>{event.preventDefault();act('join',{inviteCode:invite});}}><input aria-label="队伍邀请码" placeholder="邀请码" maxLength={8} value={invite} onChange={event=>setInvite(event.target.value.toUpperCase())} required/><button type="submit" className="icon-button" title="加入队伍" aria-label="加入队伍" disabled={busy||invite.trim().length!==8}><LogIn size={18}/></button></form>
   </div>:<>
    <header className="team-lobby-heading"><strong>{team.name}</strong><button className="icon-button team-invite" type="button" aria-label="复制队伍邀请码" title="复制邀请码" onClick={async()=>{try{await navigator.clipboard.writeText(team.inviteCode);setCopied(true);setTimeout(()=>setCopied(false),1800);}catch{setLocalError('复制失败，请选择邀请码复制。');}}}><code>{team.inviteCode}</code>{copied?<Check size={14}/>:<Copy size={14}/>}</button><button className="icon-button" type="button" aria-label="离开队伍" title="离开队伍" disabled={busy||live} onClick={()=>act('leave')}><LogOut size={16}/></button></header>
    <ol className="team-members">{Array.from({length:3},(_,index)=>{const member=team.members[index];return <li key={member?.owner||index} data-self={member?.owner===owner||undefined}>{member?<><strong>{member.nickname}{member.owner===team.leader&&<Flag size={13} aria-label="队长"/>}</strong><span data-online={member.online}>{member.online?'在线':'离线'}</span><span className="team-ready" data-ready={member.ready}>{member.ready?<><Check size={14}/>已准备</>:live?'训练中':'未准备'}</span></>:<span className="team-empty-member">等待队友加入</span>}</li>;})}</ol>
    {!live?<div className="team-configuration">
     <select aria-label="团队训练比赛" value={contestId} disabled={!leader||busy} onChange={event=>setContest(event.target.value)}><option value="">选择比赛</option>{catalogue.map(c=><option key={c.id} value={c.id}>{c.title}{c.missingProblems?` · 缺 ${c.missingProblems} 题`:''}</option>)}</select>
     <label><input type="number" aria-label="团队训练时长" value={duration} min={5} max={300} disabled={!leader||busy} onChange={event=>setDuration(event.target.value)}/><span>分钟</span></label>
     {leader&&<button className="icon-button" type="button" aria-label="保存比赛设置" title="保存比赛设置" disabled={busy||!changed||!contestId||!Number.isInteger(Number(duration))||duration<5||duration>300} onClick={()=>act('configure',{contestId,durationMinutes:Number(duration)})}><Save size={17}/></button>}
     <button className="icon-button" type="button" aria-label={me?.ready?'取消准备':'准备'} title={me?.ready?'取消准备':'准备'} aria-pressed={me?.ready} disabled={busy||!team.contestId||leader&&changed} onClick={()=>act('ready',{ready:!me?.ready})}><Check size={19}/></button>
     {leader&&<button className="icon-button" type="button" aria-label="开始团队训练" title="开始团队训练" disabled={busy||changed||team.members.length!==3||!team.members.every(p=>p.ready&&p.online)} onClick={()=>act('start')}><Play size={19}/></button>}
    </div>:<div className="team-current-room"><strong>{room.contestTitle}</strong><span role="timer" aria-label="团队比赛剩余时间">{timer(Math.ceil((room.deadline-controller.serverNow)/1000))}</span><span>{room.score.totalScore} 题</span><button type="button" className="icon-button" aria-label="进入团队比赛" title="进入团队比赛" disabled={busy} onClick={()=>ignore(controller.enter())}><LogIn size={19}/></button></div>}
    {!live&&room?.status==='finished'&&<button type="button" className="team-last-result" onClick={()=>ignore(openRecord(room.id))}>{room.contestTitle}<span>{room.score.totalScore} 题</span><History size={16}/></button>}
   </>}
  </>}
  {section==='history'&&<div className="team-history">{history===null?<p role="status">正在读取团队训练记录…</p>:history.length?history.map(r=><button type="button" key={r.id} onClick={()=>ignore(openRecord(r.id))}><time>{time(r.startedAt)}</time><strong>{r.contestTitle}</strong><span>{r.teamName}</span><b>{r.score.totalScore} 题</b></button>):<p>暂无团队训练记录</p>}</div>}
  {section==='standings'&&<table className="team-ranking"><thead><tr><th>名次</th><th>团队</th><th>总分</th></tr></thead><tbody>{standings?.map((r,index)=><tr key={r.teamId}><td>{index&&standings[index-1].totalScore===r.totalScore?standings.findIndex(p=>p.totalScore===r.totalScore)+1:index+1}</td><td>{r.name}</td><td>{r.totalScore}</td></tr>)}</tbody>{standings?.length===0&&<caption>暂无团队训练成绩</caption>}</table>}
  {record&&<section className="team-record" aria-label="团队训练历史详情"><header><strong>{record.contestTitle}</strong><select aria-label="查看历史共享代码" value={record.problemId} onChange={event=>ignore(openRecord(record.id,event.target.value))}>{record.problems.map(p=><option key={p.id} value={p.id} disabled={!p.available}>{p.letter} · {p.title}</option>)}</select>{recovery&&recovery.code!==record.document.code&&<button className="icon-button" aria-label="复制本机保留代码" title="复制本机保留代码" type="button" onClick={async()=>{try{await navigator.clipboard.writeText(recovery.code);}catch{setLocalError("暂时无法复制，请保持当前窗口。");}}}><History size={16}/></button>}<button className="icon-button" aria-label="关闭团队历史" type="button" onClick={()=>setRecord(null)}><X size={16}/></button></header><CodeEditor value={record.document.code} docKey={record.id+':'+record.problemId} readOnly language={record.document.language} ariaLabel="历史共享代码"/></section>}
 </section>;
}

export function TeamTrainingRoom({controller,owner,shortcuts,onProgress,onNotice,onPacks}){
 const [confirm,setConfirm]=useState(false),[finishing,setFinishing]=useState(false),[localError,setLocalError]=useState('');
 const state=controller.state,room=state?.room;
 const pane=useRoomPane(owner,room?.id);
 useEffect(()=>{
  if(!controller.opened)return;
  const peers=[...document.querySelectorAll('.app-shell>.main-area,.app-shell>.sidebar,.study-browser')].map(node=>({node,inert:node.inert}));
  peers.forEach(({node})=>{node.inert=true;});return()=>peers.forEach(({node,inert})=>{node.inert=inert;});
 },[controller.opened]);
 if(!controller.opened||!room||controller.opened!==room.id||!state.localContest)return null;
 const leader=state.team?.leader===owner,editor=state.team?.members.find(p=>p.owner===room.lease?.owner),status=room.status;
 const select=async id=>{try{await saveBeforeUpdate();await controller.act('select',{problemId:id});}catch(e){setLocalError(e.message);}};
 const release=async()=>{try{await saveBeforeUpdate();await controller.act('release');}catch(e){setLocalError(e.message);}};
 const finish=async()=>{setFinishing(true);try{await saveBeforeUpdate();await controller.act('finish');setConfirm(false);}catch(e){setLocalError(e.message);}finally{setFinishing(false);}};
 return <div className="team-training-room study-problem-workspace" role="region" aria-label="团队比赛工作台" data-team-status={status}>
  {(controller.error||localError)&&<div className="connection-error team-room-error" role="alert"><span>{localError||controller.error}</span><button type="button" className="icon-button" aria-label="重新连接团队" onClick={()=>{setLocalError('');ignore(controller.reload());}}><RefreshCw size={15}/></button></div>}
  <StudyPaneContext.Provider value={pane}><Suspense fallback={<p role="status">正在进入团队比赛…</p>}><Workbench key={room.id} problemId={room.problemId} contest={state.localContest} shortcuts={shortcuts} api={controller.workbenchApi} sharedSession={{canEdit:controller.canEdit,problemId:room.problemId,document:room.document}} onProgress={onProgress} onNotice={onNotice} onExit={controller.close}
   headerStart={<select aria-label="团队比赛题目" title="切换队伍题目" value={room.problemId} disabled={!controller.canEdit||controller.busy} onChange={event=>ignore(select(event.target.value))}>{room.problems.map(p=><option value={p.id} key={p.id} disabled={!p.available}>{p.letter}{room.score.solved.some(s=>s.id===p.id)?' ✓':''}{!p.available?' · 缺题':''}</option>)}</select>}
   headerEnd={<>{state.pendingNativeReceipts>0&&<RefreshCw size={14} className="spin" role="status" aria-label="团队成绩待同步" title="团队成绩待同步"/>}<span className="team-editor-owner" title={editor?`${editor.nickname} 正在编辑`:'暂无编辑者'}><UsersRound size={14}/>{editor?.nickname||'待接管'}</span><span className="mock-timer" role="timer" aria-label={status==='countdown'?'团队比赛开始倒计时':'团队比赛剩余时间'}>{status==='countdown'?Math.max(0,Math.ceil((room.startedAt-controller.serverNow)/1000)):status==='finished'?'已结束':timer(Math.ceil((room.deadline-controller.serverNow)/1000))}</span>{status==='active'&&(controller.canEdit?<button className="wb-icon-button" type="button" aria-label="交出编辑控制" title="交出编辑控制" disabled={controller.busy} onClick={()=>ignore(release())}><LogOut size={16}/></button>:<button className="wb-icon-button" type="button" aria-label="接管编辑控制" title="接管编辑控制" disabled={controller.busy||room.lease?.until>controller.serverNow} onClick={()=>ignore(controller.act('claim'))}><Hand size={17}/></button>)}{leader&&status==='active'&&<button className="wb-icon-button" type="button" aria-label="结束团队比赛" title="结束团队比赛" disabled={controller.busy} onClick={()=>setConfirm(true)}><Flag size={16}/></button>}</>}/></Suspense></StudyPaneContext.Provider>
  {onPacks&&<button type="button" className="team-pack-button achievement-top-button" aria-label="卡包" title="卡包" onClick={onPacks}><Gift size={17}/></button>}
  {confirm&&<div className="modal-overlay"><section className="modal" role="dialog" aria-modal="true" aria-label="结束团队比赛确认"><h2>结束这场比赛？</h2><div className="modal-actions"><button type="button" disabled={finishing} onClick={()=>setConfirm(false)}>继续比赛</button><button type="button" disabled={finishing} onClick={()=>ignore(finish())}>{finishing?'正在处理…':'结束并复盘'}</button></div></section></div>}
 </div>;
}
