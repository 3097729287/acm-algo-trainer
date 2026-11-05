import {useEffect,useRef,useState} from 'react';
import {Bell,Diamond,Flame,Heart,Leaf,Music2,Orbit,Rainbow,Sparkles,Star,Waves} from 'lucide-react';
import {STICKER_ANIMATIONS,playStickerSound,prepareStickerAudio} from '@/lib/stickerSound.js';
import {STICKER_FEEDBACK} from '@/lib/stickerFeedbackCatalog.js';
import {ROCKET_FLIGHT_MS} from '@/lib/rocketFlight.js';
import './StickerReaction.css';
export function useStickerReaction(owner){
 const [reactions,setReactions]=useState({}),timers=useRef(new Map()),last=useRef(new Map());
 useEffect(()=>{setReactions({});last.current.clear();if(owner)void prepareStickerAudio();return()=>{timers.current.forEach(clearTimeout);timers.current.clear();};},[owner]);
 const trigger=(unit,item)=>{
  if(!STICKER_FEEDBACK[item?.shape])return;
  const now=performance.now(),motion=item.rarity==='legendary'&&STICKER_ANIMATIONS[item.shape],special=motion&&item.shape!=='duck',duration=item.shape==='rocket'?ROCKET_FLIGHT_MS:1500;
  if(special&&now-(last.current.get(unit.id)??-Infinity)<(item.shape==='rocket'?duration:450))return;
  last.current.set(unit.id,now);playStickerSound(item.shape);
  if(!motion)return;
  clearTimeout(timers.current.get(unit.id));
  setReactions(previous=>({...previous,[unit.id]:{unitId:unit.id,shape:item.shape,kind:motion,id:now,angle:Math.random()*360}}));
  timers.current.set(unit.id,setTimeout(()=>{setReactions(previous=>{const next={...previous};delete next[unit.id];return next;});timers.current.delete(unit.id);},duration));
 };
 return [reactions,trigger];
}
export default function StickerReaction({reaction}){
 if(!reaction)return null;const Note=({duck:Music2,gem:Diamond,phoenix:Flame,dragon:Flame,envelope:Heart,orbit:Orbit,rainbow:Rainbow,telescope:Star,tower:Bell,bridge:Waves,yearbadge:Leaf})[reaction.shape]||Sparkles;
 if(reaction.shape==='dragon'){const radians=(reaction.angle||0)*Math.PI/180;return <span key={reaction.id} className="sticker-reaction reaction-dragon-solid" data-sticker-reaction="dragon" aria-hidden="true"><span className="dragon-fireball" style={{'--fire-angle':(reaction.angle||0)+'deg','--fire-x':Math.cos(radians)*150+'px','--fire-y':Math.sin(radians)*150+'px'}}><svg viewBox="0 0 90 54"><path d="M4 27C23 23 29 8 44 9L37 2C70 4 90 17 85 34 80 55 48 55 35 40L39 47C24 43 19 30 4 27Z" fill="#ee8242"/><path d="M15 27C37 24 46 13 59 18 85 24 70 46 50 38L43 33 48 39C36 37 28 29 15 27Z" fill="#ffd26f"/></svg></span></span>;}
 if(reaction.shape==='rocket')return <span key={reaction.id} className="sticker-reaction reaction-rocket" data-sticker-reaction="rocket" aria-hidden="true"><span className="rocket-plume"/>{[0,1,2,3,4].map(index=><i key={index} className="rocket-spark" style={{'--spark':index}}/>)}</span>;
 if(reaction.shape==='envelope')return <span key={reaction.id} className="sticker-reaction reaction-post-solid" data-sticker-reaction="envelope" aria-hidden="true"><Heart className="posted-heart" size={36} fill="currentColor" strokeWidth={1.5}/><span className="post-heart-trail"/></span>;
 if(reaction.shape==='telescope')return <span key={reaction.id} className="sticker-reaction reaction-telescope-beam" data-sticker-reaction="telescope" aria-hidden="true"><span className="telescope-beam"/><Star className="telescope-star" size={31} fill="currentColor"/></span>;
 return <span key={reaction.id} className={'sticker-reaction reaction-'+reaction.kind} data-sticker-reaction={reaction.shape} aria-hidden="true">{[0,1,2,3].map(index=><span className="sticker-reaction-particle" key={index} style={{'--particle':index}}><Note size={reaction.shape==='duck'?13:11}/></span>)}</span>;
}
