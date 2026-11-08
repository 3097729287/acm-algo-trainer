import {createRoot} from 'react-dom/client';
import useTeamTraining from '../src/lib/useTeamTraining.js';
import TeamTraining,{TeamTrainingRoom} from '../src/components/TeamTraining.jsx';
import '../src/app/Workbench.css';
import 'katex/dist/katex.min.css';

const config=window.teamFixture;
window.__tbAccountUserId=config.owner;
const api=async(path,body)=>{
 const response=await fetch(config.endpoint+'/api/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-TB-Token':config.token},...(body===undefined?{}:{body:JSON.stringify(body)})});
 const value=await response.json();
 if(!response.ok)throw Object.assign(new Error(value.error||'fixture request failed'),{status:response.status,code:value.code});
 return value;
};
const style=document.createElement('style');
style.textContent=':root{font-family:Segoe UI,Microsoft YaHei UI,sans-serif;--bg:#12151b;--panel-base:#181d26;--panel:#181d26;--panel-2:#202634;--text:#e1e5ed;--muted:#929cad;--accent:#74cbb6;--accent-soft:#74cbb615;--line:#30394a;--soft-line:#252d3a;--danger:#ec8293;--success:#74cbb6}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-size:16px}button,input,select{font:inherit;color:inherit}button{cursor:pointer}button:disabled{opacity:.4;cursor:default}button,input,select{background:var(--panel-2);border:0;border-radius:5px;padding:8px}input,select{height:38px}.icon-button{display:inline-flex;align-items:center;justify-content:center;gap:6px;background:none;padding:8px}.connection-error{color:var(--danger);padding:8px}.modal-overlay{position:fixed;inset:0;background:#0008;display:grid;place-items:center}.modal{padding:24px;background:var(--panel)}.modal-actions{display:flex;gap:16px}.team-training{max-width:1200px;margin:auto}';document.head.append(style);
function App(){
 const controller=useTeamTraining(api,config.owner);window.team=controller;window.fixtureApi=api;
 return <><TeamTraining controller={controller} owner={config.owner}/><TeamTrainingRoom controller={controller} owner={config.owner}/></>;
}
createRoot(document.getElementById('root')).render(<App/>);
