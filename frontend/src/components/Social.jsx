import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import {trainingDay} from '@/lib/trainingDate.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Check,Gift,Heart,LoaderCircle,MessageCircle,Send,X } from 'lucide-react';
import {StickerArt,STICKER_NAMES} from './StickerArt.jsx';
import Tooltip from './Tooltip.jsx';
import './Social.css';
import {readSocialCounts,saveSocialCounts,retainSocialCounts} from '@/lib/socialSnapshot.js';
import {giftPresetWarnings} from '@/lib/stickerScenes.js';

const dateText=value=>new Date(value).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
const socialCache=new WeakMap();
export function useSocial(api, enabled, owner='') {
  const cached=()=>socialCache.get(api)?.get(owner)||readSocialCounts(owner);
  const [saved,setSaved]=useState(()=>({owner,value:enabled?cached():null})), [error,setError]=useState('');
  const snapshot=saved.owner===owner?saved.value:enabled?cached():null;
  const setSnapshot=update=>setSaved(previous=>({owner,value:typeof update==='function'?update(previous.owner===owner?previous.value:null):update}));
  const remember=value=>{let cache=socialCache.get(api);if(!cache){cache=new Map();socialCache.set(api,cache);}cache.set(owner,value);saveSocialCounts(owner,value);};
  const generation=useRef(0), pending=useRef(null);
  const refresh=useCallback(() => {
    if (!enabled) return Promise.resolve();
    if (pending.current) return pending.current;
    const request=generation.current;
    const task=api('social').then(value=>{if(request===generation.current){setSnapshot(previous=>{const retained=retainSocialCounts(previous,value);remember(retained);return retained;});setError('');}})
      .catch(issue=>{if(request===generation.current)setError(issue.message);})
      .finally(()=>{if(pending.current===task)pending.current=null;});
    pending.current=task;return task;
  },[api,enabled,owner]);
  useEffect(()=>{
    generation.current++;pending.current=null;setSnapshot(enabled?cached():null);
    if(!enabled)return;
    refresh();const visible=()=>{if(!document.hidden)refresh();};
    const timer=setInterval(visible,30000);
    window.addEventListener('tb:social-change',visible);document.addEventListener('visibilitychange',visible);
    return()=>{generation.current++;clearInterval(timer);window.removeEventListener('tb:social-change',visible);document.removeEventListener('visibilitychange',visible);};
  },[enabled,refresh]);
  const markRead=useCallback(async selection=>{
    const request=generation.current;
    await api('social/read',selection);
    if(request!==generation.current)return;
    generation.current++;pending.current=null;
    setSnapshot(previous=>{
      if(!previous)return previous;
      const ids=new Set(selection.ids||[]),matches=item=>selection.all||ids.has(item.id);
      const count=previous.notifications.filter(item=>!item.read&&matches(item)).length;
      const value={...previous,notifications:previous.notifications.map(item=>matches(item)?{...item,read:true}:item),unreadCount:selection.all?0:Math.max(0,previous.unreadCount-count)};
      remember(value);return value;
    });
    await refresh();
  },[api,refresh]);
  return {snapshot,error,refresh,markRead,owner};
}

const particles=[['0px','-30px','#f97083'],['23px','-23px','#f5bd63'],['32px','0px','#8f8cf0'],['23px','23px','#6ccbb1'],['0px','31px','#68b8f4'],['-23px','23px','#e18ce8'],['-32px','0px','#f5bd63'],['-23px','-23px','#6ccbb1']];
export function LikeBurst({ targetId,nickname,likes,disabled,self=false,api,onLiked,onError,period='total',eventName='tb:social-change',toggle=false }) {
  const count=likes?.counts?.[period]??likes?.total??0;
  const [value,setValue]=useState({...likes,total:count,likedToday:!!likes?.likedToday}), [burst,setBurst]=useState(false), [oldCount,setOldCount]=useState(0);
  const inFlight=useRef(false), acknowledged=useRef(false), timer=useRef(null),queued=useRef(false),latestLike=useRef(null);
  useEffect(()=>{if(!inFlight.current)setValue(previous=>!toggle&&acknowledged.current ? {total:Math.max(previous.total,count),likedToday:true} : {total:count,likedToday:!!likes?.likedToday});},[count,likes?.likedToday,toggle]);
  useEffect(()=>()=>{clearTimeout(timer.current);latestLike.current=null;},[]);
  async function like(){
    if(disabled || !toggle&&value.likedToday)return;
    if(inFlight.current){if(toggle)queued.current=!queued.current;return;}
    inFlight.current=true;
    const before=value,liked=toggle?!before.likedToday:true;setOldCount(before.total);setValue({total:Math.max(0,before.total+(liked?1:-1)),likedToday:liked});setBurst(liked);
    timer.current=setTimeout(()=>setBurst(false),600);
    try {
      const result=await api('social/likes',{targetId,...(toggle?{liked}:{})});
      const received={...result.likes,counts:result.counts};
      acknowledged.current=true;setValue({total:result.counts?.[period]??result.likes.total,likedToday:result.likes.likedToday});onLiked?.({...result,likes:received});
      window.dispatchEvent(new CustomEvent(eventName,{detail:result}));
    } catch(issue){setValue(before);setBurst(false);onError?.(issue.message);}
    finally{inFlight.current=false;if(toggle&&queued.current){queued.current=false;requestAnimationFrame(()=>latestLike.current?.());}}
  }
  latestLike.current=like;
  return <button type="button" className="like-burst" data-liked={value.likedToday||self} data-self={self} data-burst={burst} disabled={disabled || !toggle&&value.likedToday} aria-label={toggle?`${value.likedToday?'取消':'给'} ${nickname} 点爱心，${value.total} 个爱心`:`${value.likedToday ? '今天已给' : '给'} ${nickname} 点爱心，${value.total} 个爱心`} aria-pressed={value.likedToday} title={toggle?(value.likedToday?'取消点赞':'点赞'):value.likedToday ? '今天已点爱心，明天可以再点' : disabled ? '收到的爱心' : '点爱心，今天不能取消'} onClick={like}>
    <span className="like-burst-icon"><Heart size={19} fill={value.likedToday||self?'currentColor':'none'}/>{burst && particles.map(([x,y,color],index)=><i key={index} style={{'--dx':x,'--dy':y,'--particle-color':color}} aria-hidden="true"/>)}</span>
    <span className="like-burst-count" aria-live="polite"><span key={burst ? 'roll' : 'still'} className={burst?'like-count-roll':''}>{burst && <span aria-hidden="true">{oldCount}</span>}<span>{value.total}</span></span></span>
  </button>;
}

export function CommentDialog({ target,api,onClose,onSent,replyTo }) {
  const dialog=useRef(null),textarea=useRef(null),submission=useRef(null),alive=useRef(true),sender=useRef(window.__tbAccountUserId);
  const [text,setText]=useState(''), [busy,setBusy]=useState(false), [error,setError]=useState('');
  const [inventory,setInventory]=useState(null),[gift,setGift]=useState(null),[picker,setPicker]=useState(false),[giftLoading,setGiftLoading]=useState(false),[presetAcknowledged,setPresetAcknowledged]=useState(false);
  const presetWarnings=gift?giftPresetWarnings(inventory,gift.unit.id):[];
  useEffect(()=>{alive.current=true;const node=dialog.current;node.showModal();textarea.current.focus();return()=>{alive.current=false;node.close();};},[]);
  async function gifts(){
    setPicker(value=>!value);if(inventory||giftLoading)return;setGiftLoading(true);setError('');
    try{const value=await api('stickers');if(!alive.current||sender.current!==window.__tbAccountUserId)return;if(sender.current&&value.owner!==sender.current)throw new Error('账号已切换');setInventory(value);}
    catch(issue){if(alive.current)setError(issue.message);}finally{if(alive.current)setGiftLoading(false);}
  }
  async function send(event){
    event.preventDefault();if(busy || !text.trim()||presetWarnings.length&&!presetAcknowledged)return;
    setBusy(true);setError('');
    const payload={targetId:target.userId,text:text.trim(),...(replyTo?{replyTo}:{}),...(gift?{gift:{unitId:gift.unit.id,revision:gift.unit.revision,...(presetWarnings.length?{presetRevision:inventory.revision}:{})}}:{})},signature=JSON.stringify(payload);
    if(submission.current?.signature!==signature)submission.current={signature,requestId:crypto.randomUUID()};
    try{const value=await api('social/comments',{...payload,requestId:submission.current.requestId});if(!alive.current||sender.current!==window.__tbAccountUserId)return;window.dispatchEvent(new Event('tb:social-change'));if(gift)window.dispatchEvent(new Event('tb:sticker-rewards'));onSent?.({...value,id:value.id||submission.current.requestId,text:payload.text,replyTo,createdAt:value.createdAt||new Date().toISOString(),...(gift?{gift:value.gift||gift.item}:{})});onClose();}
    catch(issue){if(alive.current){setError(issue.message);setBusy(false);if(gift&&issue.status===409){setPresetAcknowledged(false);try{const fresh=await api('stickers');if(alive.current&&sender.current===window.__tbAccountUserId)setInventory(fresh);}catch{}}}}
  }
  return <dialog onPointerDown={dialogPointerDown} onClick={dialogBackdropClick} ref={dialog} className="social-comment-dialog" aria-labelledby="social-comment-title" onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
    <header><h3 id="social-comment-title"><MessageCircle size={18}/>给 {target.nickname || '训练者'} 留言</h3><button type="button" aria-label="关闭留言" disabled={busy} onClick={onClose}><X size={18}/></button></header>
    <form onSubmit={send}><label htmlFor="social-comment-text">留言内容</label><textarea ref={textarea} id="social-comment-text" value={text} onChange={event=>setText(event.target.value)} maxLength={500} rows={5} required disabled={busy} placeholder="送上一句鼓励…"/>
    <div className="comment-gift-controls"><button type="button" className="icon-button" aria-label="赠送贴纸" title="赠送贴纸" aria-expanded={picker} disabled={busy} onClick={gifts}><Gift size={19}/></button>{gift&&<div className="comment-selected-gift"><StickerArt item={gift.item} size={42}/><span>{STICKER_NAMES[gift.item.rarity]} · {gift.item.title||gift.item.shape}</span><button type="button" className="icon-button" aria-label="取消赠送贴纸" disabled={busy} onClick={()=>setGift(null)}><X size={15}/></button></div>}</div>
    {picker&&<div className="comment-gift-picker" role="group" aria-label="可赠送的贴纸">{giftLoading?<LoaderCircle size={20} className="spin"/>:(inventory?.units||[]).filter(unit=>!unit.placement).map(unit=>{const item=inventory.catalogue.find(item=>item.id===unit.stickerId);return <button type="button" className={'comment-gift-choice rarity-'+item?.rarity} key={unit.id} aria-label={`赠送 ${item?.title||item?.shape}`} aria-pressed={gift?.unit.id===unit.id} disabled={busy} onClick={()=>{setGift({unit,item});setPresetAcknowledged(false);setPicker(false);setText(value=>value.trim()?value:'送你一张贴纸');}}><StickerArt item={item} size={48}/><small>{item?.title||item?.shape}</small></button>;})}{!giftLoading&&inventory&&!inventory.units.some(unit=>!unit.placement)&&<p>暂无可赠送的库存贴纸</p>}</div>}
    {presetWarnings.length>0&&<div className="comment-preset-warning" role="alert"><p>赠送后，{presetWarnings.map(p=>`「${p.name}」缺少 ${p.missing} 张贴纸`).join('、')}。</p><p>预设会保留，切换时跳过缺少的贴纸。重新获得同款后可补回；也可以调整场景后覆盖保存。</p><label><input type="checkbox" checked={presetAcknowledged} onChange={event=>setPresetAcknowledged(event.target.checked)}/>我已了解，继续赠送</label></div>}
    <div className="social-comment-footer"><small>{Array.from(text).length}/500 · 对方会在消息通知中收到</small><button className="primary" disabled={busy || !text.trim()||presetWarnings.length>0&&!presetAcknowledged}><Send size={15}/>{busy?'正在发送…':'发送留言'}</button></div>{error && <p className="connection-error" role="alert">{error}</p>}</form>
  </dialog>;
}

function SocialNotification({item,busy,onRead,onReply,replies=[]}) {
  const replyable=item.kind==='comment'&&typeof item.actor?.userId==='string'&&Boolean(item.actor.userId);
  return <article className="social-notification" data-read={item.read} data-replyable={replyable} role={replyable?'button':undefined} tabIndex={replyable?0:undefined} aria-label={replyable?`回复 ${item.actor.nickname||'训练者'} 的留言`:undefined}
    onClick={event=>{if(replyable&&!event.target.closest('button,a,input,textarea')&&window.getSelection()?.isCollapsed!==false)onReply(item);}}
    onKeyDown={event=>{if(replyable&&event.target===event.currentTarget&&['Enter',' '].includes(event.key)){event.preventDefault();event.stopPropagation();onReply(item);}}}>
    {item.kind==='like'?<Heart size={18} className="social-heart" fill="currentColor"/>:<MessageCircle size={18}/>}<div><strong>{item.actor.nickname} {item.kind==='like'?'给你点了爱心':'给你留言'}</strong>{item.kind==='comment'&&<p>{item.text}</p>}{item.gift&&<div className="social-message-gift"><StickerArt item={item.gift} size={48}/><span>{STICKER_NAMES[item.gift.rarity]}贴纸 · {item.gift.title||item.gift.shape}</span></div>}<time dateTime={item.createdAt}>{dateText(item.createdAt)}</time>
    {replies.length>0&&<div className="social-my-replies" aria-label="我的回复">{replies.map(reply=><div key={reply.id}><strong>我的回复</strong><p>{reply.text}</p>{reply.gift&&<div className="social-message-gift"><StickerArt item={reply.gift} size={38}/><span>{STICKER_NAMES[reply.gift.rarity]}贴纸 · {reply.gift.title||reply.gift.shape}</span></div>}<time dateTime={reply.createdAt}>{dateText(reply.createdAt)}</time></div>)}</div>}</div>
    {!item.read&&<button className="text-button" disabled={busy} onClick={()=>onRead({ids:[item.id]})} aria-label={`标为已读 ${item.actor.nickname} 的${item.kind==='like'?'爱心':'留言'}`}><Check size={14}/></button>}
  </article>;
}

export function SocialNotifications({ social,api,showReadAll=true,showEmpty=true }) {
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[replyTarget,setReplyTarget]=useState(null);
  const [sentReplies,setSentReplies]=useState({});
  useEffect(()=>{setSentReplies({});setReplyTarget(null);},[social.owner]);
  const raw=social.snapshot,today=trainingDay(new Date().toISOString());
  const notifications=(raw?.notifications||[]).filter(item=>trainingDay(item.createdAt)===today);
  const value=raw?{...raw,notifications,totalLikes:Number.isSafeInteger(raw.todayLikes)?raw.todayLikes:notifications.filter(item=>item.kind==='like').length,unreadCount:notifications.filter(item=>!item.read).length}:raw;
  const attempted=useRef(new Set());
  const unread=JSON.stringify((value?.notifications||[]).filter(item=>!item.read).map(item=>item.id));
  useEffect(()=>{
    if(busy||!social.markRead)return;
    const ids=JSON.parse(unread).filter(id=>!attempted.current.has(id)).slice(0,100);
    if(!ids.length)return;
    ids.forEach(id=>attempted.current.add(id));
    void read({ids});
  },[unread,social.markRead,busy]);
  if(!value?.available)return social.error ? <p className="connection-error" role="status">消息暂时无法刷新。{social.error}</p> : null;
  async function read(selection){
    if(busy)return;setBusy(true);setError('');
    try{if(social.markRead)await social.markRead(selection);else{await api('social/read',selection);await social.refresh();}}catch(issue){setError(issue.message);}finally{setBusy(false);}
  }
  return <><section className="social-notifications" aria-label="爱心与留言"><div className="progress-section-heading social-notifications-heading"><h2 className="social-notifications-title" aria-label="爱心与留言"><Tooltip text="爱心"><Heart size={22} className="social-heart" fill="currentColor"/></Tooltip><span>和</span><Tooltip text="留言"><MessageCircle size={22}/></Tooltip></h2><p className="progress-small social-notifications-summary">共收到 {value.totalLikes} 个爱心 · {value.unreadCount} 条未读消息</p>{showReadAll&&<button type="button" className="text-button" disabled={busy || !value.unreadCount} onClick={()=>read({all:true})}><Check size={14}/>全部已读</button>}</div>
    {value.notifications.length ? <div>{value.notifications.map(item=><SocialNotification key={item.id} item={item} busy={busy} onRead={read} onReply={setReplyTarget} replies={[...new Map([...(item.myReplies||[]),...(sentReplies[item.id]||[])].map(reply=>[reply.id,reply])).values()]}/>)}</div> : showEmpty&&<p className="progress-muted">收到的爱心和留言会出现在这里。</p>}
    {error && <p className="connection-error" role="alert">{error}</p>}
  </section>{replyTarget&&<CommentDialog target={replyTarget.actor} replyTo={replyTarget.id} api={api} onClose={()=>setReplyTarget(null)} onSent={reply=>{setSentReplies(previous=>({...previous,[reply.replyTo]:[...(previous[reply.replyTo]||[]),reply]}));void social.refresh?.();}}/>}</>;
}

export function SocialActivity({ items=[] }) {
  const today=trainingDay(new Date().toISOString());
  const current=items.filter(item=>trainingDay(item.createdAt)===today);
  return <section className="social-activity" aria-label="爱心动态"><h3><Heart size={16}/>爱心动态</h3>{current.slice(0,20).map(item=><div key={item.id}><span><strong>{item.actor.nickname}</strong> 给 <strong>{item.recipient.nickname}</strong> 点了爱心</span><time dateTime={item.createdAt}>{dateText(item.createdAt)}</time></div>)}</section>;
}
