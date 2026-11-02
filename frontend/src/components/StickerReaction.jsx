import {useEffect,useRef,useState} from 'react';
import {Diamond,Flame,Heart,Music2,Orbit,Rainbow,Sparkles} from 'lucide-react';
import {LEGENDARY_FEEDBACK,playStickerSound,prepareStickerAudio} from '@/lib/stickerSound.js';
export function useStickerReaction(owner){
 const [reaction,setReaction]=useState(null),timer=useRef(),last=useRef(new Map());
 useEffect(()=>{setReaction(null);last.current.clear();if(owner)void prepareStickerAudio();return()=>clearTimeout(timer.current);},[owner]);
 const trigger=(unit,item)=>{if(item?.rarity!=='legendary'||!LEGENDARY_FEEDBACK[item.shape])return;const now=performance.now();if(now-(last.current.get(unit.id)||-Infinity)<450)return;last.current.set(unit.id,now);playStickerSound(item.shape);clearTimeout(timer.current);setReaction({unitId:unit.id,shape:item.shape,kind:LEGENDARY_FEEDBACK[item.shape],id:now});timer.current=setTimeout(()=>setReaction(null),1250);};
 return [reaction,trigger];
}
export default function StickerReaction({reaction}){
 if(!reaction)return null;const Note=({duck:Music2,gem:Diamond,phoenix:Flame,envelope:Heart,orbit:Orbit,rainbow:Rainbow})[reaction.shape]||Sparkles;
 return <span key={reaction.id} className={'sticker-reaction reaction-'+reaction.kind} data-sticker-reaction={reaction.shape} aria-hidden="true">{[0,1,2,3].map(index=><span className="sticker-reaction-particle" key={index} style={{'--particle':index}}><Note size={reaction.shape==='duck'?13:11}/></span>)}</span>;
}
