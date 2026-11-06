import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import InitialCodeSettings from '../src/pages/InitialCodeSettings.jsx';
import MockProblemPicker from '../src/app/MockProblemPicker.jsx';
import ReaderFrame from '../src/components/ReaderFrame.jsx';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
document.documentElement.dataset.theme='dark';window.__tbAccountUserId='isolated-interface';
let snapshot={selection:{cpp17:'default',python3:'default'},revisions:{cpp17:'',python3:''},templates:['cpp17','python3'].map(language=>({id:'default',title:'默认',language,code:language==='cpp17'?'int main() {}':'print(42)',builtin:true,revision:''}))};
const calls=[];async function api(path,body){calls.push({path,body});if(path==='initial-code')return structuredClone(snapshot);if(path==='initial-code/save'){const template={...snapshot.templates.find(item=>item.language===body.language),...body,revision:crypto.randomUUID(),customized:true};snapshot={...snapshot,templates:snapshot.templates.map(item=>item.language===body.language?template:item)};return {...structuredClone(snapshot),template};}if(path==='initial-code/select')return structuredClone(snapshot);throw Error('Unexpected isolated request '+path);}
const slots=['AC','WA','TLE','MLE','OLE','RE','CE','RUNNING','QUEUED',null].map((verdict,index)=>({id:String(index),title:verdict||'Untouched',letter:String(index),verdict,accepted:verdict==='AC'}));
function Fixture(){const[revision,setRevision]=useState(0),[reading,setReading]=useState(false);window.interfaceFixture={openReader:()=>setReading(true),calls,state:()=>snapshot,reopen:()=>setRevision(value=>value+1)};return <main className="settings-page" style={{height:'100dvh',padding:16}}><MockProblemPicker contest={{name:'Status fixture',slots,accepted:1,total:slots.length}} currentId="0" onSelect={()=>{}} onHistory={()=>{}}/><InitialCodeSettings key={revision} api={api}/>{reading&&<ReaderFrame fullscreen identity="fixture-full-reader"><header className="solution-reader-header" style={{height:44,minHeight:44}}>返回</header><div className="reader-content" aria-label="独立全屏正文">{Array.from({length:100},(_,i)=><p key={i}>全屏题解正文</p>)}</div></ReaderFrame>}</main>;}
createRoot(document.getElementById('root')).render(<Fixture/>);
