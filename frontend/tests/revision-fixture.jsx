import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import MockSetup from '../src/app/MockSetup.jsx';
import AppRecovery from '../src/components/AppRecovery.jsx';
import {ProfileSettings} from '../src/pages/CommunityPanel.jsx';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';

const fixture=window.revisionFixture={calls:[],started:[],fail:false,profileReady:false};
const event={name:'CCPC 2025 郑州区域赛',displayName:'CCPC 2025 郑州区域赛',platform:'牛客',series:'XCPC',difficulty:1200,count:2,duration:300,rules:'xcpc'};
const categories=[{name:'基础技巧',tags:Array.from({length:30},(_,i)=>'parent'+i),children:[{name:'前缀和',tags:['前缀和']},{name:'二分查找',tags:['二分','二分查找']}]}];
async function api(path,body){
 fixture.calls.push({path,body});
 if(path==='contests/events')return {events:[event]};
 if(path==='contests/preview'){
  if(body.mode==='topic'&&(!body.tags.length||body.tags.length>256))throw Error('Invalid topics');
  if(body.mode==='replay'&&body.contest!==event.name)throw Error('Invalid event');
  const count=body.mode==='replay'?2:body.count;
  return {plan:{previewId:'preview-'+body.mode,name:body.mode,slots:Array.from({length:count},(_,i)=>({id:'fixture::'+i,letter:String.fromCharCode(65+i),judgeScope:'local'}))}};
 }
 if(path==='contests/start'){fixture.started.push(body);return {contest:{id:'created'}};}
 if(path==='profile'){await new Promise(resolve=>fixture.resolveProfile=resolve);fixture.profileReady=true;return {profile:{userId:'self',nickname:'快速账号'},leaderboard:{configured:true}};}
 throw Error('Unexpected '+path);
}
function Content(){if(fixture.fail)throw Error('Fixture render failure');return <div data-restored="true">已恢复</div>;}
function Fixture(){const[mode,setMode]=useState('mock'),[generation,setGeneration]=useState(0);return <><div className="fixture-switch"><button onClick={()=>setMode('mock')}>模拟赛测试</button><button onClick={()=>setMode('profile')}>账号测试</button><button onClick={()=>setMode('recovery')}>恢复测试</button><button onClick={()=>{fixture.fail=true;setGeneration(x=>x+1);}}>触发渲染异常</button></div><div id="tb-page-search"/><div className="workspace-area" style={{height:'calc(100dvh - 90px)'}}>{mode==='mock'?<MockSetup key={generation} api={api} categories={categories} onStarted={()=>setGeneration(value=>value+1)}/>:mode==='profile'?<ProfileSettings api={api} initialAccount={{userId:'self',nickname:'快速账号',loginId:'fixture'}}/>:<AppRecovery><Content key={generation}/></AppRecovery>}</div></>;}
document.documentElement.dataset.theme='dark';document.documentElement.style.setProperty('--panel-opacity','100%');
createRoot(document.getElementById('root')).render(<Fixture/>);
