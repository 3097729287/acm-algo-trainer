import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import SolutionReader from '../src/components/SolutionReader.jsx';
import SolutionMarkdown from '../src/components/SolutionMarkdown.jsx';
import CatalogExplorer from '../src/components/CatalogExplorer.jsx';
import 'katex/dist/katex.min.css';

const fixture=window.gymFixture;
const style=document.createElement('style');
style.textContent=`:root{font-family:"Microsoft YaHei",sans-serif;--panel:#fff;--text:#243449;--muted:#64748b;--line:#dce3ed;--accent:#12805c;--surface:#f6f8fa;--border:#dce3ed}*{box-sizing:border-box}body{margin:0;color:var(--text);background:#f1f5f9}body.dark{--panel:#191d25;--text:#e8edf3;--muted:#acb8c6;--line:#354254;--surface:#232b36;--border:#354254;background:#11151d}main{width:min(100%,1080px);margin:auto;padding:20px;background:var(--panel)}.reader-content{max-height:none;overflow:visible}.markdown{font-size:17px;line-height:1.8;overflow-wrap:anywhere}.markdown p{margin:12px 0}pre{white-space:pre;overflow:auto;max-width:100%;padding:14px;background:#8795aa16;border-radius:8px;font-size:14px}table{display:block;max-width:100%;overflow:auto;border-collapse:collapse}td,th{padding:7px 10px;border:1px solid var(--line)}.katex-display{overflow:auto;max-width:100%}button{cursor:pointer}a{color:var(--accent)}.code-block{position:relative}.copy-code{display:none}.lesson-reader-link{margin:12px 0}.reading-image-open{max-width:100%}.markdown img{max-width:100%;height:auto}`;
document.head.append(style);document.body.classList.toggle('dark',Boolean(fixture.dark));
const api=async name=>name==='lectures'?{lectures:fixture.lectures||[]}:{};
function App(){
 const [prefs,setPrefs]=useState({}),[scope,setScope]=useState({path:['校队训练']});
 if(fixture.mode==='statement')return <main><SolutionMarkdown text={fixture.statement.markdown} images={fixture.statement.images}/></main>;
 if(fixture.mode==='catalog')return <main><CatalogExplorer rows={fixture.rows} scope={scope} onChange={setScope}/></main>;
 return <main><SolutionReader reader={fixture.reader} api={api} prefs={prefs} setPrefs={setPrefs} onClose={()=>{}} onFullscreen={()=>{}}/></main>;
}
createRoot(document.getElementById('root')).render(<App/>);
