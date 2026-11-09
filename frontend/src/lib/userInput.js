// Observe actual input, including the same-origin Wiki/PDF reading frames.
// Timers, focus changes and programmatic scrolling never reset idle status.
export function observeUserInput(onInput,root=document){
 const documents=new Map(),frames=new Map(),events=['keydown','pointerdown','pointermove','wheel','touchstart'];
 const input=event=>{if(event.isTrusted)onInput();};
 function detachFrame(frame){const previous=frames.get(frame);if(!previous)return;frame.removeEventListener('load',previous.load);previous.stop?.();frames.delete(frame);}
 function attachFrame(frame){
  if(frames.has(frame))return;
  const entry={stop:null,load:null};
  entry.load=()=>{entry.stop?.();entry.stop=null;try{if(frame.contentDocument)entry.stop=attachDocument(frame.contentDocument);}catch{/* Cross-origin frames keep their own input boundary. */}};
  frames.set(frame,entry);frame.addEventListener('load',entry.load);entry.load();
 }
 function scan(node){if(node.nodeType!==1)return;if(node.matches('iframe'))attachFrame(node);node.querySelectorAll('iframe').forEach(attachFrame);}
 function attachDocument(doc){
  if(documents.has(doc))return()=>{};
  for(const name of events)doc.addEventListener(name,input,{capture:true,passive:true});
  const changed=new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)scan(node);for(const frame of frames.keys())if(!frame.isConnected)detachFrame(frame);});
  changed.observe(doc,{childList:true,subtree:true});doc.querySelectorAll('iframe').forEach(attachFrame);
  const stop=()=>{changed.disconnect();for(const name of events)doc.removeEventListener(name,input,true);for(const frame of [...frames.keys()])if(frame.ownerDocument===doc)detachFrame(frame);documents.delete(doc);};
  documents.set(doc,stop);return stop;
 }
 attachDocument(root);
 return()=>{for(const stop of [...documents.values()])stop();};
}

// A native child WebView has no trusted DOM events in this document. Its
// process-owned sampler exposes only an immutable session/counter and the
// monotonic age of real input; reading it never constitutes input itself.
export function observeNativeInput(api,onInput){
 let stopped=false,timer=null,pending=null,session=null,revision=-1;
 const sample=()=>{
  if(stopped)return Promise.resolve();
  if(pending)return pending;
  clearTimeout(timer);let delay=25000;
  const started=performance.now();
  const request=(async()=>{
   try{
    const value=await api('desktop/input-activity');
    if(stopped||value?.available!==true)return;
    delay=1000;
    if(typeof value.session!=='string'||!value.session||value.session.length>128||!Number.isSafeInteger(value.revision)||value.revision<0||typeof value.observed!=='boolean')return;
    const changed=value.session!==session||value.revision>revision;
    if(value.session===session&&value.revision<revision)return;
    if(!changed)return;
    if(value.observed&&(value.revision===0||typeof value.ageSeconds!=='number'||!Number.isFinite(value.ageSeconds)||value.ageSeconds<0||value.ageSeconds>Number.MAX_SAFE_INTEGER/1000))return;
    session=value.session;revision=value.revision;
    if(value.observed)onInput(started-value.ageSeconds*1000);
   }catch{/* Old/non-native clients continue to use trusted DOM input. */}
   finally{if(!stopped)timer=setTimeout(sample,delay);}
  })();
  pending=request;
  request.finally(()=>{if(pending===request)pending=null;});
  return request;
 };
 const stop=()=>{stopped=true;clearTimeout(timer);};
 stop.sample=sample;
 void sample();
 return stop;
}
