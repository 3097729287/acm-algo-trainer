import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import Workbench from '../src/app/Workbench.jsx';
import {StudyPaneContext} from '../src/lib/StudyPane.jsx';
const style=document.createElement('style');
style.textContent=':root{--panel:white;--panel-2:#f5f5f5;--text:#222;--line:#ddd;--muted:#666;--accent:#198}*{box-sizing:border-box}body{margin:0}#root{height:100dvh}';
document.head.append(style);
const api=async(path,body)=>path==='draft'?{savedAt:new Date().toISOString()}:path.startsWith('problem?')?window.pdfFixtureData:Promise.reject(new Error('Unexpected fixture API: '+path));
function Harness(){
 const [visible,setVisible]=useState(true),[problemId,setProblemId]=useState('pdf-fixture');window.pdfFixtureSetVisible=setVisible;window.pdfFixtureSetProblem=setProblemId;
 return <StudyPaneContext.Provider value={{visible,focused:visible,state:{},scope:'',embedded:true,remember:()=>{}}}><div style={{height:'100%',display:visible?'block':'none'}}><Workbench problemId={problemId} contest={null} api={api}/></div></StudyPaneContext.Provider>;
}
createRoot(document.getElementById('root')).render(<Harness/>);
