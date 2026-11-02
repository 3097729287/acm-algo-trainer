import {StickerArt,STICKER_NAMES as NAMES} from './StickerArt.jsx';
export {StickerArt} from './StickerArt.jsx';
import {useCallback,useEffect,useRef,useState} from 'react';
import {fitStickerPlacement} from '@/lib/stickerPlacement.js';
import {Check,ChevronLeft,ChevronRight,Gift,LoaderCircle,RefreshCw,RotateCw,Sticker,Target,X} from 'lucide-react';
import StickerBoxes from './StickerBoxes.jsx';
import PopConfirm from './PopConfirm.jsx';
import Tooltip from './Tooltip.jsx';
import './StickerCanvas.css';

const ORDER={legendary:0,epic:1,rare:2,common:3};

export default function StickerCanvas({api,owner,children}){
 const [boxesOpen,setBoxesOpen]=useState(false);
 const [mode,setMode]=useState(false),[state,setState]=useState(null),[draft,setDraft]=useState(null),[picker,setPicker]=useState(null),[confirm,setConfirm]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const surface=useRef(null),strip=useRef(null),drag=useRef(null),alive=useRef(owner),request=useRef(null),saving=useRef(null),revision=useRef(0),latest=useRef(null);
 const [bounds,setBounds]=useState({width:0,height:0});
 useEffect(()=>{const node=surface.current;if(!node)return;const measure=()=>{const box=node.getBoundingClientRect();setBounds(previous=>previous.width===box.width&&previous.height===box.height?previous:{width:box.width,height:box.height});};measure();const observer=new ResizeObserver(measure);observer.observe(node);return()=>observer.disconnect();},[]);
 const fit=value=>fitStickerPlacement(value,bounds);
 alive.current=owner;
 const accept=useCallback((value,expected)=>{if(alive.current!==expected||value.owner!==expected||latest.current&&value.revision<latest.current.revision)return false;latest.current=value;setState(value);return true;},[]);
 const refresh=useCallback(async()=>{const expected=owner,seq=++revision.current;try{const value=await api('stickers');if(seq===revision.current&&accept(value,expected))setError(value.rewardSyncError||'');}catch(issue){if(alive.current===expected&&seq===revision.current)setError(issue.message);}},[api,owner,accept]);
 useEffect(()=>{revision.current++;saving.current=null;request.current=null;drag.current=null;latest.current=null;setBusy(false);setError('');setState(null);setDraft(null);setPicker(null);setConfirm(null);setMode(false);setBoxesOpen(false);void refresh();},[refresh]);
 useEffect(()=>{const listener=()=>void refresh();window.addEventListener('tb:sticker-rewards',listener);window.addEventListener('focus',listener);return()=>{window.removeEventListener('tb:sticker-rewards',listener);window.removeEventListener('focus',listener);};},[refresh]);
 const mutate=useCallback(async(kind,unit,position)=>{
  if(saving.current)return;const operation={};saving.current=operation;setBusy(true);setError('');revision.current++;
  const expected=owner,payload={unitId:unit.id,revision:unit.revision,...position};
  const signature=JSON.stringify([kind,payload]);
  if(request.current?.signature!==signature)request.current={signature,requestId:crypto.randomUUID()};
  try{const result=await api('stickers/'+kind,{...payload,requestId:request.current.requestId});if(saving.current===operation&&alive.current===expected&&result.owner===expected){request.current=null;drag.current=null;accept(result,expected);setDraft(null);setConfirm(null);}}
  catch(issue){if(alive.current===expected&&saving.current===operation){setError(issue.message);if(issue.status===409){request.current=null;drag.current=null;setDraft(null);setConfirm(null);void refresh();}}}
  finally{if(saving.current===operation){saving.current=null;if(alive.current===expected)setBusy(false);}}
 },[api,owner,refresh,accept]);
 const fix=()=>{if(draft){const point=fit(draft);void mutate('place',draft.unit,{x:point.x,y:point.y,angle:point.angle});}};
 useEffect(()=>{
  if(!mode)return;
  const key=event=>{
   if(event.target.closest('input,textarea,select,[contenteditable="true"]')||confirm)return;
   if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(busy)return;drag.current=null;if(draft){setDraft(null);request.current=null;}else if(picker)setPicker(null);else setMode(false);}
   else if(event.key==='Enter'&&draft){event.preventDefault();event.stopPropagation();fix();}
   else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)&&draft&&!busy){event.preventDefault();const amount=event.shiftKey ? .02 : .005;setDraft(value=>fit({...value,x:value.x+(event.key==='ArrowRight'?amount:event.key==='ArrowLeft'?-amount:0),y:value.y+(event.key==='ArrowDown'?amount:event.key==='ArrowUp'?-amount:0)}));}
  };window.addEventListener('keydown',key,true);return()=>window.removeEventListener('keydown',key,true);
 },[mode,draft,picker,confirm,busy,bounds]);
 const items=[...(state?.catalogue||[])].sort((a,b)=>ORDER[a.rarity]-ORDER[b.rarity]||a.id.localeCompare(b.id));
 const units=state?.units||[],placed=units.filter(unit=>unit.placement),art=id=>items.find(item=>item.id===id);
 function position(event){const box=surface.current.getBoundingClientRect();return {x:(event.clientX-box.left)/box.width,y:(event.clientY-box.top)/box.height};}
 function begin(event,unit){if(event.button!==0||!mode||busy||draft&&draft.unit.id!==unit.id)return;event.preventDefault();event.stopPropagation();const point=position(event),start=fit(draft?.unit.id===unit.id?draft:unit.placement);setDraft({...start,unit});drag.current={pointer:event.pointerId,dx:point.x-start.x,dy:point.y-start.y};event.currentTarget.setPointerCapture(event.pointerId);}
 function move(event){const active=drag.current;if(active?.pointer!==event.pointerId)return;const point=position(event);setDraft(value=>value?fit({...value,x:point.x-active.dx,y:point.y-active.dy}):value);}
 const unitButton=(unit,selected=false)=>{const point=fit(selected?draft:unit.placement);return <button type="button" key={unit.id} className={'placed-sticker'+(selected?' selected-sticker':'')} style={{left:point.x*100+'%',top:point.y*100+'%',transform:`translate(-50%,-50%) rotate(${point.angle}deg)`}} aria-label={`${NAMES[art(unit.stickerId)?.rarity]}贴纸 ${art(unit.stickerId)?.shape}`} onPointerDown={event=>begin(event,unit)} onPointerMove={move} onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}} onContextMenu={event=>{event.preventDefault();event.stopPropagation();if(!draft&&!busy)setConfirm({unit,anchor:event.currentTarget});}}><StickerArt item={art(unit.stickerId)} size="100%"/></button>;};
 return <div className={'sticker-canvas'+(mode?' sticker-mode':'')}>
  <div className="sticker-mode-toolbar" role="group" aria-label="成长内容">{state&&Object.keys(state.boxes||{}).length>0&&<Tooltip text="贴纸宝箱"><button type="button" className="icon-button sticker-box-trigger" aria-label="贴纸宝箱" disabled={busy||Boolean(draft)} onClick={()=>setBoxesOpen(true)}><Gift size={19}/>{Object.values(state.boxes||{}).some(box=>!box.openedAt)&&<small>{Object.values(state.boxes||{}).filter(box=>!box.openedAt).length}</small>}</button></Tooltip>}<Tooltip text="目标"><button type="button" className="icon-button" aria-label="目标" aria-pressed={!mode} disabled={busy} onClick={()=>{setMode(false);setDraft(null);setPicker(null);setConfirm(null);drag.current=null;request.current=null;}}><Target size={19}/></button></Tooltip><Tooltip text="贴纸"><button type="button" className="icon-button" aria-label="贴纸" aria-pressed={mode} disabled={busy} onClick={()=>{setMode(true);void refresh();}}><Sticker size={19}/></button></Tooltip>{error&&<button type="button" className="icon-button" aria-label="刷新贴纸" onClick={refresh}><RefreshCw size={16}/></button>}</div>
  <div className="sticker-content">{children}<div ref={surface} className="sticker-surface" aria-label="贴纸区域" role="region" tabIndex={mode?0:undefined} onPointerDown={event=>{if(event.button!==0||!mode||busy||draft||event.target!==event.currentTarget)return;const point=position(event);setPicker(fit({...point,angle:0}));}}>{units.filter(unit=>unit.placement||unit.id===draft?.unit.id).map(unit=>unitButton(unit,unit.id===draft?.unit.id))}
   {draft&&<div className="sticker-edit-tools" style={{left:Math.min(80,Math.max(20,draft.x*100))+'%',top:Math.min(85,Math.max(15,draft.y*100))+'%'}} onPointerDown={event=>event.stopPropagation()}><button type="button" className="icon-button" aria-label="旋转贴纸" disabled={busy} onClick={()=>setDraft(value=>fit({...value,angle:value.angle>=165?-180:value.angle+15}))} onWheel={event=>{if(!busy)setDraft(value=>fit({...value,angle:((value.angle+(event.deltaY>0?5:-5)+540)%360)-180}));}}><RotateCw size={17}/></button><button type="button" className="icon-button" aria-label="固定贴纸" disabled={busy} onClick={fix}>{busy?<LoaderCircle className="progress-spin" size={17}/>:<Check size={18}/>}</button><button type="button" className="icon-button" aria-label="取消贴纸" disabled={busy} onClick={()=>{request.current=null;drag.current=null;setDraft(null);}}><X size={17}/></button></div>}
  </div></div>
  {picker&&mode&&<div className="sticker-picker" role="dialog" aria-label="选择贴纸"><button type="button" className="icon-button" aria-label="向左浏览贴纸" onClick={()=>strip.current.scrollBy({left:-240,behavior:'smooth'})}><ChevronLeft size={18}/></button><div ref={strip} className="sticker-inventory" onWheel={event=>{event.currentTarget.scrollLeft+=Math.abs(event.deltaX)>Math.abs(event.deltaY)?event.deltaX:event.deltaY;}}>{items.map(item=>{const available=units.filter(unit=>unit.stickerId===item.id&&!unit.placement);return <button type="button" className={'sticker-choice rarity-'+item.rarity} key={item.id} aria-label={`${NAMES[item.rarity]} ${item.shape}，库存 ${available.length}`} disabled={!available.length} onClick={()=>{setDraft({unit:available[0],...picker,angle:0});setPicker(null);}}><StickerArt item={item}/><span>{available.length}</span></button>;})}</div><button type="button" className="icon-button" aria-label="向右浏览贴纸" onClick={()=>strip.current.scrollBy({left:240,behavior:'smooth'})}><ChevronRight size={18}/></button><button type="button" className="icon-button" aria-label="关闭贴纸选择" onClick={()=>setPicker(null)}><X size={17}/></button></div>}
  {mode&&error&&<p className="sticker-error connection-error" role="alert">{error}</p>}
  {boxesOpen&&state?.owner===owner&&<StickerBoxes api={api} state={state} onUpdated={value=>accept(value,owner)} onClose={()=>setBoxesOpen(false)}/>}
  {confirm&&<PopConfirm anchor={confirm.anchor} label="回收贴纸确认" title="回收贴纸？" confirmLabel="回收" busyLabel="正在回收…" busy={busy} error={error} onCancel={()=>setConfirm(null)} onConfirm={()=>mutate('recycle',confirm.unit)}/>}
 </div>;
}
