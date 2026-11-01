import {cloneElement,useEffect,useRef,useState} from 'react';
import './ReorderableNavigation.css';

// Keep the DOM order stable while dragging. Neighbours move into the vacant
// slot; only a completed drop changes the saved navigation preference.
export default function ReorderableNavigation({entries,pending,fallback,onReorder,children}){
 const root=useRef(null),gesture=useRef(null),timer=useRef(null),frame=useRef(null),settle=useRef(null),ignoreClick=useRef(0);
 const callbacks=useRef({entries,onReorder});callbacks.current={entries,onReorder};
 const [drag,setDrag]=useState(null);
 const signature=entries.map(item=>item.id).join('\0');
 const clear=()=>{clearTimeout(timer.current);clearTimeout(settle.current);cancelAnimationFrame(frame.current);};
 const cancel=()=>{
  clear();const current=gesture.current;gesture.current=null;setDrag(null);
  if(current?.active){ignoreClick.current=performance.now()+300;try{root.current?.releasePointerCapture(current.pointer);}catch{}}
 };
 const position=current=>{
  const scroll=root.current.scrollTop-current.scroll;
  const center=current.y;
  let target=current.boxes.findIndex(box=>center<box.top+box.height/2-scroll);
  if(target<0)target=current.boxes.length;
  // Removing the source shifts insertion positions after it by one.
  target=Math.max(0,Math.min(current.boxes.length-1,target-(target>current.source?1:0)));
  current.target=target;
  setDrag({id:current.id,source:current.source,target,boxes:current.boxes,shift:current.y-current.startY+scroll,settling:false});
 };
 const tick=()=>{
  const current=gesture.current;if(!current?.active||current.settling)return;
  const nav=root.current,box=nav.getBoundingClientRect(),before=nav.scrollTop;
  if(current.y<box.top+30)nav.scrollTop-=8;else if(current.y>box.bottom-30)nav.scrollTop+=8;
  if(nav.scrollTop!==before)position(current);
  frame.current=requestAnimationFrame(tick);
 };
 const down=event=>{
  if(pending||event.button!==0||gesture.current)return;
  const button=event.target.closest('[data-navigation-id]');if(!button||!root.current.contains(button))return;
  const current={id:button.dataset.navigationId,pointer:event.pointerId,startX:event.clientX,startY:event.clientY,y:event.clientY,active:false};
  gesture.current=current;
  timer.current=setTimeout(()=>{
   if(gesture.current!==current)return;
   const nodes=[...root.current.querySelectorAll('[data-navigation-id]')];
   current.boxes=nodes.map(node=>{const box=node.getBoundingClientRect();return {id:node.dataset.navigationId,top:box.top,height:box.height};});
   current.source=current.boxes.findIndex(box=>box.id===current.id);current.target=current.source;current.scroll=root.current.scrollTop;current.active=true;
   root.current.setPointerCapture(current.pointer);ignoreClick.current=performance.now()+600;
   position(current);frame.current=requestAnimationFrame(tick);
  },360);
 };
 const move=event=>{
  const current=gesture.current;if(!current||current.pointer!==event.pointerId||current.settling)return;
  if(!current.active){if(Math.hypot(event.clientX-current.startX,event.clientY-current.startY)>6)cancel();return;}
  event.preventDefault();current.y=event.clientY;position(current);
 };
 const up=event=>{
  const current=gesture.current;if(!current||current.pointer!==event.pointerId)return;
  clearTimeout(timer.current);
  if(!current.active){gesture.current=null;return;}
  event.preventDefault();cancelAnimationFrame(frame.current);current.settling=true;ignoreClick.current=performance.now()+500;
  const shift=current.boxes[current.target].top-current.boxes[current.source].top;
  setDrag(value=>({...value,shift,settling:true}));
  settle.current=setTimeout(()=>{
   const {entries,onReorder}=callbacks.current,next=[...entries],source=next.findIndex(item=>item.id===current.id);
   if(source>=0&&source!==current.target){const [item]=next.splice(source,1);next.splice(current.target,0,item);onReorder(next);}
   cancel();
  },170);
 };
 useEffect(()=>{
  const escape=event=>{if(event.key==='Escape'&&gesture.current){event.preventDefault();event.stopPropagation();cancel();}};
  const release=event=>{if(gesture.current&&!gesture.current.active)up(event);};
  document.addEventListener('keydown',escape,true);document.addEventListener('pointerup',release,true);window.addEventListener('blur',cancel);
  return()=>{clear();document.removeEventListener('keydown',escape,true);document.removeEventListener('pointerup',release,true);window.removeEventListener('blur',cancel);};
 },[]);
 useEffect(()=>{cancel();},[signature,pending]);
 const style=(item,index)=>{
  if(!drag)return undefined;
  let shift=0;
  if(item.id===drag.id)shift=drag.shift;
  else if(drag.source<drag.target&&index>drag.source&&index<=drag.target)shift=drag.boxes[index-1].top-drag.boxes[index].top;
  else if(drag.source>drag.target&&index>=drag.target&&index<drag.source)shift=drag.boxes[index+1].top-drag.boxes[index].top;
  return {transform:`translateY(${shift}px)${item.id===drag.id&&!drag.settling?' scale(1.04)':''}`};
 };
 return <nav ref={root} className="reorderable-navigation" aria-label="主导航" aria-busy={pending} data-reordering={Boolean(drag)} data-settling={Boolean(drag?.settling)}
  onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={cancel} onLostPointerCapture={()=>{if(gesture.current?.active&&!gesture.current.settling)cancel();}}
  onClickCapture={event=>{if(performance.now()<ignoreClick.current){event.preventDefault();event.stopPropagation();}}}
  onContextMenu={event=>{if(gesture.current?.active)event.preventDefault();}}>
  {pending?fallback:entries.map((item,index)=>cloneElement(children(item),{key:item.id,'data-navigation-id':item.id,'data-drag-active':drag?.id===item.id,style:style(item,index)}))}
 </nav>;
}
