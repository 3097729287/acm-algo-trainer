import {useEffect} from 'react';
import {CalendarClock} from 'lucide-react';
import './ContestReminder.css';

const startTime = new Intl.DateTimeFormat('zh-CN', {timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',hour12:false});
export default function ContestReminder({contest, now, onShown}) {
  useEffect(() => { onShown(); }, [contest.signature, contest.ownerKey, onShown]);
  const remaining = Math.ceil((Date.parse(contest.startAt) - now) / 60000);
  return <div className="contest-start-reminder"><CalendarClock size={28}/><div><strong>{contest.title}</strong><p><time dateTime={contest.startAt}>{startTime.format(new Date(contest.startAt))}</time><span>{remaining > 0 ? `${remaining} 分钟后开始` : '进行中'}</span></p></div></div>;
}
