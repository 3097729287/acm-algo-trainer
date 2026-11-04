import {useEffect,useRef,useState} from 'react';
import {Bell,Diamond,Flame,Heart,Leaf,Music2,Orbit,Rainbow,Sparkles,Star,Waves} from 'lucide-react';
import {STICKER_ANIMATIONS,playStickerSound,prepareStickerAudio} from '@/lib/stickerSound.js';
import {STICKER_FEEDBACK} from '@/lib/stickerFeedbackCatalog.js';
export function useStickerReaction(owner){
 const [reaction,setReaction]=useState(null),timer=useRef(),last=useRef(new Map());
 useEffect(()=>{setReaction(null);last.current.clear();if(owner)void prepareStickerAudio();return()=>clearTimeout(timer.current);},[owner]);
 const trigger=(unit,item)=>{if(!['epic','legendary'].includes(item?.rarity)||!STICKER_FEEDBACK[item.shape])return;const now=performance.now();if(now-(last.current.get(unit.id)||-Infinity)<450)return;last.current.set(unit.id,now);playStickerSound(item.shape);clearTimeout(timer.current);if(item.rarity==='legendary'){setReaction({unitId:unit.id,shape:item.shape,kind:STICKER_ANIMATIONS[item.shape]||'type',id:now});timer.current=setTimeout(()=>setReaction(null),1500);}else setReaction(null);};
 return [reaction,trigger];
}
export default function StickerReaction({reaction}){
 if(!reaction)return null;const Note=({duck:Music2,gem:Diamond,phoenix:Flame,dragon:Flame,envelope:Heart,orbit:Orbit,rainbow:Rainbow,telescope:Star,tower:Bell,bridge:Waves,yearbadge:Leaf})[reaction.shape]||Sparkles;
 return <span key={reaction.id} className={'sticker-reaction reaction-'+reaction.kind} data-sticker-reaction={reaction.shape} aria-hidden="true">{[0,1,2,3].map(index=><span className="sticker-reaction-particle" key={index} style={{'--particle':index}}><Note size={reaction.shape==='duck'?13:11}/></span>)}</span>;
}
