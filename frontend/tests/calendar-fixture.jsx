import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import ContestCalendar from '../src/pages/ContestCalendar.jsx';
import useContestCalendar from '../src/lib/useContestCalendar.js';
import ContestReminder from '../src/components/ContestReminder.jsx';

const fixture=window.calendarFixture={events:[0,0,1,2,4].map((day,index)=>({id:String(index),title:`Contest ${index}`,platform:'atcoder',startAt:`2026-10-${26+day}T19:00:00+08:00`,endAt:`2026-10-${26+day}T23:59:59+08:00`,url:'https://atcoder.jp/contests/fixture'}))};
const api=async path=>{
 fixture.calls||=[];fixture.calls.push(path);
 const value={contests:structuredClone(fixture.events),providers:[]};
 if(fixture.hold){fixture.hold=false;await new Promise(resolve=>{fixture.release=resolve;});}
 return value;
};
const style=document.createElement('style');style.textContent=':root{--panel-2:#f0f2f5;--accent:#168473;--accent-soft:#d8f0eb;--line:#ddd;--muted:#777;--text:#222}body{font-family:sans-serif;padding:20px}.contest-calendar{max-width:800px}.notification-dot{display:inline-block;width:7px;height:7px;background:teal;border-radius:50%}';document.head.append(style);
function Fixture(){
  const [now,setNow]=useState(Date.parse('2026-10-26T10:00:00+08:00')),[open,setOpen]=useState(false),[,render]=useState(0);
  const calendar=useContestCalendar(api,true,open,now);
  fixture.setNow=setNow;fixture.refresh=calendar.refresh;fixture.account=id=>{window.__tbAccountUserId=id;render(value=>value+1);};
  return <><button onClick={()=>setOpen(!open)}>比赛日历{calendar.hasUnreadToday&&<span className="notification-dot"/>}</button>{open&&<ContestCalendar calendar={calendar}/>} {calendar.reminder&&<section role="dialog" aria-label="比赛即将开始"><ContestReminder contest={calendar.reminder} now={calendar.now} onShown={calendar.markReminderShown}/><button onClick={calendar.dismissReminder}>关闭提醒</button></section>}</>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
