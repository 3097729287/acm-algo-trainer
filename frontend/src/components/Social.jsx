import {trainingDay} from '@/lib/trainingDate.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Check, Heart, MessageCircle, Send, X } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
import './Social.css';

const dateText=value=>new Date(value).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
const socialCache=new WeakMap();
export function useSocial(api, enabled) {
  const [snapshot,setSnapshot]=useState(()=>enabled?socialCache.get(api)||null:null), [error,setError]=useState('');
  const generation=useRef(0), pending=useRef(null);
  const refresh=useCallback(() => {
    if (!enabled) return Promise.resolve();
    if (pending.current) return pending.current;
    const request=generation.current;
    const task=api('social').then(value=>{if(request===generation.current){setSnapshot(value);socialCache.set(api,value);setError('');}})
      .catch(issue=>{if(request===generation.current)setError(issue.message);})
      .finally(()=>{if(pending.current===task)pending.current=null;});
    pending.current=task;return task;
  },[api,enabled]);
  useEffect(()=>{
    generation.current++;pending.current=null;setSnapshot(enabled?socialCache.get(api)||null:null);
    if(!enabled)return;
    refresh();const visible=()=>{if(!document.hidden)refresh();};
    const timer=setInterval(visible,30000);
    window.addEventListener('tb:social-change',visible);document.addEventListener('visibilitychange',visible);
    return()=>{generation.current++;clearInterval(timer);window.removeEventListener('tb:social-change',visible);document.removeEventListener('visibilitychange',visible);};
  },[enabled,refresh]);
  return {snapshot,error,refresh};
}

const particles=[['0px','-30px','#f97083'],['23px','-23px','#f5bd63'],['32px','0px','#8f8cf0'],['23px','23px','#6ccbb1'],['0px','31px','#68b8f4'],['-23px','23px','#e18ce8'],['-32px','0px','#f5bd63'],['-23px','-23px','#6ccbb1']];
export function LikeBurst({ targetId,nickname,likes,disabled,self=false,api,onLiked,onError,period='total' }) {
  const count=likes?.counts?.[period]??likes?.total??0;
  const [value,setValue]=useState({...likes,total:count,likedToday:!!likes?.likedToday}), [burst,setBurst]=useState(false), [oldCount,setOldCount]=useState(0);
  const inFlight=useRef(false), acknowledged=useRef(false), timer=useRef(null);
  useEffect(()=>{setValue(previous=>acknowledged.current ? {total:Math.max(previous.total,count),likedToday:true} : {total:count,likedToday:!!likes?.likedToday});},[count,likes?.likedToday]);
  useEffect(()=>()=>clearTimeout(timer.current),[]);
  async function like(){
    if(disabled || value.likedToday || inFlight.current)return;
    inFlight.current=true;
    const before=value;setOldCount(before.total);setValue({total:before.total+1,likedToday:true});setBurst(true);
    timer.current=setTimeout(()=>setBurst(false),600);
    try {
      const result=await api('social/likes',{targetId});
      const received={...result.likes,counts:result.counts};
      acknowledged.current=true;setValue({total:result.counts?.[period]??result.likes.total,likedToday:result.likes.likedToday});onLiked?.({...result,likes:received});
      window.dispatchEvent(new CustomEvent('tb:social-change',{detail:result}));
    } catch(issue){setValue(before);setBurst(false);onError?.(issue.message);}
    finally{inFlight.current=false;}
  }
  return <button type="button" className="like-burst" data-liked={value.likedToday||self} data-self={self} data-burst={burst} disabled={disabled || value.likedToday} aria-label={`${value.likedToday ? '今天已给' : '给'} ${nickname} 点爱心，${value.total} 个爱心`} aria-pressed={value.likedToday} title={value.likedToday ? '今天已点爱心，明天可以再点' : disabled ? '收到的爱心' : '点爱心，今天不能取消'} onClick={like}>
    <span className="like-burst-icon"><Heart size={19} fill={value.likedToday||self?'currentColor':'none'}/>{burst && particles.map(([x,y,color],index)=><i key={index} style={{'--dx':x,'--dy':y,'--particle-color':color}} aria-hidden="true"/>)}</span>
    <span className="like-burst-count" aria-live="polite"><span key={burst ? 'roll' : 'still'} className={burst?'like-count-roll':''}>{burst && <span aria-hidden="true">{oldCount}</span>}<span>{value.total}</span></span></span>
  </button>;
}

export function CommentDialog({ target,api,onClose,onSent }) {
  const dialog=useRef(null),textarea=useRef(null),submission=useRef(null);
  const [text,setText]=useState(''), [busy,setBusy]=useState(false), [error,setError]=useState('');
  useEffect(()=>{const node=dialog.current;node.showModal();textarea.current.focus();return()=>node.close();},[]);
  async function send(event){
    event.preventDefault();if(busy || !text.trim())return;
    setBusy(true);setError('');
    if(submission.current?.text!==text.trim())submission.current={text:text.trim(),requestId:crypto.randomUUID()};
    try{await api('social/comments',{targetId:target.userId,...submission.current});window.dispatchEvent(new Event('tb:social-change'));onSent?.();onClose();}
    catch(issue){setError(issue.message);setBusy(false);}
  }
  return <dialog ref={dialog} className="social-comment-dialog" aria-labelledby="social-comment-title" onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
    <header><h3 id="social-comment-title"><MessageCircle size={18}/>给 {target.nickname || '训练者'} 留言</h3><button type="button" aria-label="关闭留言" disabled={busy} onClick={onClose}><X size={18}/></button></header>
    <form onSubmit={send}><label htmlFor="social-comment-text">留言内容</label><textarea ref={textarea} id="social-comment-text" value={text} onChange={event=>setText(event.target.value)} maxLength={500} rows={5} required disabled={busy} placeholder="送上一句鼓励…"/><div className="social-comment-footer"><small>{Array.from(text).length}/500 · 对方会在消息通知中收到</small><button className="primary" disabled={busy || !text.trim()}><Send size={15}/>{busy?'正在发送…':'发送留言'}</button></div>{error && <p className="connection-error" role="alert">{error}</p>}</form>
  </dialog>;
}

export function SocialNotifications({ social,api }) {
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const value=social.snapshot;
  if(!value?.available)return social.error ? <p className="connection-error" role="status">消息暂时无法刷新。{social.error}</p> : null;
  async function read(selection){
    if(busy)return;setBusy(true);setError('');
    try{await api('social/read',selection);await social.refresh();}catch(issue){setError(issue.message);}finally{setBusy(false);}
  }
  return <section className="social-notifications" aria-label="爱心与留言"><div className="progress-section-heading"><h2 className="social-notifications-title" aria-label="爱心与留言"><Tooltip text="爱心"><Heart size={22} className="social-heart" fill="currentColor"/></Tooltip><span>和</span><Tooltip text="留言"><MessageCircle size={22}/></Tooltip></h2><button type="button" className="text-button" disabled={busy || !value.unreadCount} onClick={()=>read({all:true})}><Check size={14}/>全部已读</button></div>
    <p className="progress-small">共收到 {value.totalLikes} 个爱心 · {value.unreadCount} 条未读消息</p>
    {value.notifications.length ? <div>{value.notifications.map(item=><article key={item.id} className="social-notification" data-read={item.read}>{item.kind==='like'?<Heart size={18} className="social-heart" fill="currentColor"/>:<MessageCircle size={18}/>}<div><strong>{item.actor.nickname} {item.kind==='like'?'给你点了爱心':'给你留言'}</strong>{item.kind==='comment' && <p>{item.text}</p>}<time dateTime={item.createdAt}>{dateText(item.createdAt)}</time></div>{!item.read && <button className="text-button" disabled={busy} onClick={()=>read({ids:[item.id]})} aria-label={`标为已读 ${item.actor.nickname} 的${item.kind==='like'?'爱心':'留言'}`}><Check size={14}/></button>}</article>)}</div> : <p className="progress-muted">收到的爱心和留言会出现在这里。</p>}
    {error && <p className="connection-error" role="alert">{error}</p>}
  </section>;
}

export function SocialActivity({ items=[] }) {
  const today=trainingDay(new Date().toISOString());
  const current=items.filter(item=>trainingDay(item.createdAt)===today);
  return <section className="social-activity" aria-label="爱心动态"><h3><Heart size={16}/>爱心动态</h3>{current.slice(0,20).map(item=><div key={item.id}><span><strong>{item.actor.nickname}</strong> 给 <strong>{item.recipient.nickname}</strong> 点了爱心</span><time dateTime={item.createdAt}>{dateText(item.createdAt)}</time></div>)}</section>;
}
