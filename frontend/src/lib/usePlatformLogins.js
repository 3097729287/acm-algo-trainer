import {useEffect, useRef} from 'react';

export default function usePlatformLogins(api,enabled){
  const requested=useRef(false);
  useEffect(()=>{
    if(!enabled||requested.current||window.__tbAdmin)return;
    let alive=true;
    api('browser-preparation').then(value=>{
      if(!alive||requested.current||value.mode!=='external')return;
      requested.current=true;
      return api('browser-preparation',{action:'startup-logins'});
    }).catch(()=>{});
    return()=>{alive=false;};
  },[api,enabled]);
}
