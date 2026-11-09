import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import Workbench from '../src/app/Workbench.jsx';
import 'katex/dist/katex.min.css';

window.__tbAccountUserId='review-editor-isolated-owner';
const style=document.createElement('style');
style.textContent=':root{font-family:Segoe UI,sans-serif;--bg:#15181e;--panel:#191d24;--panel-2:#20252d;--text:#ecedf2;--muted:#a2a9b8;--line:#404753;--accent:#67cbb1;--accent-soft:#67cbb114;--success:#67cbb1;--danger:#ef8b8b;--warning:#e4c079}*{box-sizing:border-box}body{margin:0;color:var(--text);background:var(--bg)}#root{height:100vh}';
document.head.append(style);
async function api(path,body){
 const response=await fetch('/api/'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},...(body?{body:JSON.stringify(body)}:{})});
 const value=await response.json();if(!response.ok)throw Error(value.error||'Isolated request failed');return value;
}
function Fixture(){
 const [reviewTask,setReviewTask]=useState(null);
 window.reviewEditorFixture={api,open:task=>setReviewTask(task),reviewTask};
 return <Workbench problemId="fixture::A" reviewTask={reviewTask} api={api} onProgress={()=>{}}/>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
