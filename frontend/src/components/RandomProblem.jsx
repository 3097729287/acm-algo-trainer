import {useRef,useState} from 'react';
import {Dices,LoaderCircle} from 'lucide-react';
import PopConfirm from './PopConfirm.jsx';
import Tooltip from './Tooltip.jsx';
import {uniformIndex} from '@/lib/uniformRandom.js';
export default function RandomProblem({rows,disabled,onChoose,onError}) {
  const [anchor,setAnchor]=useState(null),[opening,setOpening]=useState(false),pending=useRef(false);
  async function confirm() {
    if(pending.current||disabled||!rows.length)return;
    pending.current=true;setOpening(true);
    try{await onChoose(rows[uniformIndex(rows.length)].id);setAnchor(null);}
    catch(error){onError?.(error);}
    finally{pending.current=false;setOpening(false);}
  }
  return <><Tooltip text="随机单题"><button type="button" className="icon-button catalog-random" aria-label="随机单题" disabled={disabled||opening||!rows.length} onClick={event=>setAnchor(event.currentTarget)}>{opening?<LoaderCircle className="spin" size={18}/>:<Dices size={18}/>}</button></Tooltip>{anchor&&<PopConfirm anchor={anchor} label="随机单题确认" title="随机选择一道题？" busy={opening} onCancel={()=>{setAnchor(null);anchor.focus();}} onConfirm={confirm} confirmLabel="确认" busyLabel="正在打开…" confirmTone="primary"/>}</>;
}
