import { useEffect, useRef, useState } from 'react';
import { CircleCheck, CloudOff, LoaderCircle } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
export default function AccountSyncStatus() {
  const [sync,setSync] = useState(() => window.__tbAccountSync), [done,setDone] = useState(false), previous=useRef(window.__tbAccountSync), timer=useRef(null);
  useEffect(() => {
    const update = event => { const next=event.detail, before=previous.current; setSync(next); previous.current=next;
      if(next?.pending||['syncing','error'].includes(next?.status)){clearTimeout(timer.current);setDone(false);}
      if (next && !next.pending && !['syncing','error'].includes(next.status) && before && (before.pending || before.status==='syncing')) { clearTimeout(timer.current); setDone(true); timer.current=setTimeout(() => setDone(false),2200); }
    };
    window.addEventListener('tb:sync-status',update);
    return () => { window.removeEventListener('tb:sync-status',update); clearTimeout(timer.current); };
  },[]);
  const offline=sync?.offline || sync?.status==='offline';
  const waiting = !offline && (sync?.pending || sync?.status==='syncing');
  return <span className="account-sync-status">{waiting && sync?.status!=='error' ? <Tooltip text="同步中"><span className="sync-status-icon" role="status" aria-label="账号数据同步中"><LoaderCircle size={15} className="spin"/></span></Tooltip> : offline || sync?.status==='error' ? <Tooltip text={sync.error || '待同步'}><span className="sync-status-icon" aria-label={offline?'离线学习，本机已保存':'账号数据待同步'}><CloudOff size={15}/></span></Tooltip> : done ? <span className="sync-complete-toast" role="status" aria-label="账号数据已同步"><CircleCheck size={18} strokeWidth={2.5}/></span> : null}</span>;
}
