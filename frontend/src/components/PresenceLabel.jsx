import {ACTIVITY_LABELS} from '@/lib/usePresence.js';
import './PresenceLabel.css';
export default function PresenceLabel({online,activity}){
 if(typeof online!=='boolean')return null;
 return <span className="user-presence" data-online={online}><i aria-hidden="true"/>{online?ACTIVITY_LABELS[activity]||'在线':'离线'}</span>;
}
