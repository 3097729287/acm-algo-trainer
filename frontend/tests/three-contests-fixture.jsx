import React,{useState,useCallback} from 'react';
import {createRoot} from 'react-dom/client';
import SolutionReader from '../src/components/SolutionReader.jsx';
import Markdown from '../src/components/SolutionMarkdown.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import 'katex/dist/katex.min.css';

const data=await (await fetch('/__three_contests_data')).json();
window.fixtureData=data;
function Fixture(){
 const [index,setIndex]=useState(0),[prefs,setPrefs]=useState({}),[statement,setStatement]=useState(null);
 window.openContestEditorial=index=>{setStatement(null);setIndex(index)};
 window.openContestStatement=(index,chinese)=>setStatement(chinese?{...data.statements[index],...data.statements[index].translation}:data.statements[index]);
 const api=useCallback(async path=>({lectures:[]}),[]);
 return <main className="workspace-area" style={{height:'100vh',padding:0,display:'flex'}}>
  {statement?<section className="reader-content" style={{maxWidth:'100%',width:'100%',padding:24,overflow:'auto'}}><Markdown text={statement.markdown} images={statement.images||{}}/></section>:
   <aside className="solution-reader" style={{position:'relative',width:'100%',maxWidth:'100%',height:'100%',display:'flex',flexDirection:'column',border:0}}>
    <SolutionReader key={index} reader={data.readers[index]} api={api} prefs={prefs} setPrefs={setPrefs} onClose={()=>{}} fullscreen onFullscreen={()=>{}}/>
   </aside>}
 </main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
