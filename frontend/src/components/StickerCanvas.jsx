import {StickerArt,STICKER_NAMES as NAMES} from './StickerArt.jsx';
export {StickerArt} from './StickerArt.jsx';
import {cloneElement,useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import {readStickerLayout,cacheStickerLayout} from '@/lib/stickerCache.js';
import {createPortal} from 'react-dom';
import {fitStickerPlacement,stickerSize} from '@/lib/stickerPlacement.js';
import {Check,ChevronLeft,ChevronRight,Gift,LoaderCircle,Maximize2,RefreshCw,RotateCw,Sticker,Target,X} from 'lucide-react';
import StickerBoxes from './StickerBoxes.jsx';
import PopConfirm from './PopConfirm.jsx';
import Tooltip from './Tooltip.jsx';
import StickerReaction,{useStickerReaction} from './StickerReaction.jsx';
import './StickerCanvas.css';

const ORDER={legendary:0,epic:1,rare:2,common:3};

export default function StickerCanvas({api,owner,children,statistics,goals}){
 const [boxesOpen,setBoxesOpen]=useState(false),[goalsOpen,setGoalsOpen]=useState(false);
 const [mode,setMode]=useState(false),[state,setState]=useState(()=>readStickerLayout(owner)),[draft,setDraft]=useState(null),[picker,setPicker]=useState(null),[confirm,setConfirm]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const surface=useRef(null),strip=useRef(null),drag=useRef(null),alive=useRef(owner),request=useRef(null),saving=useRef(null),revision=useRef(0),latest=useRef(null);
 const [bounds,setBounds]=useState({width:0,height:0});
 const [reaction,reactToSticker]=useStickerReaction(owner),movedUnit=useRef(null);
 const recycling=useRef(new Map()),recycleRequests=useRef(new Map()),[pendingRecycles,setPendingRecycles]=useState(new Set());
 const [recycleError,setRecycleError]=useState('');
 useLayoutEffect(()=>{const node=surface.current;if(!node)return;const measure=()=>{const box=node.getBoundingClientRect();setBounds(previous=>previous.width===box.width&&previous.height===box.height?previous:{width:box.width,height:box.height});};measure();const observer=new ResizeObserver(measure);observer.observe(node);return()=>observer.disconnect();},[]);
 const fit=value=>fitStickerPlacement(value,bounds);
 alive.current=owner;
 const accept=useCallback((value,expected)=>{if(alive.current!==expected||value.owner!==expected||latest.current&&value.revision<latest.current.revision)return false;latest.current=value;cacheStickerLayout(value,expected);setState(value);return true;},[]);
 const refresh=useCallback(async()=>{const expected=owner,seq=++revision.current;try{const value=await api('stickers');if(seq===revision.current&&accept(value,expected))setError(value.rewardSyncError||'');}catch(issue){if(alive.current===expected&&seq===revision.current)setError(issue.message);}},[api,owner,accept]);
 useLayoutEffect(()=>{revision.current++;saving.current=null;request.current=null;drag.current=null;latest.current=null;recycling.current=new Map();recycleRequests.current=new Map();setPendingRecycles(new Set());setRecycleError('');setBusy(false);setError('');setState(readStickerLayout(owner));setDraft(null);setPicker(null);setConfirm(null);setMode(false);setGoalsOpen(false);setBoxesOpen(false);void refresh();},[refresh]);
 useEffect(()=>{const listener=event=>{const value=event.detail?.inventory;if(value){if(accept(value,owner))setError(value.rewardSyncError||'');}else void refresh();};window.addEventListener('tb:sticker-rewards',listener);window.addEventListener('focus',listener);return()=>{window.removeEventListener('tb:sticker-rewards',listener);window.removeEventListener('focus',listener);};},[refresh,accept,owner]);
 const mutate=useCallback(async(kind,unit,position)=>{
  if(saving.current)return;const operation={};saving.current=operation;setBusy(true);setError('');revision.current++;
  const expected=owner,payload={unitId:unit.id,revision:unit.revision,...position};
  const signature=JSON.stringify([kind,payload]);
  if(request.current?.signature!==signature)request.current={signature,requestId:crypto.randomUUID()};
  try{const result=await api('stickers/'+kind,{...payload,requestId:request.current.requestId});if(saving.current===operation&&alive.current===expected&&result.owner===expected){request.current=null;drag.current=null;accept(result,expected);setDraft(null);setConfirm(null);}}
  catch(issue){if(alive.current===expected&&saving.current===operation){setError(issue.message);if(issue.status===409){request.current=null;drag.current=null;setDraft(null);setConfirm(null);void refresh();}}}
  finally{if(saving.current===operation){saving.current=null;if(alive.current===expected)setBusy(false);}}
 },[api,owner,refresh,accept]);
 const recycle=useCallback(async unit=>{
  if(recycling.current.has(unit.id))return;
  const expected=owner,operation={},pending=recycling.current;
  pending.set(unit.id,operation);setError('');setRecycleError('');setConfirm(null);
  setPendingRecycles(new Set(pending.keys()));revision.current++;
  const signature=unit.id+':'+unit.revision;
  if(!recycleRequests.current.has(signature))recycleRequests.current.set(signature,crypto.randomUUID());
  try{
   const result=await api('stickers/recycle',{unitId:unit.id,revision:unit.revision,requestId:recycleRequests.current.get(signature)});
   if(alive.current!==expected||recycling.current!==pending)return;
   if(result?.owner!==expected)throw new Error('贴纸库存响应无效');
   accept(result,expected);
   recycleRequests.current.delete(signature);
  }catch(issue){
   if(alive.current===expected&&recycling.current===pending){setError(issue.message);setRecycleError(issue.message);if([404,409].includes(issue.status))recycleRequests.current.delete(signature);void refresh();}
  }finally{
   if(recycling.current===pending&&pending.get(unit.id)===operation){pending.delete(unit.id);setPendingRecycles(new Set(pending.keys()));}
  }
 },[api,owner,accept,refresh]);
 const canScale=Boolean(state?.placementPolicy?.scale);
 const fix=()=>{if(draft){const point=fit(draft);void mutate('place',draft.unit,{x:point.x,y:point.y,angle:point.angle,...(canScale?{scale:point.scale??1}:{})});}};
 useEffect(()=>{
  const node=surface.current;if(!node||!mode||!draft||!canScale||busy)return;
  const wheel=event=>{if(!event.target.closest('.selected-sticker'))return;event.preventDefault();event.stopPropagation();setDraft(value=>fit({...value,scale:(value.scale??1)*(event.deltaY>0?.95:1.05)}));};
  node.addEventListener('wheel',wheel,{passive:false});return()=>node.removeEventListener('wheel',wheel);
 },[mode,draft,canScale,busy,bounds]);
 useEffect(()=>{
  if(!mode)return;
  const key=event=>{
   if(event.target.closest('input,textarea,select,[contenteditable="true"]')||confirm)return;
   if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(busy)return;drag.current=null;if(draft){setDraft(null);request.current=null;}else if(picker)setPicker(null);else setMode(false);}
   else if(event.key==='Enter'&&draft){event.preventDefault();event.stopPropagation();fix();}
   else if(['+','-','='].includes(event.key)&&draft&&canScale&&!busy){event.preventDefault();setDraft(value=>fit({...value,scale:(value.scale??1)+(event.key==='-'?-.05:.05)}));}
   else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)&&draft&&!busy){event.preventDefault();const amount=event.shiftKey ? .02 : .005;setDraft(value=>fit({...value,x:value.x+(event.key==='ArrowRight'?amount:event.key==='ArrowLeft'?-amount:0),y:value.y+(event.key==='ArrowDown'?amount:event.key==='ArrowUp'?-amount:0)}));}
  };window.addEventListener('keydown',key,true);return()=>window.removeEventListener('keydown',key,true);
 },[mode,draft,picker,confirm,busy,bounds,canScale]);
 const items=[...(state?.owner===owner?state.catalogue||[]:[])].sort((a,b)=>ORDER[a.rarity]-ORDER[b.rarity]||a.id.localeCompare(b.id));
 const units=state?.owner===owner?(state.units||[]).filter(unit=>!pendingRecycles.has(unit.id)):[],placed=units.filter(unit=>unit.placement),art=id=>items.find(item=>item.id===id);
 const availableItems=items.filter(item=>units.some(unit=>unit.stickerId===item.id&&!unit.placement));
 const pickerWidth=Math.min(384,Math.max(150,availableItems.length*52+64),window.innerWidth-24);
 const pickerStyle=picker?{width:pickerWidth,left:Math.max(8,Math.min(picker.screenX-pickerWidth/2,window.innerWidth-pickerWidth-8)),top:Math.max(8,Math.min(picker.screenY+10,window.innerHeight-100))}:undefined;
 function position(event){const box=surface.current.getBoundingClientRect();return {x:(event.clientX-box.left)/box.width,y:(event.clientY-box.top)/box.height};}
 function begin(event,unit){if(event.button!==0||!mode||busy||draft&&draft.unit.id!==unit.id)return;event.preventDefault();event.stopPropagation();const point=position(event),start=fit(draft?.unit.id===unit.id?draft:unit.placement);setDraft({...start,unit});movedUnit.current=null;drag.current={pointer:event.pointerId,unitId:unit.id,startX:event.clientX,startY:event.clientY,dx:point.x-start.x,dy:point.y-start.y};event.currentTarget.setPointerCapture(event.pointerId);}
 function beginRotation(event){if(event.button!==0||busy||!draft)return;event.preventDefault();event.stopPropagation();const r=surface.current.getBoundingClientRect(),cx=r.left+draft.x*r.width,cy=r.top+draft.y*r.height;drag.current={kind:'rotate',pointer:event.pointerId,cx,cy,start:Math.atan2(event.clientY-cy,event.clientX-cx),angle:draft.angle};event.currentTarget.setPointerCapture(event.pointerId);}
 function beginScale(event){if(event.button!==0||busy||!draft||!canScale)return;event.preventDefault();event.stopPropagation();const r=surface.current.getBoundingClientRect(),cx=r.left+draft.x*r.width,cy=r.top+draft.y*r.height;drag.current={kind:'scale',pointer:event.pointerId,cx,cy,radius:Math.max(1,Math.hypot(event.clientX-cx,event.clientY-cy)),scale:draft.scale??1};event.currentTarget.setPointerCapture(event.pointerId);}
 function move(event){const active=drag.current;if(active?.pointer!==event.pointerId)return;if(active.unitId&&Math.hypot(event.clientX-active.startX,event.clientY-active.startY)>4)movedUnit.current=active.unitId;if(active.kind==='rotate'){const delta=(Math.atan2(event.clientY-active.cy,event.clientX-active.cx)-active.start)*180/Math.PI;setDraft(value=>value?fit({...value,angle:Math.round((active.angle+delta)*10)/10}):value);}else if(active.kind==='scale'){const scale=active.scale*Math.hypot(event.clientX-active.cx,event.clientY-active.cy)/active.radius;setDraft(value=>value?fit({...value,scale:Math.round(scale*1000)/1000}):value);}else{const point=position(event);setDraft(value=>value?fit({...value,x:point.x-active.dx,y:point.y-active.dy}):value);}}
 const unitButton=(unit,selected=false)=>{
  const point=fit(selected?draft:unit.placement),item=art(unit.stickerId),effect=reaction?.unitId===unit.id?reaction:null;
  return <button type="button" key={unit.id} className={'placed-sticker'+(selected?' selected-sticker':'')+(effect?' legendary-reacting':'')} data-rarity={item?.rarity} title={item?.title} style={{left:point.x*100+'%',top:point.y*100+'%',width:stickerSize(bounds,point.scale)+'px',transform:`translate(-50%,-50%) rotate(${point.angle}deg)`}} aria-label={`${NAMES[item?.rarity]}贴纸 ${item?.shape}`} onPointerDown={event=>begin(event,unit)} onPointerMove={move} onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;movedUnit.current=unit.id;}} onClick={event=>{event.stopPropagation();if(movedUnit.current===unit.id){movedUnit.current=null;return;}reactToSticker(unit,item);}} onContextMenu={event=>{event.preventDefault();event.stopPropagation();if(!draft&&!busy)setConfirm({unit,anchor:event.currentTarget});}}><StickerArt item={item} size="100%"/>{effect&&<StickerReaction reaction={effect}/>}</button>;
 };
 return <div className={'sticker-canvas'+(mode?' sticker-mode':'')}>

  <div className="sticker-content">{children}<div ref={surface} className="sticker-surface" aria-label="贴纸区域" role="region" tabIndex={mode?0:undefined} onPointerDown={event=>{if(event.button!==0||!mode||busy||draft||event.target!==event.currentTarget)return;const point=position(event);setPicker({...fit({...point,angle:0}),screenX:event.clientX,screenY:event.clientY});}}>{units.filter(unit=>unit.placement||unit.id===draft?.unit.id).map(unit=>unitButton(unit,unit.id===draft?.unit.id))}
   {draft&&canScale&&<button type="button" className="sticker-size-handle icon-button" aria-label="调整贴纸大小" title="拖动缩放贴纸" disabled={busy} style={{left:`calc(${draft.x*100}% + ${stickerSize(bounds,draft.scale)/2+8}px)`,top:`calc(${draft.y*100}% + ${stickerSize(bounds,draft.scale)/2+8}px)`}} onPointerDown={beginScale} onPointerMove={move} onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}}><Maximize2 size={13}/></button>}
   {draft&&<div className="sticker-edit-tools" style={{left:Math.min(80,Math.max(20,draft.x*100))+'%',top:Math.min(85,Math.max(15,draft.y*100))+'%',transform:`translate(-50%,${stickerSize(bounds,draft.scale)/2+18}px)`}} onPointerDown={event=>event.stopPropagation()}><button type="button" className="icon-button" aria-label="旋转贴纸" disabled={busy} data-sticker-rotate onPointerDown={beginRotation} onPointerMove={move} onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}} onWheel={event=>{if(!busy)setDraft(value=>fit({...value,angle:value.angle+(event.deltaY>0?1:-1)}));}}><RotateCw size={17}/></button><button type="button" className="icon-button" aria-label="固定贴纸" disabled={busy} onClick={fix}>{busy?<LoaderCircle className="progress-spin" size={17}/>:<Check size={18}/>}</button><button type="button" className="icon-button" aria-label="取消贴纸" disabled={busy} onClick={()=>{request.current=null;drag.current=null;setDraft(null);}}><X size={17}/></button></div>}
  </div></div>
  {picker&&mode&&createPortal(<div className="sticker-picker" style={pickerStyle} role="dialog" aria-label="选择贴纸"><button type="button" className="icon-button" aria-label="向左浏览贴纸" onClick={()=>strip.current.scrollBy({left:-240,behavior:'smooth'})}><ChevronLeft size={18}/></button><div ref={strip} className="sticker-inventory" onWheel={event=>{event.currentTarget.scrollLeft+=Math.abs(event.deltaX)>Math.abs(event.deltaY)?event.deltaX:event.deltaY;}}>{availableItems.map(item=>{const available=units.filter(unit=>unit.stickerId===item.id&&!unit.placement);return <button type="button" className={'sticker-choice rarity-'+item.rarity} key={item.id} aria-label={`${NAMES[item.rarity]} ${item.shape}，库存 ${available.length}`} disabled={!available.length} onClick={()=>{setDraft({unit:available[0],...picker,angle:0});setPicker(null);}}><StickerArt item={item}/><span>{available.length}</span></button>;})}</div><button type="button" className="icon-button" aria-label="向右浏览贴纸" onClick={()=>strip.current.scrollBy({left:240,behavior:'smooth'})}><ChevronRight size={18}/></button><button type="button" className="icon-button" aria-label="关闭贴纸选择" onClick={()=>setPicker(null)}><X size={17}/></button></div>,document.body)}
  {statistics}
  <div className="sticker-mode-toolbar" role="group" aria-label="成长内容">{<Tooltip text="贴纸宝箱"><button type="button" className="icon-button sticker-box-trigger" aria-label="贴纸宝箱" disabled={busy||Boolean(draft)||!state} onClick={()=>setBoxesOpen(true)}><Gift size={19}/>{Object.values(state?.boxes||{}).some(box=>!box.openedAt)&&<small>{Object.values(state?.boxes||{}).filter(box=>!box.openedAt).length}</small>}</button></Tooltip>}<Tooltip text="目标"><button type="button" className="icon-button" aria-label="目标" aria-expanded={goalsOpen} aria-pressed={goalsOpen} disabled={busy} onClick={()=>{setGoalsOpen(value=>!value);setMode(false);setDraft(null);setPicker(null);setConfirm(null);drag.current=null;request.current=null;}}><Target size={19}/></button></Tooltip><Tooltip text="贴纸"><button type="button" className="icon-button" aria-label="贴纸" aria-pressed={mode} disabled={busy} onClick={()=>{setGoalsOpen(false);setMode(value=>!value);setDraft(null);setPicker(null);setConfirm(null);drag.current=null;request.current=null;void refresh();}}><Sticker size={19}/></button></Tooltip>{error&&<button type="button" className="icon-button" aria-label="刷新贴纸" onClick={refresh}><RefreshCw size={16}/></button>}</div>
  {goalsOpen&&!mode&&goals&&cloneElement(goals,{onClose:()=>setGoalsOpen(false)})}
  {(recycleError||mode&&error)&&<p className="sticker-error connection-error" role="alert">{recycleError||error}</p>}
  {boxesOpen&&state?.owner===owner&&<StickerBoxes api={api} state={state} onUpdated={value=>accept(value,owner)} onClose={()=>setBoxesOpen(false)}/>}
  {confirm&&<PopConfirm anchor={confirm.anchor} label="回收贴纸确认" title="回收贴纸？" confirmLabel="回收" busyLabel="正在回收…" busy={busy} error={error} onCancel={()=>setConfirm(null)} onConfirm={()=>recycle(confirm.unit)}/>}
 </div>;
}
