import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import SolutionMarkdown from '../src/components/SolutionMarkdown.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import 'katex/dist/katex.min.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
function Review(){
 const [entry,setEntry]=useState(null);
 window.reviewEntry=value=>{window.copiedCode=null;setEntry(value);};
 return <main className="reading-body" style={{maxWidth:980,margin:'20px auto',padding:'0 18px',minHeight:'100vh'}}>{entry?<SolutionMarkdown key={entry.pid+entry.edition} text={entry.markdown} images={entry.images} onCopy={value=>{window.copiedCode=value;}}/>:<p>Ready</p>}</main>;
}
createRoot(document.getElementById('root')).render(<Review/>);
