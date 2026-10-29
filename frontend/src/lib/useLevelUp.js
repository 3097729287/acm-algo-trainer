import {useCallback,useEffect,useRef,useState} from 'react';
import {acceptGrowth,observeLevel,acknowledgeLevel,mergeLevelNotices} from './levelNotices.js';
import {newlyUnlocked} from './featureUnlocks.js';
function localNotice(owner){try{return JSON.parse(sessionStorage.getItem(`tb.level-notice.${owner}`)||'{}');}catch{return {};}}
function remember(owner,value){try{sessionStorage.setItem(`tb.level-notice.${owner}`,JSON.stringify(value));}catch{}}
const typing=()=>!!document.activeElement?.closest?.('input,textarea,select,.cm-editor,[contenteditable=true]');
const otherDialog=()=>[...document.querySelectorAll('dialog[open],[aria-modal=true],[data-popconfirm]')].some(node=>!node.closest('[data-level-up]'));
export default function useLevelUp({owner,growth,preferences,preferencesReady,setPreferences,blocked=false}){
 const [dialog,setDialog]=useState(null),[feedback,setFeedback]=useState([]),[wake,setWake]=useState(0);
 const authority=useRef(null),latest=useRef(preferences),presented=useRef(0),shownFrom=useRef(0),scope=useRef(owner);
 latest.current=mergeLevelNotices(preferences,owner?localNotice(owner):{});
 const persist=useCallback(value=>{if(!owner)return;remember(owner,value);latest.current=value;setPreferences(previous=>{const next=mergeLevelNotices(previous,value);return Object.keys(next).every(key=>previous[key]===next[key])?previous:{...previous,...next};});},[owner,setPreferences]);
 useEffect(()=>{if(scope.current!==owner){scope.current=owner;authority.current=null;presented.current=0;shownFrom.current=0;setDialog(null);setFeedback([]);}},[owner]);
 useEffect(()=>{
  if(!owner||!preferencesReady)return;const next=acceptGrowth(authority.current,growth,owner);if(!next)return;authority.current=next;
  const state=observeLevel(latest.current,next.level);persist(state);
  setDialog(previous=>previous&&state.levelNoticePending>previous.to?{...previous,to:state.levelNoticePending,growth}:previous);
 },[owner,growth,preferencesReady,persist]);
 useEffect(()=>{
  if(!owner||!preferencesReady||!authority.current||authority.current.owner!==owner||dialog||blocked||document.hidden||typing()||otherDialog())return;
  const state=latest.current;if(state.levelNoticePending>state.levelNoticeSeen&&authority.current.level>=state.levelNoticePending){shownFrom.current=state.levelNoticeSeen;presented.current=0;setDialog({from:state.levelNoticeSeen,to:state.levelNoticePending,growth});}
 },[owner,preferencesReady,preferences.levelNoticePending,preferences.levelNoticeSeen,blocked,wake,dialog,growth]);
 useEffect(()=>{
  if(!owner)return;
  const update=()=>setWake(value=>value+1),focus=()=>setTimeout(update,0);document.addEventListener('visibilitychange',update);document.addEventListener('focusin',focus);document.addEventListener('focusout',focus);
  return()=>{document.removeEventListener('visibilitychange',update);document.removeEventListener('focusin',focus);document.removeEventListener('focusout',focus);};
 },[owner]);
 useEffect(()=>{if(!owner||dialog||!(preferences.levelNoticePending>preferences.levelNoticeSeen))return;const timer=setInterval(()=>{if(!document.hidden)setWake(value=>value+1);},500);return()=>clearInterval(timer);},[owner,dialog,preferences.levelNoticePending,preferences.levelNoticeSeen]);
 const markPresented=useCallback(level=>{if(scope.current===owner&&!document.hidden)presented.current=Math.max(presented.current,level);},[owner]);
 const close=useCallback(()=>{const seen=presented.current;if(!seen||scope.current!==owner){setDialog(null);return;}persist(acknowledgeLevel(latest.current,seen));setFeedback(newlyUnlocked(shownFrom.current,seen).map(item=>item.id));setDialog(null);},[owner,persist]);
 const clearFeedback=useCallback(()=>setFeedback([]),[]);
 return {dialog,close,markPresented,feedback,clearFeedback};
}
