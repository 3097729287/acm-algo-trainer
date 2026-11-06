import {canonicalStickerId} from '@/lib/stickerCatalogue.js';
import {useEffect,useRef,useState} from 'react';
import {ArrowRight,Check,Eye,Gift,LoaderCircle,RotateCcw,Sparkles,X} from 'lucide-react';
import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import {StickerArt} from './StickerArt.jsx';
import './StickerBoxes.css';

export const PACK_NAMES={common:'普通',rare:'稀有',epic:'史诗',legendary:'传奇'};
const tiers=Object.keys(PACK_NAMES),quantities={common:3,rare:4,epic:5,legendary:6};
export function PackArtwork({rarity='common',opening=false}){
 return <div className={'card-pack-art pack-'+rarity+(opening?' pack-breaking':'')} aria-hidden="true">
  <div className="pack-aura"/><div className="pack-wrapper"><div className="pack-foil"/><div className="pack-trim"/>
   <span className="pack-brand">ToBe</span><div className="pack-seal"><Sparkles strokeWidth={1}/></div>
   <strong>{rarity==='background'?'背景':PACK_NAMES[rarity]}</strong><span className="pack-card-dots">{Array.from({length:quantities[rarity]||1},(_,i)=><i key={i}/>)}</span>
  </div><div className="pack-tear"/><div className="pack-rays"/>
 </div>;
}

export default function StickerBoxes({api,state,owner:accountId,loading=false,inventoryError='',onRefresh,onUpdated,onClose}){
 const dialog=useRef(null),request=useRef(null),alive=useRef(true),owner=useRef(accountId||state?.owner),inFlight=useRef(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[opening,setOpening]=useState(null),[selected,setSelected]=useState(null);
 const [stage,setStage]=useState('packs'),[draw,setDraw]=useState(null),[packIndex,setPackIndex]=useState(0),[revealed,setRevealed]=useState(new Set());
 useEffect(()=>{alive.current=true;const node=dialog.current;node.showModal();return()=>{alive.current=false;node.close();};},[]);
 const boxes=Object.values(state?.boxes||{}).filter(box=>!box.openedAt),catalogue=state?.catalogue||[];
 const groups=tiers.map(rarity=>({rarity,boxes:boxes.filter(box=>(box.rarity||(box.level?'legendary':'common'))===rarity)})).filter(group=>group.boxes.length);
 const backgrounds=Object.values(state?.backgroundRewards||{}).filter(reward=>!reward.openedAt);
 if(backgrounds.length)groups.push({rarity:'background',boxes:backgrounds});
 const current=groups.find(group=>group.rarity===selected)||groups[0];
 const packs=opening?.packs||(opening?[opening]:[]),cards=packs[packIndex]?.drops||[];
 const allRevealed=cards.length>0&&cards.every(card=>revealed.has(card.id));
 async function open(rarity,count){
  if(inFlight.current||!state)return;
  const payload=request.current||{rarity,count,requestId:crypto.randomUUID(),...(rarity==='background'?{rewardId:current.boxes[0].id}:{})};
  request.current=payload;inFlight.current=true;setBusy(true);setError('');setDraw(payload);setStage('opening');
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  try{
   const [value]=await Promise.all([api(payload.rarity==='background'?'stickers/open-background':'stickers/open-packs',payload.rarity==='background'?{requestId:payload.requestId,rewardId:payload.rewardId}:payload),new Promise(resolve=>setTimeout(resolve,reduced?0:1500))]);
   if(!alive.current||value.owner!==owner.current)return;
   if(!value.opening||!Array.isArray(value.opening.drops)||value.opening.drops.length===0)throw new Error('开包结果尚未收到，请重试');
   onUpdated(value);setOpening({...value.opening,drops:value.opening.drops.map(drop=>({...drop,stickerId:canonicalStickerId(drop.stickerId)})),...(value.opening.packs?{packs:value.opening.packs.map(pack=>({...pack,drops:pack.drops.map(drop=>({...drop,stickerId:canonicalStickerId(drop.stickerId)}))}))}:{})});setPackIndex(0);setRevealed(new Set());setStage('cards');request.current=null;
   window.dispatchEvent(new CustomEvent('tb:sticker-rewards',{detail:{inventory:value}}));
  }catch(issue){if(alive.current){setError(issue.message);setStage('packs');}}
  finally{inFlight.current=false;if(alive.current)setBusy(false);}
 }
 function advance(){
  if(!allRevealed){setRevealed(new Set(cards.map(card=>card.id)));return;}
  if(packIndex+1<packs.length){setPackIndex(value=>value+1);setRevealed(new Set());}
  else{setOpening(null);setStage('packs');setDraw(null);setSelected(null);}
 }
 return <dialog ref={dialog} className={'sticker-box-dialog card-pack-dialog stage-'+stage} aria-labelledby="sticker-box-title" onPointerDown={event=>{if(!busy)dialogPointerDown(event);}} onClick={event=>{if(!busy)dialogBackdropClick(event);}} onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
  <header><h3 id="sticker-box-title"><Gift size={20}/>卡包</h3><button type="button" className="icon-button" aria-label="关闭卡包" disabled={busy} onClick={onClose}><X size={18}/></button></header>
  {stage==='packs'&&!state&&<div className="pack-inventory-status">
   {loading?<p role="status"><LoaderCircle size={20} className="spin"/>正在读取卡包</p>:<><p role="alert" className="connection-error">{inventoryError||'暂时无法读取卡包'}</p><button type="button" className="progress-button" onClick={onRefresh}><RotateCcw size={16}/>重新读取</button></>}
  </div>}
  {stage==='packs'&&state&&<>
   <div className="pack-selection" role="group" aria-label="持有的卡包">{groups.map(group=><button type="button" key={group.rarity} className={'pack-selection-item pack-'+group.rarity+(current?.rarity===group.rarity?' pack-selected':'')} aria-label={`${group.rarity==='background'?'背景奖励':PACK_NAMES[group.rarity]+'卡包'} ${group.boxes.length} 个`} aria-pressed={current?.rarity===group.rarity} disabled={busy||Boolean(request.current)} onClick={()=>setSelected(group.rarity)}>
    <PackArtwork rarity={group.rarity}/><span>{group.rarity==='background'?'背景奖励':PACK_NAMES[group.rarity]+'卡包'} <b>× {group.boxes.length}</b></span>
   </button>)}</div>
   {current&&<div className={'pack-details pack-'+current.rarity}>
    <div className="pack-draw-actions"><button type="button" className="progress-button progress-primary" disabled={busy||Boolean(request.current)} onClick={()=>open(current.rarity,1)}><Sparkles size={18}/>抽卡</button>{current.rarity!=='background'&&<button type="button" className="progress-button" disabled={busy||Boolean(request.current)||current.boxes.length<5} onClick={()=>open(current.rarity,5)}>五连抽</button>}</div>
   </div>}
   {!groups.length&&<p className="pack-empty">暂无待开启的卡包</p>}
   {error&&<div className="pack-error"><p role="alert" className="connection-error">{error}</p>{request.current&&<button type="button" className="progress-button" onClick={()=>open(request.current.rarity,request.current.count)}><RotateCcw size={16}/>重试</button>}</div>}
  </>}
  {stage==='opening'&&<div className={'pack-opening-scene pack-'+draw.rarity} role="status" aria-label="正在开包"><div className="pack-opening-halo"/><PackArtwork rarity={draw.rarity} opening/><span className="pack-opening-caption"><LoaderCircle size={18} className="spin"/>正在开包{draw.count===5?' · 五连抽':''}</span></div>}
  {stage==='cards'&&<section className="pack-result" aria-label="本次获得的贴纸">
   <div className="pack-result-caption"><h4>{opening?.kind==='background'?'获得背景':'获得贴纸'}</h4>{packs.length>1&&<span>{packIndex+1} / {packs.length}</span>}</div>
   <div className="pack-reveal-grid" style={{'--card-count':cards.length}} key={packIndex}>{cards.map((card,index)=>{
    const item=catalogue.find(item=>item.id===card.stickerId),face=revealed.has(card.id),background=opening?.kind==='background';
    return <button type="button" key={card.id} className={'pack-result-card pack-'+(background?'background':card.rarity)+(face?' card-revealed':'')} style={{'--card-index':index}} aria-label={face?`${background?'动效背景':PACK_NAMES[card.rarity]+'贴纸'} ${item?.title||item?.shape}`:`翻开第 ${index+1} 张${background?'背景':'贴纸'}`} aria-pressed={face} onClick={()=>setRevealed(previous=>new Set([...previous,card.id]))}>
     <div className="pack-card-turn"><div className="pack-card-back"><div className="pack-card-border"/><Sparkles size={34} strokeWidth={1}/><span>ToBe</span></div><div className="pack-card-front"><span className="card-rarity-mark"/><StickerArt item={item} size={96}/><strong>{item?.title||item?.shape}</strong><small>{background?'动效背景':PACK_NAMES[card.rarity]}</small></div></div>
    </button>;
   })}</div>
   <div className="pack-result-actions"><button type="button" className="progress-button progress-primary" onClick={advance}>{!allRevealed?<><Eye size={18}/>全部翻开</>:packIndex+1<packs.length?<><ArrowRight size={18}/>下一包</>:<><Check size={18}/>完成</>}</button></div>
  </section>}
 </dialog>;
}
