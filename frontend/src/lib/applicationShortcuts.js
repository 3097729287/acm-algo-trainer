import {useLayoutEffect,useRef} from 'react';
import {eventShortcut,shortcutValue} from './shortcuts.js';

const routes=new Map(),subscribers=new Set(),invocations=new Set();
let serial=0,fingerprint='',snapshot={serial:0,bindings:[]},pending=false;
const textTarget='input,textarea,select,[contenteditable]:not([contenteditable=false]),.cm-editor,[data-shortcut-input]';
export const shortcutBinding=(id,overrides={})=>({id,combo:shortcutValue(id,overrides)});
export const textSafeCombo=combo=>/(?:^|\+)(?:Ctrl|Alt|Meta)\+/i.test(combo)||/^(?:F(?:[1-9]|1\d|2[0-4])|Escape)$/i.test(combo);

function ordered(){return [...routes.values()].filter(route=>route.enabled?.()!==false).sort((a,b)=>b.priority-a.priority||a.key.localeCompare(b.key));}
function notify(){if(pending)return;pending=true;queueMicrotask(()=>{pending=false;shortcutSnapshot();for(const changed of subscribers)changed();});}
export function shortcutSnapshot(){
 const bindings=ordered().flatMap(route=>route.bindings.filter(binding=>binding.combo&&textSafeCombo(binding.combo)).map(binding=>({route:route.key,id:binding.id,combo:binding.combo,context:route.context||''})));
 const value=JSON.stringify(bindings);
 if(value!==fingerprint){fingerprint=value;snapshot={serial:++serial,bindings};}
 return snapshot;
}
export function subscribeShortcuts(listener){subscribers.add(listener);return()=>subscribers.delete(listener);}
export function subscribeShortcutInvocation(listener){invocations.add(listener);return()=>invocations.delete(listener);}
export function registerShortcutRoute({key,priority=0,context='',bindings=[],handle,enabled,target}){
 const route={key,priority,context,bindings,handle,enabled,target};routes.set(key,route);notify();
 return()=>{if(routes.get(key)===route){routes.delete(key);notify();}};
}

export function dispatchApplicationShortcut(event,{route:onlyRoute,id:onlyId,native=false}={}){
 if(event.defaultPrevented||event.isComposing||event.keyCode===229)return false;
 const combo=eventShortcut(event).toLowerCase();
 if(!combo)return false;
 for(const route of ordered()){
  if(onlyRoute&&route.key!==onlyRoute)continue;
  const binding=route.bindings.find(item=>item.combo?.toLowerCase()===combo&&(!onlyId||item.id===onlyId));
  if(!binding)continue;
  // Bare letter/list navigation retains normal text editing. Modified app
  // bindings, function keys and Escape are independent of the focused field.
  if(!textSafeCombo(binding.combo)&&event.target?.closest?.(textTarget))continue;
  if(event.repeat){event.preventDefault();event.stopPropagation?.();return true;}
  const accepted=route.handle(event,binding.id);
  if(event.defaultPrevented||accepted===true){
   for(const invoked of invocations)invoked();
   event.preventDefault();event.stopPropagation?.();return true;
  }
  if(native)return false;
 }
 return false;
}

// Only the private HTTP reader calls this with events emitted by the native
// input hook. There is no DOM CustomEvent or webpage message enqueue endpoint.
export function deliverNativeShortcut(command,registration){
 const current=shortcutSnapshot();
 if(registration!==current.serial||!Number.isFinite(command.ageSeconds)||command.ageSeconds<0||command.ageSeconds>2)return false;
 const route=routes.get(command.route),binding=route?.bindings.find(item=>item.id===command.id);
 if(!route||route.enabled?.()===false||!binding||!textSafeCombo(binding.combo))return false;
 const parts=[];let key=binding.combo,match;
 while((match=/^(Ctrl|Alt|Shift|Meta)\+/i.exec(key))){parts.push(match[1].toLowerCase());key=key.slice(match[0].length);}
 const event={key:key==='Space'?' ':key,ctrlKey:parts.includes('ctrl'),metaKey:parts.includes('meta'),altKey:parts.includes('alt'),shiftKey:parts.includes('shift'),repeat:false,isComposing:false,defaultPrevented:false,
  target:route.target?.()||document.activeElement||document.body,
  preventDefault(){this.defaultPrevented=true;},stopPropagation(){},stopImmediatePropagation(){}};
 return dispatchApplicationShortcut(event,{route:command.route,id:command.id,native:true});
}

export function useShortcutRoute({key,priority,context,bindings,handle,enabled,target,active=true}){
 const generated=useRef(crypto.randomUUID()),latest=useRef(null);latest.current={handle,enabled,target};
 const signature=JSON.stringify(bindings);
 useLayoutEffect(()=>{
  if(!active)return;
  return registerShortcutRoute({key:key||generated.current,priority,context,bindings:JSON.parse(signature),
   handle:(...args)=>latest.current.handle(...args),enabled:()=>latest.current.enabled?.()!==false,target:()=>latest.current.target?.()});
 },[key,priority,context,signature,active]);
}

if(typeof window!=='undefined')window.addEventListener('keydown',event=>dispatchApplicationShortcut(event),true);
