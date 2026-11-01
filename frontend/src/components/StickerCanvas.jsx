import {useCallback,useEffect,useRef,useState} from 'react';
import {Check,ChevronLeft,ChevronRight,LoaderCircle,RefreshCw,RotateCw,Sticker,Target,X} from 'lucide-react';
import PopConfirm from './PopConfirm.jsx';
import Tooltip from './Tooltip.jsx';
import './StickerCanvas.css';

const ORDER={legendary:0,epic:1,rare:2,common:3};
const NAMES={common:'普通',rare:'稀有',epic:'史诗',legendary:'传说'};
const SHAPES={
 spark:'M50 8 59 36 88 40 65 58 70 88 50 71 28 88 33 58 11 40 41 36Z',
 leaf:'M79 17C25 9 10 49 29 72 51 99 91 66 79 17ZM28 75 69 33M47 54 44 36M54 48 70 50',
 drop:'M50 8C42 24 18 42 18 63a32 32 0 0 0 64 0C82 42 58 24 50 8Z',
 cloud:'M24 76a20 20 0 0 1-4-39 26 26 0 0 1 49-9 24 24 0 1 1 9 48Z',
 flame:'M49 7C61 28 82 37 81 61a31 31 0 0 1-62 0c0-15 9-27 17-35-2 17 6 22 6 22S57 33 49 7Z',
 bolt:'M57 7 17 56 44 56 36 94 85 40 58 40 66 7Z',
 sun:'M50 19 57 6 63 22 80 15 78 33 95 40 80 50 94 64 75 67 77 86 59 79 49 95 41 79 22 86 25 67 6 62 21 48 6 37 25 31 23 14 40 22Z',
 comet:'M91 8 68 65 38 86 16 69 14 43 41 22ZM19 61 60 21M36 82 79 39',
 moon:'M77 72C25 79 20 30 47 8 8 15-2 70 31 87 51 98 74 90 85 76Z',
 planet:'M73 26a31 31 0 1 0-46 48 31 31 0 0 0 46-48ZM13 61C-2 92 102 45 89 37M10 64C8 81 69 57 86 36',
 crystal:'M50 7 77 32 85 68 50 94 14 68 23 32ZM23 32 50 56 77 32M14 68 50 56 85 68M50 7 50 94',
 butterfly:'M49 47C5-11 3 36 24 53 1 57 16 95 42 70L50 58 58 70C84 95 99 57 76 53 97 36 95-11 51 47ZM50 42 50 82M50 42 41 27M50 42 59 27',
 gem:'M24 13H76L94 40 50 93 6 40ZM6 40H94M24 13 36 40 50 93 64 40 76 13M36 40 50 13 64 40',
 crown:'M12 23 33 42 50 13 68 42 88 23 77 79H23ZM23 65H77',
 galaxy:'M50 41C8 4 1 42 24 58 48 83 90 59 84 33 77 5 38 15 32 42 22 79 73 95 83 60M50 33 55 46 69 50 55 55 50 69 45 55 31 50 45 46Z',
 phoenix:'M48 72C12 85 9 53 6 23 20 44 34 28 50 55 66 28 80 44 94 23 91 53 88 85 52 72L50 94ZM50 58 50 24 64 15 57 32',
};
export function StickerArt({item,size=64}){
 const id=useRef('sticker-'+crypto.randomUUID()).current,rarity=item?.rarity||'common';
 const colors=rarity==='legendary'?['#69e3ff','#e184ff','#ffdc83']:rarity==='epic'?['#d8b9ff','#a06af2','#6e42bd']:rarity==='rare'?['#ffd184','#ff9b35','#db611a']:['#a8dcff','#4b9aff','#3864dc'];
 return <svg className="sticker-art" viewBox="0 0 100 100" width={size} height={size} aria-hidden="true"><defs><linearGradient id={id} x1="0" y1="0" x2="1" y2="1"><stop stopColor={colors[0]}/><stop offset=".5" stopColor={colors[1]}/><stop offset="1" stopColor={colors[2]}/></linearGradient></defs><path d={SHAPES[item?.shape]||SHAPES.spark} fill={`url(#${id})`} stroke="white" strokeWidth="8" strokeLinejoin="round" strokeLinecap="round"/><path d={SHAPES[item?.shape]||SHAPES.spark} fill={`url(#${id})`} stroke={colors[2]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"/><path d="M34 27 38 24M26 39 28 35" stroke="white" strokeOpacity=".7" strokeWidth="4" strokeLinecap="round"/></svg>;
}
const clamp=value=>Math.max(.04,Math.min(.96,value));

export default function StickerCanvas({api,owner,children}){
 const [mode,setMode]=useState(false),[state,setState]=useState(null),[draft,setDraft]=useState(null),[picker,setPicker]=useState(null),[confirm,setConfirm]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const surface=useRef(null),strip=useRef(null),drag=useRef(null),alive=useRef(owner),request=useRef(null),saving=useRef(false),revision=useRef(0);
 alive.current=owner;
 const refresh=useCallback(async()=>{const expected=owner,seq=++revision.current;try{const value=await api('stickers');if(alive.current===expected&&seq===revision.current){setState(value);setError(value.rewardSyncError||'');}}catch(issue){if(alive.current===expected)setError(issue.message);}},[api,owner]);
 useEffect(()=>{setState(null);setDraft(null);setPicker(null);setMode(false);void refresh();},[refresh]);
 useEffect(()=>{const listener=()=>void refresh();window.addEventListener('tb:sticker-rewards',listener);window.addEventListener('focus',listener);return()=>{window.removeEventListener('tb:sticker-rewards',listener);window.removeEventListener('focus',listener);};},[refresh]);
 const mutate=useCallback(async(kind,unit,position)=>{
  if(saving.current)return;saving.current=true;setBusy(true);setError('');revision.current++;
  const expected=owner,payload={unitId:unit.id,revision:unit.revision,...position};
  const signature=JSON.stringify([kind,payload]);
  if(request.current?.signature!==signature)request.current={signature,requestId:crypto.randomUUID()};
  try{const result=await api('stickers/'+kind,{...payload,requestId:request.current.requestId});if(alive.current===expected){request.current=null;setState(result);setDraft(null);setConfirm(null);}}
  catch(issue){if(alive.current===expected){setError(issue.message);if(issue.status===409){request.current=null;setDraft(null);setConfirm(null);void refresh();}}}
  finally{saving.current=false;if(alive.current===expected)setBusy(false);}
 },[api,owner,refresh]);
 const fix=()=>{if(draft)void mutate('place',draft.unit,{x:draft.x,y:draft.y,angle:draft.angle});};
 useEffect(()=>{
  if(!mode)return;
  const key=event=>{
   if(event.target.closest('input,textarea,select,[contenteditable="true"]')||confirm)return;
   if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(busy)return;if(draft){setDraft(null);request.current=null;}else if(picker)setPicker(null);else setMode(false);}
   else if(event.key==='Enter'&&draft){event.preventDefault();event.stopPropagation();fix();}
   else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)&&draft){event.preventDefault();const amount=event.shiftKey ? .02 : .005;setDraft(value=>({...value,x:clamp(value.x+(event.key==='ArrowRight'?amount:event.key==='ArrowLeft'?-amount:0)),y:clamp(value.y+(event.key==='ArrowDown'?amount:event.key==='ArrowUp'?-amount:0))}));}
  };window.addEventListener('keydown',key,true);return()=>window.removeEventListener('keydown',key,true);
 },[mode,draft,picker,confirm,busy]);
 const items=[...(state?.catalogue||[])].sort((a,b)=>ORDER[a.rarity]-ORDER[b.rarity]||a.id.localeCompare(b.id));
 const units=state?.units||[],placed=units.filter(unit=>unit.placement),art=id=>items.find(item=>item.id===id);
 function position(event){const box=surface.current.getBoundingClientRect();return {x:clamp((event.clientX-box.left)/box.width),y:clamp((event.clientY-box.top)/box.height)};}
 function begin(event,unit){if(!mode||busy||draft&&draft.unit.id!==unit.id)return;event.preventDefault();event.stopPropagation();const point=position(event),start=unit.placement||draft;setDraft({...start,unit});drag.current={pointer:event.pointerId,dx:point.x-start.x,dy:point.y-start.y};event.currentTarget.setPointerCapture(event.pointerId);}
 function move(event){if(drag.current?.pointer!==event.pointerId)return;const point=position(event);setDraft(value=>({...value,x:clamp(point.x-drag.current.dx),y:clamp(point.y-drag.current.dy)}));}
 const unitButton=(unit,selected=false)=>{const point=selected?draft:unit.placement;return <button type="button" key={unit.id} className={'placed-sticker'+(selected?' selected-sticker':'')} style={{left:point.x*100+'%',top:point.y*100+'%',transform:`translate(-50%,-50%) rotate(${point.angle}deg)`}} aria-label={`${NAMES[art(unit.stickerId)?.rarity]}贴纸 ${art(unit.stickerId)?.shape}`} onPointerDown={event=>begin(event,unit)} onPointerMove={move} onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}} onContextMenu={event=>{event.preventDefault();event.stopPropagation();if(!draft&&!busy)setConfirm({unit,anchor:event.currentTarget});}}><StickerArt item={art(unit.stickerId)} size="100%"/></button>;};
 return <div className={'sticker-canvas'+(mode?' sticker-mode':'')}>
  <div className="sticker-mode-toolbar" role="group" aria-label="成长内容"><Tooltip text="目标"><button type="button" className="icon-button" aria-label="目标" aria-pressed={!mode} disabled={busy} onClick={()=>{setMode(false);setDraft(null);setPicker(null);}}><Target size={19}/></button></Tooltip><Tooltip text="贴纸"><button type="button" className="icon-button" aria-label="贴纸" aria-pressed={mode} disabled={busy} onClick={()=>{setMode(true);void refresh();}}><Sticker size={19}/></button></Tooltip>{error&&<button type="button" className="icon-button" aria-label="刷新贴纸" onClick={refresh}><RefreshCw size={16}/></button>}</div>
  <div className="sticker-content">{children}<div ref={surface} className="sticker-surface" aria-label="贴纸区域" role="region" tabIndex={mode?0:undefined} onPointerDown={event=>{if(!mode||busy||draft||event.target!==event.currentTarget)return;const point=position(event);setPicker(point);}}>{units.filter(unit=>unit.placement||unit.id===draft?.unit.id).map(unit=>unitButton(unit,unit.id===draft?.unit.id))}
   {draft&&<div className="sticker-edit-tools" style={{left:Math.min(80,Math.max(20,draft.x*100))+'%',top:Math.min(85,Math.max(15,draft.y*100))+'%'}} onPointerDown={event=>event.stopPropagation()}><button type="button" className="icon-button" aria-label="旋转贴纸" disabled={busy} onClick={()=>setDraft(value=>({...value,angle:value.angle>=165?-180:value.angle+15}))} onWheel={event=>{setDraft(value=>({...value,angle:((value.angle+(event.deltaY>0?5:-5)+540)%360)-180}));}}><RotateCw size={17}/></button><button type="button" className="icon-button" aria-label="固定贴纸" disabled={busy} onClick={fix}>{busy?<LoaderCircle className="progress-spin" size={17}/>:<Check size={18}/>}</button><button type="button" className="icon-button" aria-label="取消贴纸" disabled={busy} onClick={()=>{request.current=null;setDraft(null);}}><X size={17}/></button></div>}
  </div></div>
  {picker&&mode&&<div className="sticker-picker" role="dialog" aria-label="选择贴纸"><button type="button" className="icon-button" aria-label="向左浏览贴纸" onClick={()=>strip.current.scrollBy({left:-240,behavior:'smooth'})}><ChevronLeft size={18}/></button><div ref={strip} className="sticker-inventory" onWheel={event=>{event.currentTarget.scrollLeft+=Math.abs(event.deltaX)>Math.abs(event.deltaY)?event.deltaX:event.deltaY;}}>{items.map(item=>{const available=units.filter(unit=>unit.stickerId===item.id&&!unit.placement);return <button type="button" className={'sticker-choice rarity-'+item.rarity} key={item.id} aria-label={`${NAMES[item.rarity]} ${item.shape}，库存 ${available.length}`} disabled={!available.length} onClick={()=>{setDraft({unit:available[0],...picker,angle:0});setPicker(null);}}><StickerArt item={item}/><span>{available.length}</span></button>;})}</div><button type="button" className="icon-button" aria-label="向右浏览贴纸" onClick={()=>strip.current.scrollBy({left:240,behavior:'smooth'})}><ChevronRight size={18}/></button><button type="button" className="icon-button" aria-label="关闭贴纸选择" onClick={()=>setPicker(null)}><X size={17}/></button></div>}
  {mode&&error&&<p className="sticker-error connection-error" role="alert">{error}</p>}
  {confirm&&<PopConfirm anchor={confirm.anchor} label="回收贴纸确认" title="回收贴纸？" confirmLabel="回收" busyLabel="正在回收…" busy={busy} error={error} onCancel={()=>setConfirm(null)} onConfirm={()=>mutate('recycle',confirm.unit)}/>}
 </div>;
}
