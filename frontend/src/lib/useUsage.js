import {useEffect} from 'react';

export default function useUsage(api,enabled) {
  useEffect(()=>{
    if(!enabled)return;
    const sessionId=crypto.randomUUID();let sequence=0,last=performance.now(),active=document.visibilityState==='visible'&&document.hasFocus();
    const tick=()=>{
      const now=performance.now(),seconds=Math.min(60,(now-last)/1000),wasActive=active;last=now;
      active=document.visibilityState==='visible'&&document.hasFocus();
      if(wasActive&&seconds>=.1)api('usage',{sessionId,sequence:++sequence,seconds}).catch(()=>{});
    };
    const timer=setInterval(tick,30000);
    window.addEventListener('focus',tick);window.addEventListener('blur',tick);window.addEventListener('pagehide',tick);document.addEventListener('visibilitychange',tick);
    return()=>{clearInterval(timer);window.removeEventListener('focus',tick);window.removeEventListener('blur',tick);window.removeEventListener('pagehide',tick);document.removeEventListener('visibilitychange',tick);};
  },[api,enabled]);
}
