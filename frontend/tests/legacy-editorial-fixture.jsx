import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import SolutionReader from '../src/components/SolutionReader.jsx';
import '../src/styles/workspace.css';

const params=new URLSearchParams(location.search);
document.documentElement.dataset.theme=params.get('theme')||'dark';
const cases=await fetch('./legacy-editorial-data.json').then(response=>response.json());
const sample=cases[Number(params.get('sample')||0)];
window.legacyEditorial={sample,formatCalls:0};
const api=async path=>{
 if(path==='lectures')return {lectures:[]};
 if(path==='code/format'){window.legacyEditorial.formatCalls++;throw Error('Formatter deliberately unavailable: stored content must already be formatted');}
 throw Error('Unexpected test API: '+path);
};
function Fixture(){
 const [prefs,setPrefs]=useState({});
 const reader=params.has('legacy')?{...sample.reader,markdown:sample.reader.markdown.replaceAll('```cpp','```cxx')}:sample.reader;
 return <main style={{height:'100dvh',width:'100%',display:'flex',flexDirection:'column',background:'var(--panel)',color:'var(--text)'}}><SolutionReader reader={reader} api={api} problemId={sample.id} methodId="original" prefs={prefs} setPrefs={setPrefs} onClose={()=>{}} onFullscreen={()=>{}}/></main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
