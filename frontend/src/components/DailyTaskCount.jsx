import {Check} from 'lucide-react';
export default function DailyTaskCount({value}) {
 const completed=Math.max(0,Number(value?.displayCompletedCount)||0);
 const complete=value?.displayComplete===true||completed>=10;
 const target=Math.min(10,Math.max(3,completed+1));
 return <small aria-label={complete?'今日已完成十项任务':`今日任务 ${completed}/${target}`}>{complete?<Check size={16} aria-hidden="true"/>:`${completed}/${target}`}</small>;
}
