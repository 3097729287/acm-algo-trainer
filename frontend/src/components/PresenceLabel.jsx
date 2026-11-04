import {ACTIVITY_LABELS} from '@/lib/usePresence.js';
import './PresenceLabel.css';
export default function PresenceLabel({online,activity,cached=false}){
 if(typeof online!=='boolean')return null;
 return <span className="user-presence" data-online={online} data-cached={cached||undefined} title={cached?'上次确认的在线状态，正在后台刷新':undefined}><i aria-hidden="true"/>{online?ACTIVITY_LABELS[activity]||'在线':'离线'}</span>;
}
