import {guideAction} from '@/lib/guideActions.js';
import {StickerArt,STICKER_NAMES as NAMES} from './StickerArt.jsx';
export {StickerArt} from './StickerArt.jsx';
import {cloneElement,useCallback,useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {readStickerLayout,cacheStickerLayout} from '@/lib/stickerCache.js';
import {createPortal} from 'react-dom';
import {fitStickerPlacement,stickerSize} from '@/lib/stickerPlacement.js';
import {Gift,Layers,RefreshCw,Sticker,Target,X} from 'lucide-react';
import {readStickerOrder,bringStickerForward} from '@/lib/stickerOrder.js';
import {BackgroundArt,WeatherArt} from './SceneStickerArt.jsx';
import {StickerScenePresets,StickerWardrobe} from './StickerScenePanels.jsx';
import {previewPreset,stickerWeather} from '@/lib/stickerScenes.js';
import StickerBoxes from './StickerBoxes.jsx';
import PopConfirm from './PopConfirm.jsx';
import Tooltip from './Tooltip.jsx';
import StickerReaction,{useStickerReaction} from './StickerReaction.jsx';
import './StickerCanvas.css';

const ORDER={legendary:0,epic:1,rare:2,common:3};

export default function StickerCanvas({api,owner,children,statistics,goals}){
 const [toolbarHost,setToolbarHost]=useState(null);
 useLayoutEffect(()=>{setToolbarHost(document.querySelector('.app-statusbar'));},[]);
 const [boxesOpen,setBoxesOpen]=useState(false),[goalsOpen,setGoalsOpen]=useState(false);
 const [mode,setMode]=useState(false),[state,setState]=useState(()=>readStickerLayout(owner)),[draft,setDraft]=useState(null),[picker,setPicker]=useState(null),[confirm,setConfirm]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const surface=useRef(null),drag=useRef(null),alive=useRef(owner),request=useRef(null),saving=useRef(null),revision=useRef(0),latest=useRef(null);
 const placements=useRef(new Map()),[optimistic,setOptimistic]=useState(new Map());
 const [bounds,setBounds]=useState({width:0,height:0});
 const [stack,setStack]=useState(()=>({owner,ids:readStickerOrder(owner)})),stackRef=useRef(stack);
 useLayoutEffect(()=>{const next={owner,ids:readStickerOrder(owner)};stackRef.current=next;setStack(next);},[owner]);
 const promote=id=>{const ids=bringStickerForward(owner,stackRef.current.owner===owner?stackRef.current.ids:readStickerOrder(owner),id);stackRef.current={owner,ids};setStack(stackRef.current);};
 const [reaction,reactToSticker]=useStickerReaction(owner),movedUnit=useRef(null);
 const recycling=useRef(new Map()),recycleRequests=useRef(new Map()),[pendingRecycles,setPendingRecycles]=useState(new Set());
 const [recycleError,setRecycleError]=useState('');
 const [wardrobe,setWardrobe]=useState(null),[outfitPreview,setOutfitPreview]=useState(null),[scenesOpen,setScenesOpen]=useState(false),[scenePreview,setScenePreview]=useState(null),[sceneStatus,setSceneStatus]=useState(''),[pickerKind,setPickerKind]=useState('sticker');
 const sceneRequests=useRef(new Map());
 useLayoutEffect(()=>{const node=surface.current;if(!node)return;const measure=()=>{const box=node.getBoundingClientRect();setBounds(previous=>previous.width===box.width&&previous.height===box.height?previous:{width:box.width,height:box.height});};measure();const observer=new ResizeObserver(measure);observer.observe(node);return()=>observer.disconnect();},[]);
 const fit=(value,unit=value?.unit)=>fitStickerPlacement(value,bounds,state?.catalogue?.find(item=>item.id===unit?.stickerId));
 alive.current=owner;
 const accept=useCallback((value,expected)=>{if(!value||typeof expected!=='string'||!expected||alive.current!==expected||value.owner!==expected||!Array.isArray(value.catalogue)||!Array.isArray(value.units)||latest.current&&value.revision<latest.current.revision)return false;latest.current=value;cacheStickerLayout(value,expected);setState(value);return true;},[]);
 const refresh=useCallback(async()=>{const expected=owner,seq=++revision.current;try{const value=await api('stickers');if(seq===revision.current&&accept(value,expected))setError(value.rewardSyncError||'');}catch(issue){if(alive.current===expected&&seq===revision.current)setError(issue.message);}},[api,owner,accept]);
 useLayoutEffect(()=>{revision.current++;saving.current=null;request.current=null;drag.current=null;latest.current=readStickerLayout(owner);placements.current=new Map();setOptimistic(new Map());recycling.current=new Map();recycleRequests.current=new Map();setPendingRecycles(new Set());setRecycleError('');setBusy(false);setError('');setState(readStickerLayout(owner));setDraft(null);setPicker(null);setConfirm(null);setMode(false);setGoalsOpen(false);setBoxesOpen(false);setWardrobe(null);setOutfitPreview(null);setScenesOpen(false);setScenePreview(null);setSceneStatus('');sceneRequests.current=new Map();void refresh();},[refresh]);
 useEffect(()=>{const listener=event=>{const value=event.detail?.inventory;if(value){if(accept(value,owner))setError(value.rewardSyncError||'');}else void refresh();};window.addEventListener('tb:sticker-rewards',listener);window.addEventListener('focus',listener);return()=>{window.removeEventListener('tb:sticker-rewards',listener);window.removeEventListener('focus',listener);};},[refresh,accept,owner]);
 // Render immediately, then serialize inventory writes in the background.
 // Newer gestures on a unit supersede its queued point, never its in-flight
 // request ID. Lost responses can therefore be retried without another grant.
 const flushPlacements=useCallback(async()=>{
  const pending=placements.current;if(saving.current||!pending.size)return;
  const operation={};saving.current=operation;const expected=owner;
  try{
   while(pending.size&&placements.current===pending&&alive.current===expected){
    const [id,change]=pending.entries().next().value;
    const unit=latest.current?.units?.find(value=>value.id===id)||change.unit;
    change.payload??={unitId:id,revision:unit.revision,...change.point,requestId:crypto.randomUUID()};
    try{
     const result=await api('stickers/place',change.payload);
     if(saving.current!==operation||alive.current!==expected||placements.current!==pending)return;
     if(result?.owner!==expected)throw new Error('贴纸库存响应无效');
     accept(result,expected);setError('');
     if(pending.get(id)===change)pending.delete(id);
     setOptimistic(new Map(pending));
    }catch(issue){
     if(saving.current!==operation||alive.current!==expected||placements.current!==pending)return;
     setError(issue.message);
     if([404,409].includes(issue.status)){
      pending.delete(id);setOptimistic(new Map(pending));
      setDraft(value=>value?.unit.id===id?null:value);await refresh();
     }else break;
    }
   }
  }finally{if(saving.current===operation)saving.current=null;}
 },[api,owner,accept,refresh]);
 const place=(unit,point)=>{
  const {x,y,angle,scale}=fit(point,unit),position={x,y,angle,...(canScale?{scale:scale??1}:{})};
  const current=placements.current.get(unit.id)?.point||latest.current?.units?.find(value=>value.id===unit.id)?.placement||unit.placement;
  if(current&&['x','y','angle','scale'].every(key=>Math.abs((current[key]??(key==='scale'?1:0))-(position[key]??(key==='scale'?1:0)))<1e-8))return;
  promote(unit.id);
  placements.current.set(unit.id,{unit,point:position});setOptimistic(new Map(placements.current));
  revision.current++;setError('');void flushPlacements();
 };
 useEffect(()=>{const retry=()=>{void flushPlacements();};window.addEventListener('online',retry);window.addEventListener('focus',retry);return()=>{window.removeEventListener('online',retry);window.removeEventListener('focus',retry);};},[flushPlacements]);
 const recycle=useCallback(async unit=>{
  if(recycling.current.has(unit.id)||placements.current.has(unit.id))return;
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
 const pendingRewardCount=Object.values(state?.boxes||{}).filter(box=>!box.openedAt).length+Object.values(state?.backgroundRewards||{}).filter(reward=>!reward.openedAt).length;
 const canScale=Boolean(state?.placementPolicy?.scale);
 const fix=()=>{if(draft){place(draft.unit,draft);drag.current=null;setDraft(null);setPicker(null);}};
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
 const owned=Boolean(state&&typeof owner==='string'&&owner&&state.owner===owner);
 const visibleState=scenePreview||state;
 const items=useMemo(()=>[...(owned?visibleState.catalogue||[]:[])].sort((a,b)=>ORDER[a.rarity]-ORDER[b.rarity]||a.id.localeCompare(b.id)),[owned,visibleState?.catalogue]);
 const byId=useMemo(()=>new Map(items.map(item=>[item.id,item])),[items]);
 const units=owned?(visibleState.units||[]).filter(unit=>!pendingRecycles.has(unit.id)):[],art=id=>byId.get(id);
 const stackIds=stack.owner===owner?stack.ids:readStickerOrder(owner),layerById=new Map(units.map((unit,index)=>[unit.id,index+1]));
 stackIds.forEach((id,index)=>layerById.set(id,units.length+index+1));
 const displayUnits=units.map(unit=>({...unit,placement:unit.id===draft?.unit.id?draft:optimistic.get(unit.id)?.point||unit.placement}));
 const pendingBackground=[...optimistic.values()].filter(change=>art(change.unit.stickerId)?.kind==='background').at(-1)?.unit.id;
 const background=displayUnits.find(unit=>art(unit.stickerId)?.kind==='background'&&unit.placement&&(!pendingBackground||unit.id===pendingBackground));
 const weather=stickerWeather(displayUnits,byId,bounds);
 const availableItems=items.filter(item=>(item.kind==='background')===(pickerKind==='background')&&units.some(unit=>unit.stickerId===item.id&&(item.kind==='background'||!unit.placement&&!optimistic.has(unit.id)&&unit.id!==draft?.unit.id)));
 const sceneBlocked=busy||Boolean(draft)||optimistic.size>0||Boolean(saving.current)||visibleState?.cachedPlacementOnly;
 async function sceneAction(kind,values){
  if(sceneBlocked)return;const expected=owner;
  const signature=JSON.stringify([kind,values]);let payload=sceneRequests.current.get(signature);
  if(!payload){payload={...values,inventoryRevision:latest.current.revision,requestId:crypto.randomUUID()};sceneRequests.current.set(signature,payload);}
  setBusy(true);setError('');setSceneStatus('');setPicker(null);
  if(kind==='scene-apply'){const preset=latest.current.scenePresets.find(p=>p.id===values.presetId);if(preset)setScenePreview(previewPreset(preset,latest.current));}
  try{const value=await api('stickers/'+kind,payload);if(alive.current!==expected)return;if(!accept(value,expected))throw new Error('场景响应无效');sceneRequests.current.delete(signature);guideAction(kind);setSceneStatus(value.scene?.missing.length?`已切换，暂时跳过 ${value.scene.missing.length} 张缺少的贴纸。`:kind==='scene-save'?'场景已保存':kind==='scene-delete'?'预设已删除':'场景已切换');}
  catch(issue){if(alive.current===expected){setError(issue.message);setSceneStatus(issue.message);if([404,409].includes(issue.status)){sceneRequests.current.delete(signature);void refresh();}}}
  finally{if(alive.current===expected){setScenePreview(null);setBusy(false);}}
 }
 async function wear(appearance){
  if(!wardrobe||busy||optimistic.size)return;const expected=owner,unit=latest.current.units.find(u=>u.id===wardrobe.unit.id);if(!unit)return;
  setWardrobe(null);setOutfitPreview({id:unit.id,appearance});setBusy(true);setError('');
  try{const value=await api('stickers/outfit',{unitId:unit.id,revision:unit.revision,appearance,requestId:crypto.randomUUID()});if(alive.current!==expected)return;if(!accept(value,expected))throw new Error('服装响应无效');}
  catch(issue){if(alive.current===expected){setError(issue.message);void refresh();}}
  finally{if(alive.current===expected){setOutfitPreview(null);setBusy(false);}}
 }
 function openPicker(event,kind){if(busy)return;if(draft)fix();setGoalsOpen(false);setMode(true);setPickerKind(kind);setScenesOpen(false);setPicker({x:.5,y:.5,angle:0,screenX:event.clientX,screenY:event.clientY-410});}

 const pickerWidth=Math.min(428,window.innerWidth-24),pickerHeight=Math.min(376,window.innerHeight-24);
 const pickerStyle=picker?{width:pickerWidth,left:Math.max(8,Math.min(picker.screenX-pickerWidth/2,window.innerWidth-pickerWidth-8)),top:Math.max(8,Math.min(picker.screenY+10,window.innerHeight-pickerHeight-12))}:undefined;
 function position(event){const box=surface.current.getBoundingClientRect();return {x:(event.clientX-box.left)/box.width,y:(event.clientY-box.top)/box.height};}
 function begin(event,unit){
  if(event.button!==0||!mode||busy)return;event.preventDefault();event.stopPropagation();
  const point=position(event),start=fit(draft?.unit.id===unit.id?draft:optimistic.get(unit.id)?.point||unit.placement,unit);
  const r=surface.current.getBoundingClientRect(),cx=r.left+start.x*r.width,cy=r.top+start.y*r.height;
  const edge=event.target.closest('[data-sticker-edge]')?.dataset.stickerEdge,corner=event.target.closest('[data-sticker-corner]');
  const radians=start.angle*Math.PI/180,axis=edge==='north'||edge==='south'?'y':'x';
  const project=(x,y)=>axis==='y'?-(x-cx)*Math.sin(radians)+(y-cy)*Math.cos(radians):(x-cx)*Math.cos(radians)+(y-cy)*Math.sin(radians);
  setDraft({...start,unit});setPicker(null);setConfirm(null);movedUnit.current=null;
  drag.current={kind:corner?'rotate':edge&&canScale?'scale':'move',pointer:event.pointerId,unit,point:start,startX:event.clientX,startY:event.clientY,dx:point.x-start.x,dy:point.y-start.y,cx,cy,start:Math.atan2(event.clientY-cy,event.clientX-cx),project,distance:Math.max(1,Math.abs(project(event.clientX,event.clientY))),changed:false};
  event.currentTarget.setPointerCapture(event.pointerId);
 }
 function move(event){
  const active=drag.current;if(active?.pointer!==event.pointerId)return;
  if(!active.changed&&Math.hypot(event.clientX-active.startX,event.clientY-active.startY)<=4)return;
  if(!active.changed)promote(active.unit.id);
  active.changed=true;movedUnit.current=active.unit.id;let point;
  if(active.kind==='rotate'){
   const delta=(Math.atan2(event.clientY-active.cy,event.clientX-active.cx)-active.start)*180/Math.PI;
   point={...active.point,angle:Math.round((active.point.angle+delta)*10)/10};
  }else if(active.kind==='scale'){
   point={...active.point,scale:Math.round((active.point.scale??1)*Math.abs(active.project(event.clientX,event.clientY))/active.distance*1000)/1000};
  }else{const next=position(event);point={...active.point,x:next.x-active.dx,y:next.y-active.dy};}
  active.current=fit(point,active.unit);setDraft({...active.current,unit:active.unit});
 }
 function end(event,cancel=false){
  const active=drag.current;if(active?.pointer!==event.pointerId)return;drag.current=null;
  if(cancel){setDraft({...active.point,unit:active.unit});movedUnit.current=active.unit.id;}
  else if(active.changed)place(active.unit,active.current);
 }
 const unitButton=(unit,selected=false)=>{
  const point=fit(selected?draft:optimistic.get(unit.id)?.point||unit.placement,unit),item=art(unit.stickerId),effect=!mode&&reaction?.unitId===unit.id?reaction:null;
  return <button type="button" key={unit.id} className={'placed-sticker'+(selected?' selected-sticker':'')+(effect?' legendary-reacting':'')+(!mode&&weather.hidden.has(unit.id)?' weather-component-hidden':'')} data-unit-id={unit.id} data-rarity={item?.rarity} title={item?.title} style={{zIndex:selected?units.length+stackIds.length+2:layerById.get(unit.id)||1,left:point.x*100+'%',top:point.y*100+'%',width:stickerSize(bounds,point.scale,item)+'px',transform:`translate(-50%,-50%) rotate(${point.angle}deg)`}} aria-label={`${NAMES[item?.rarity]}贴纸 ${item?.shape}`} onPointerDown={event=>begin(event,unit)} onPointerMove={move} onPointerUp={event=>end(event)} onPointerCancel={event=>end(event,true)} onClick={event=>{event.stopPropagation();if(busy)return;if(movedUnit.current===unit.id){movedUnit.current=null;return;}if(item?.shape?.startsWith('person')&&state.wardrobe&&!busy&&!optimistic.size){setDraft(null);setWardrobe({unit,item});}else if(!mode)reactToSticker(unit,item);else if(!draft||draft.unit.id!==unit.id)setDraft({...point,unit});}} onContextMenu={event=>{event.preventDefault();event.stopPropagation();if(!busy&&!placements.current.has(unit.id)){setDraft(null);setConfirm({unit,anchor:event.currentTarget});}}}>{weather.effects.has(unit.id)?<WeatherArt type={weather.effects.get(unit.id)}/>:<StickerArt item={item} size="100%" appearance={outfitPreview?.id===unit.id?outfitPreview.appearance:unit.appearance}/>}{selected&&<span className="sticker-transform-frame" aria-hidden="true">{canScale&&['north','east','south','west'].map(edge=><span key={edge} className={'sticker-transform-edge '+edge} data-sticker-edge={edge}/>)}{['nw','ne','sw','se'].map(corner=><span key={corner} className={'sticker-transform-corner '+corner} data-sticker-corner={corner}/>)}</span>}{effect&&<StickerReaction reaction={effect}/>}</button>;
 };
 return <div className={'sticker-canvas'+(mode?' sticker-mode':'')}>

  <div className="sticker-content">{children}<div ref={surface} className="sticker-surface" aria-label="贴纸区域" role="region" tabIndex={mode?0:undefined} onPointerDown={event=>{if(event.button!==0||!mode||busy||event.target!==event.currentTarget)return;if(draft){fix();return;}setConfirm(null);setPickerKind('sticker');const point=position(event);setPicker({...fit({...point,angle:0}),screenX:event.clientX,screenY:event.clientY});}}>{background&&<div className="scene-background-layer"><BackgroundArt item={art(background.stickerId)}/></div>}{units.filter(unit=>art(unit.stickerId)?.kind!=='background'&&(unit.placement||optimistic.has(unit.id)||unit.id===draft?.unit.id)).map(unit=>unitButton(unit,unit.id===draft?.unit.id))}
  </div></div>
  {picker&&mode&&createPortal(<div className="sticker-picker" style={pickerStyle} role="dialog" aria-label={pickerKind==='background'?'选择背景':'选择贴纸'}><nav className="sticker-picker-tabs"><button type="button" aria-pressed={pickerKind==='sticker'} onClick={()=>setPickerKind('sticker')}>贴纸</button><button type="button" aria-pressed={pickerKind==='background'} onClick={()=>setPickerKind('background')}>背景</button>{pickerKind==='background'&&background&&<button type="button" disabled={busy} onClick={()=>{void recycle(background);setPicker(null);}}>收起背景</button>}</nav><div className="sticker-inventory">{availableItems.map(item=>{const available=units.filter(unit=>unit.stickerId===item.id&&(item.kind==='background'||!unit.placement&&!optimistic.has(unit.id)&&unit.id!==draft?.unit.id));return <button type="button" className={'sticker-choice rarity-'+item.rarity} key={item.id} aria-label={`${NAMES[item.rarity]} ${item.shape}，库存 ${available.length}`} disabled={!available.length} onClick={()=>{if(item.kind==='background')place(available[0],{x:.5,y:.5,angle:0,scale:1});else setDraft({...fit({x:picker.x,y:picker.y,angle:0,scale:1},available[0]),unit:available[0]});setPicker(null);}}><StickerArt item={item}/><span>{available.length}</span></button>;})}{!availableItems.length&&<p className="sticker-empty-inventory">{pickerKind==='background'?'完成默认时长的重现赛，至少 AC 2 题且用时达到一半，可获得一张背景。':'暂无可摆放的库存贴纸'}</p>}</div><button type="button" className="icon-button" aria-label="关闭贴纸选择" onClick={()=>setPicker(null)}><X size={17}/></button></div>,document.body)}
  {statistics}
  {wardrobe&&<StickerWardrobe {...wardrobe} choices={state.wardrobe} onClose={()=>setWardrobe(null)} onSave={wear}/>}
  {scenesOpen&&owned&&<StickerScenePresets state={visibleState} disabled={sceneBlocked} status={sceneStatus||(optimistic.size?'正在保存位置…':'')} onClose={()=>setScenesOpen(false)} onSave={(name,presetId)=>void sceneAction('scene-save',{name,...(presetId?{presetId}:{})})} onApply={preset=>void sceneAction('scene-apply',{presetId:preset.id})} onDelete={presetId=>void sceneAction('scene-delete',{presetId})}/>}
  {toolbarHost&&createPortal(<div className="growth-footer-actions" role="group" aria-label="成长内容">{state?.capabilities?.scenes&&<><Tooltip text="场景预设"><button type="button" className="achievement-top-button" aria-label="场景预设" aria-pressed={scenesOpen} disabled={busy} onClick={()=>{if(draft)fix();setScenesOpen(v=>!v);setGoalsOpen(false);setPicker(null);}}><Layers size={19}/></button></Tooltip></>}{<Tooltip text="卡包"><button type="button" className="achievement-top-button sticker-box-trigger" aria-label="卡包" disabled={busy||Boolean(draft)||!state} onClick={()=>setBoxesOpen(true)}><Gift size={19}/>{pendingRewardCount>0&&<small>{pendingRewardCount}</small>}</button></Tooltip>}<Tooltip text="目标"><button type="button" className="achievement-top-button" aria-label="目标" aria-expanded={goalsOpen} aria-pressed={goalsOpen} disabled={busy} onClick={()=>{setGoalsOpen(value=>!value);setMode(false);setDraft(null);setPicker(null);setConfirm(null);drag.current=null;request.current=null;}}><Target size={19}/></button></Tooltip><Tooltip text="贴纸"><button type="button" className="achievement-top-button" aria-label="贴纸" aria-pressed={mode} disabled={busy} onClick={()=>{setGoalsOpen(false);setMode(value=>!value);setDraft(null);setPicker(null);setConfirm(null);drag.current=null;request.current=null;void refresh();}}><Sticker size={19}/></button></Tooltip>{error&&<button type="button" className="achievement-top-button" aria-label="刷新贴纸" onClick={refresh}><RefreshCw size={16}/></button>}</div>,toolbarHost)}
  {goalsOpen&&!mode&&goals&&cloneElement(goals,{onClose:()=>setGoalsOpen(false)})}
  {(recycleError||mode&&error)&&<p className="sticker-error connection-error" role="alert">{recycleError||error}</p>}
  {boxesOpen&&owned&&<StickerBoxes api={api} state={state} onUpdated={value=>accept(value,owner)} onClose={()=>setBoxesOpen(false)}/>}
  {confirm&&<PopConfirm anchor={confirm.anchor} label="回收贴纸确认" title="回收贴纸？" confirmLabel="回收" busyLabel="正在回收…" busy={busy} error={error} onCancel={()=>setConfirm(null)} onConfirm={()=>recycle(confirm.unit)}/>}
 </div>;
}
