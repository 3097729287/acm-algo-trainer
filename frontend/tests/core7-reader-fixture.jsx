import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import SolutionReader from '../src/components/SolutionReader.jsx';
import 'katex/dist/katex.min.css';
const fixture=window.core7Reader;
const style=document.createElement('style');
style.textContent=`:root{font-family:"Microsoft YaHei",sans-serif;--panel:#fff;--text:#243449;--muted:#64748b;--line:#dce3ed;--accent:#12805c}*{box-sizing:border-box}body{margin:0;background:#edf0f4;color:var(--text)}body.dark{--panel:#191d25;--text:#e8edf3;--muted:#acb8c6;--line:#354254;background:#11151d}main{max-width:1080px;margin:auto;background:var(--panel);height:100vh;display:flex;flex-direction:column;padding:12px}.reader-content{min-height:0;flex:1;overflow:auto;padding:12px}.markdown{font-size:17px;line-height:1.85;overflow-wrap:anywhere}pre{overflow:auto;white-space:pre;padding:12px;font-size:14px}table{display:block;overflow:auto;max-width:100%}.katex-display{overflow:auto}button,a{color:inherit}button{cursor:pointer}nav{display:flex;gap:8px;flex-wrap:wrap}.lesson-reader-link{display:flex;gap:8px;padding:8px}.icon-button{border:0;background:transparent;padding:8px}footer{padding:8px}`;
document.head.append(style);document.body.classList.toggle('dark',fixture.dark);
const headerStyle=document.createElement('style');
headerStyle.textContent='.solution-reader-header{display:flex;align-items:center}.reader-content{min-width:0}.code-block{max-width:100%}';
document.head.append(headerStyle);
function Fixture(){
  const [method,setMethod]=useState(fixture.reader.primaryMethod),[prefs,setPrefs]=useState({});
  const api=async()=>({lectures:fixture.lectures});
  return <main><nav>{fixture.reader.methods.map(m=><button key={m.id} onClick={()=>setMethod(m.id)} data-method={m.id}>{m.title}</button>)}</nav>
    <SolutionReader reader={fixture.reader} api={api} methodId={method} onClose={()=>{}} onFullscreen={()=>{}} prefs={prefs} setPrefs={setPrefs}/>
  </main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
