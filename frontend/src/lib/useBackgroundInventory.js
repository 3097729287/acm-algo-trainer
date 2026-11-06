import {useCallback,useEffect,useRef,useState} from 'react';
import {normalizeStickerInventory} from './stickerCatalogue.js';

export default function useBackgroundInventory(api,owner,enabled){
 const [snapshot,setSnapshot]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(false),generation=useRef(0),current=useRef({api,owner});current.current={api,owner};
 const accept=useCallback(value=>{if(!owner||value?.owner!==owner||!Array.isArray(value.units)||!Array.isArray(value.catalogue)||current.current.owner!==owner)return;setSnapshot(previous=>previous?.owner===owner&&previous.revision>value.revision?previous:normalizeStickerInventory(value));setError('');},[owner]);
 const refresh=useCallback(async()=>{if(!owner)return;const ticket=++generation.current;setLoading(true);try{const value=await api('stickers');if(ticket===generation.current&&current.current.owner===owner)accept(value);}catch(issue){if(ticket===generation.current&&current.current.owner===owner)setError(issue.message);}finally{if(ticket===generation.current&&current.current.owner===owner)setLoading(false);}},[api,owner,accept]);
 useEffect(()=>{generation.current++;setSnapshot(null);setError('');setLoading(false);},[owner]);
 useEffect(()=>{if(enabled)void refresh();},[enabled,refresh]);
 useEffect(()=>{const listener=event=>{if(event.detail?.inventory)accept(event.detail.inventory);else if(enabled)void refresh();};window.addEventListener('tb:sticker-rewards',listener);window.addEventListener('tb:sticker-layout-confirmed',listener);return()=>{generation.current++;window.removeEventListener('tb:sticker-rewards',listener);window.removeEventListener('tb:sticker-layout-confirmed',listener);};},[accept,refresh,enabled]);
 return {inventory:snapshot?.owner===owner?snapshot:null,error,loading,refresh,accept};
}
