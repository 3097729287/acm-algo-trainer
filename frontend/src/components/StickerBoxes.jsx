import {useEffect,useRef,useState} from 'react';
import {Gift,LoaderCircle,X} from 'lucide-react';
import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import {StickerArt,STICKER_NAMES} from './StickerArt.jsx';
import './StickerBoxes.css';

export default function StickerBoxes({api,state,onUpdated,onClose}){
 const dialog=useRef(null),request=useRef(null),alive=useRef(true),owner=useRef(state.owner);
 const [busy,setBusy]=useState(null),[error,setError]=useState(''),[opening,setOpening]=useState(null);
 useEffect(()=>{alive.current=true;const node=dialog.current;node.showModal();return()=>{alive.current=false;node.close();};},[]);
 const boxes=Object.values(state.boxes||{}).filter(box=>!box.openedAt).sort((a,b)=>a.level-b.level),catalogue=state.catalogue||[];
 async function open(box){
  if(busy)return;setBusy(box.id);setError('');
  if(request.current?.boxId!==box.id)request.current={boxId:box.id,requestId:crypto.randomUUID()};
  try{const value=await api('stickers/open-box',request.current);if(!alive.current||value.owner!==owner.current)return;onUpdated(value);setOpening(value.opening);request.current=null;window.dispatchEvent(new Event('tb:sticker-rewards'));}
  catch(issue){if(alive.current)setError(issue.message);}
  finally{if(alive.current)setBusy(null);}
 }
 return <dialog ref={dialog} className="sticker-box-dialog" aria-labelledby="sticker-box-title" onPointerDown={dialogPointerDown} onClick={dialogBackdropClick} onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
  <header><h3 id="sticker-box-title"><Gift size={20}/>贴纸宝箱</h3><button type="button" className="icon-button" aria-label="关闭贴纸宝箱" disabled={Boolean(busy)} onClick={onClose}><X size={18}/></button></header>
  {opening&&<section className="sticker-box-result" aria-label="本次获得的贴纸"><h4>获得贴纸</h4><div>{opening.drops.map(drop=>{const item=catalogue.find(item=>item.id===drop.stickerId);return <div key={drop.id} className={'sticker-drop rarity-'+drop.rarity}><StickerArt item={item}/><span>{item?.title||item?.shape}</span><small>{STICKER_NAMES[drop.rarity]}</small></div>;})}</div></section>}
  <div className="sticker-box-list">{boxes.map(box=><section className="sticker-box-card" key={box.id} aria-label={'Lv.'+box.level+' 贴纸宝箱'}><div className="sticker-box-caption"><Gift size={28}/><strong>Lv.{box.level}</strong><span>{box.quantity} 张贴纸</span><button type="button" className="icon-button primary" aria-label={'开启 Lv.'+box.level+' 宝箱'} disabled={Boolean(busy)} onClick={()=>open(box)}>{busy===box.id?<LoaderCircle className="spin" size={18}/>:<Gift size={18}/>}</button></div><dl aria-label="每张贴纸的品质概率">{Object.entries(box.probabilities).map(([rarity,weight])=><div key={rarity} className={'rarity-'+rarity}><dt>{STICKER_NAMES[rarity]}</dt><dd>{(weight/100).toFixed(2).replace(/\.00$/,'')}%</dd></div>)}</dl></section>)}</div>
  {!boxes.length&&!opening&&<p className="progress-muted">暂无待开启的宝箱</p>}{error&&<p role="alert" className="connection-error">{error}</p>}
 </dialog>;
}
