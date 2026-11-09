import {useCallback,useEffect,useRef,useState} from 'react';
import {deliverNativeShortcut,shortcutSnapshot,subscribeShortcuts} from './applicationShortcuts.js';

let sequence=0;
const visible=node=>Boolean(node?.isConnected&&node.getClientRects().length&&getComputedStyle(node).visibility!=='hidden'&&getComputedStyle(node).display!=='none');
const blockingSurfaces='dialog[open],[role="dialog"],[role="alertdialog"],[role="listbox"],[role="tooltip"],[data-popconfirm],.modal-overlay,.modal-backdrop,.workspace-search-results,.tour-overlay,.next-actions-flyout,.recommendation-dialog';

export function embeddedFrame(node){
 if(document.hidden||!visible(node)||[...document.querySelectorAll(blockingSurfaces)].some(visible))return null;
 const viewport={width:innerWidth,height:innerHeight},box=node.getBoundingClientRect();
 let left=Math.max(0,box.left),top=Math.max(0,box.top),right=Math.min(innerWidth,box.right),bottom=Math.min(innerHeight,box.bottom);
 for(let parent=node.parentElement;parent;parent=parent.parentElement){
  if(!visible(parent))return null;
  const style=getComputedStyle(parent),clip=parent.getBoundingClientRect();
  if(/hidden|clip|scroll|auto/.test(style.overflowX)){left=Math.max(left,clip.left);right=Math.min(right,clip.right);}
  if(/hidden|clip|scroll|auto/.test(style.overflowY)){top=Math.max(top,clip.top);bottom=Math.min(bottom,clip.bottom);}
 }
 // Splitters deliberately have a wider transparent hit area. Leave that
 // native mouse target uncovered; the visible divider remains one pixel.
 for(const separator of document.querySelectorAll('[role="separator"][aria-orientation="vertical"]')){
  if(!visible(separator))continue;
  const edge=separator.getBoundingClientRect();if(edge.bottom<=top||edge.top>=bottom)continue;
  const grip=Math.max(edge.width,parseFloat(getComputedStyle(separator,'::before').width)||0),center=edge.left+edge.width/2;
  if(center>=right-16&&center<=right+16)right=Math.min(right,center-grip/2);
  else if(center>=left-16&&center<=left+16)left=Math.max(left,center+grip/2);
 }
 if(right-left<2||bottom-top<2)return null;
 for(const [x,y] of [[left+1,top+1],[right-1,top+1],[left+1,bottom-1],[right-1,bottom-1],[(left+right)/2,(top+bottom)/2]]){
  const hit=document.elementFromPoint(x,y);if(hit&&!node.contains(hit))return null;
 }
 return {rect:{x:left,y:top,width:right-left,height:bottom-top},viewport};
}

export default function useEmbeddedDeepSeek({api,owner,surface,enabled=true}){
 const [open,setOpen]=useState(false),[state,setState]=useState({available:false,status:'idle'});
 const scope=useRef(null),viewId=useRef(crypto.randomUUID()),generation=useRef(0),last=useRef(''),retry=useRef(false);
 const lastCommand=useRef(0);
 const apiRef=useRef(api);apiRef.current=api;
 useEffect(()=>{
  const epoch=++generation.current;scope.current=null;setOpen(false);setState({available:false,status:'idle'});last.current='';
  let alive=true,timer=null,attempt=0;
  const load=async()=>{
   attempt++;
   try{
    const value=await api('desktop/deepseek');if(!alive||epoch!==generation.current)return;
    scope.current=value;sequence=Math.max(sequence,value.sequence||0);setState(value);
    if(!value.available&&value.status!=='unavailable'&&attempt<5)timer=setTimeout(load,500);
   }catch(issue){if(alive&&epoch===generation.current&&![401,403].includes(issue.status)&&attempt<5)timer=setTimeout(load,500);}
  };
  void load();
  return()=>{alive=false;clearTimeout(timer);generation.current++;};
 },[api,owner]);
 const hide=useCallback(()=>{
  const context=scope.current;if(!context?.ownerKey)return;
  const message={viewId:viewId.current,sequence:++sequence,ownerKey:context.ownerKey,visible:false};
  void apiRef.current('desktop/deepseek',message).catch(()=>{});last.current='';
 },[]);
 useEffect(()=>{
  if(!open||!enabled){hide();return;}
  let alive=true,raf=null,lastSent=0,flight=false,again=false;
  const update=async(force=false)=>{
   const context=scope.current;if(!alive||!context?.available||!context.ownerKey)return;
   if(flight){again=true;return;}
   const geometry=embeddedFrame(surface.current),shortcuts=shortcutSnapshot(),key=JSON.stringify([geometry,shortcuts.serial]),now=Date.now();
   if(!force&&!retry.current&&last.current===key&&now-lastSent<1000)return;
   const message={viewId:viewId.current,sequence:++sequence,ownerKey:context.ownerKey,visible:Boolean(geometry),...(geometry?{...geometry,shortcuts}:{}),...(retry.current?{retry:true}:{})};
   const epoch=generation.current;last.current=key;lastSent=now;retry.current=false;flight=true;
   try{
    const value=await apiRef.current('desktop/deepseek',message);
    if(alive&&epoch===generation.current&&scope.current?.ownerKey===message.ownerKey)setState(previous=>JSON.stringify(previous)===JSON.stringify(value)?previous:value);
   }catch(issue){
    if(alive&&epoch===generation.current){
     setState(previous=>({...previous,status:'error',errorCode:issue.status===409?'OWNER_CHANGED':'CONNECTION_FAILED'}));
     if(issue.status===409){
      scope.current=null;setOpen(false);
      // A changed session must be explicitly reopened. Refresh only the local
      // capability; never show the new account's webpage automatically.
      void apiRef.current('desktop/deepseek').then(value=>{if(epoch===generation.current){scope.current=value;sequence=Math.max(sequence,value.sequence||0);setState(value);}}).catch(()=>{});
     }
    }
   }
   finally{flight=false;if(alive&&again){again=false;schedule();}}
  };
  const schedule=()=>{if(raf!==null)return;raf=requestAnimationFrame(()=>{raf=null;void update();});};
  const resized=new ResizeObserver(schedule);if(surface.current)resized.observe(surface.current);
  const changed=new MutationObserver(schedule);changed.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class','style','hidden','open','data-page','data-active']});
  const scroll=()=>schedule(),visibility=()=>{if(document.hidden)hide();else schedule();};
  addEventListener('resize',schedule);addEventListener('scroll',scroll,true);addEventListener('pagehide',hide);document.addEventListener('visibilitychange',visibility);
  const timer=setInterval(()=>void update(true),1000);schedule();
  const unsubscribe=subscribeShortcuts(schedule);
  return()=>{alive=false;unsubscribe();if(raf!==null)cancelAnimationFrame(raf);clearInterval(timer);resized.disconnect();changed.disconnect();removeEventListener('resize',schedule);removeEventListener('scroll',scroll,true);removeEventListener('pagehide',hide);document.removeEventListener('visibilitychange',visibility);hide();};
 },[open,enabled,owner,surface,hide]);
 useEffect(()=>{
  if(!open||!enabled)return;
  let alive=true,busy=false;const epoch=generation.current;
  const read=async()=>{
   if(busy||document.hidden||!scope.current?.available)return;busy=true;
   try{
    const value=await apiRef.current('desktop/deepseek-shortcuts');
    if(!alive||epoch!==generation.current||!value.available||value.viewId!==viewId.current||value.ownerKey!==scope.current?.ownerKey)return;
    for(const command of value.actions||[]){
     if(!alive||epoch!==generation.current)break;
     if(!Number.isSafeInteger(command.sequence)||command.sequence<=lastCommand.current)continue;
     lastCommand.current=command.sequence;deliverNativeShortcut(command,value.registration);
    }
   }catch{}finally{busy=false;}
  };
  const timer=setInterval(read,120);void read();
  return()=>{alive=false;clearInterval(timer);};
 },[open,enabled,owner]);
 const toggle=useCallback(()=>setOpen(value=>!value),[]);
 const reload=useCallback(()=>{retry.current=true;last.current='';dispatchEvent(new Event('resize'));},[]);
 return {open,toggle,reload,state};
}
