import {createContext,useCallback,useContext,useEffect,useState} from 'react';

export const StudyPaneContext=createContext(null);
export function useStudyPane(){return useContext(StudyPaneContext);}

// Explicit keys survive application restarts and do not depend on React IDs.
// Outside a learning tab this behaves exactly like ordinary component state.
export function useStudyState(key,initial) {
 const pane=useStudyPane();
 const identity=(pane?.scope||'')+':'+key;
 const read=()=>pane&&!pane.transient&&Object.hasOwn(pane.state,identity)?pane.state[identity]:typeof initial==='function'?initial():initial;
 const [entry,setEntry]=useState(()=>({identity,value:read()}));
 const value=entry.identity===identity?entry.value:read();
 // A reused experiment component must load the new chapter before it records
 // anything; an effect-only reset would overwrite that chapter's saved state.
 if(entry.identity!==identity)setEntry({identity,value});
 const setValue=useCallback(update=>setEntry(previous=>({identity,value:typeof update==='function'?update(previous.identity===identity?previous.value:read()):update})),[identity]);
 useEffect(()=>{if(!pane?.transient)pane?.remember(identity,value);},[value,pane?.remember,identity]);
 return [value,setValue];
}
