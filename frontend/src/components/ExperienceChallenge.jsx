import {useEffect,useRef,useState} from 'react';
import {Code,LoaderCircle,Sprout,X} from 'lucide-react';
import './ExperienceChallenge.css';

export default function ExperienceChallenge({owner,offer,ready,blocked,api,onGrowth,onOpen,onOpenChange}){
 const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const generation=useRef(0),scope=useRef(owner),seen=useRef(''),automatic=useRef(''),dialog=useRef(null),callbacks=useRef({onGrowth,onOpen});
 callbacks.current={onGrowth,onOpen};
 const supported=Boolean(owner&&offer?.owner===owner&&offer?.policyVersion===1);
 useEffect(()=>{onOpenChange?.(open||busy);},[open,busy,onOpenChange]);
 useEffect(()=>{scope.current=owner;generation.current++;seen.current='';automatic.current='';setOpen(false);setBusy(false);setError('');return()=>{generation.current++;};},[owner]);
 const choose=async(action,choice,launch=false)=>{
  const expected=owner,seq=++generation.current;setBusy(true);setError('');
  const current=()=>seq===generation.current&&scope.current===expected&&(!window.__tbAccountUserId||window.__tbAccountUserId===expected);
  try{
   const value=await api('experience-challenge',{action,...(choice?{choice}:{})});
   if(!current()||value.challenge?.owner!==expected)return;
   callbacks.current.onGrowth?.(value.growth);
   if(action==='choose'){
    setOpen(false);
    if(window.__tbExperienceChoicePending?.owner===expected)delete window.__tbExperienceChoicePending;
    if(launch&&value.challenge?.problemId&&value.challenge?.status!=='passed')await callbacks.current.onOpen?.(value.challenge.problemId);
   }
  }catch(issue){if(current()){setError(issue.message);if(action==='choose')setOpen(true);}}
  finally{if(current())setBusy(false);}
 };
 useEffect(()=>{
  if(!supported||!ready||blocked||busy||!offer.eligible)return;
  const pending=window.__tbExperienceChoicePending;
  if(pending?.owner===owner&&['beginner','experienced'].includes(pending.choice)&&automatic.current!==owner){
   automatic.current=owner;void choose('choose',pending.choice,pending.choice==='experienced');return;
  }
  if(offer.promptRequired&&seen.current!==owner){seen.current=owner;setOpen(true);}
 },[owner,supported,ready,blocked,busy,offer]);
 useEffect(()=>{
  if(!open||!supported)return;
  const node=dialog.current;node.showModal();node.querySelector('button')?.focus();
  void choose('seen');
  return()=>node.close();
 },[open,supported]);
 useEffect(()=>{
  const launch=event=>{if(event.detail?.owner===owner&&supported&&ready&&!blocked&&!busy&&offer.eligible)setOpen(true);};
  window.addEventListener('tb:open-experience-challenge',launch);return()=>window.removeEventListener('tb:open-experience-challenge',launch);
 },[owner,supported,ready,blocked,busy,offer?.eligible]);
 if(!open||!supported)return null;
 return <dialog ref={dialog} className="experience-challenge" aria-labelledby="experience-title" onCancel={event=>{event.preventDefault();if(!busy)setOpen(false);}}>
  <header><h2 id="experience-title">你有编程经验吗？</h2><button type="button" aria-label="稍后继续" disabled={busy} onClick={()=>setOpen(false)}><X size={18}/></button></header>
  <p>完成一道二分或前缀和模板题的全部测试，即可升至 6 级并解锁全部功能。</p>
  <div className="experience-choices"><button type="button" disabled={busy} onClick={()=>void choose('choose','beginner')}><Sprout size={22}/><strong>我是新手</strong><small>从 1 级基础题单开始，随升级逐步解锁；6 级前仍可参加老手测试。</small></button><button type="button" disabled={busy} onClick={()=>void choose('choose','experienced',true)}><Code size={22}/><strong>我是老手</strong><small>先完成模板题测试，通过后直升 6 级；未通过可继续基础练习并再次测试。</small></button></div>
  {busy&&<p role="status"><LoaderCircle size={16} className="spin"/>正在保存选择…</p>}{error&&<p role="alert">{error}</p>}
 </dialog>;
}
