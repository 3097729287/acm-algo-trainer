import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import 'katex/dist/katex.min.css';
import SolutionMarkdown from '../src/components/SolutionMarkdown.jsx';

function Fixture(){
 const [rows,setRows]=useState([]),[selected,setSelected]=useState(0);
 useEffect(()=>{fetch('/__nowcoder_editorials').then(r=>r.json()).then(setRows);},[]);
 if(!rows.length)return <p>Loading</p>;
 const row=rows[selected];
 return <><nav>{rows.map((r,i)=><button key={r.id} data-id={r.id} onClick={()=>setSelected(i)}>{r.id}</button>)}</nav>
  <main data-problem-id={row.id}><SolutionMarkdown key={row.id} text={row.markdown} images={row.images}
   problemId={row.id} onCopy={code=>{window.__nowcoderCopiedCode=code;}}/></main></>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
