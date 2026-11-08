import React from 'react';
import {createRoot} from 'react-dom/client';
import SolutionMarkdown from '../src/components/SolutionMarkdown.jsx';
import SolutionReader from '../src/components/SolutionReader.jsx';
import {readEditorialMotion} from '../src/lib/editorialMotion.js';
import '../src/styles/workspace.css';
import '../src/components/SolutionReader.css';
import 'katex/dist/katex.min.css';

const params=new URLSearchParams(location.search),cases=await fetch(params.has('article')?'./editorial-motion-articles.json':'./editorial-motion-data.json').then(r=>r.json()),sample=cases[Number(params.get('case')||0)];
document.documentElement.dataset.theme=params.get('theme')||'dark';
document.documentElement.dataset.motion=params.has('static')?'off':'on';
window.motionFixture={cases,sample,parse:readEditorialMotion};
const style=document.createElement('style');style.textContent='html,body{margin:0;background:var(--surface,#171b23);color:var(--text,#e1e7ef)}main{max-width:900px;margin:auto;padding:16px;box-sizing:border-box}.reader-content{max-height:none;overflow:visible}.article-fixture{height:100dvh;display:flex;flex-direction:column}.article-fixture>.reader-content{min-height:0;flex:1;overflow:auto}';document.head.append(style);
const api=async path=>{if(path==='lectures')return {lectures:[]};throw Error('Offline reference formatting in fixture');};
createRoot(document.getElementById('root')).render(sample.reader?<main className="article-fixture"><SolutionReader reader={sample.reader} problemId={sample.problemId} api={api} methodId="original" prefs={{}} setPrefs={()=>{}} onClose={()=>{}} onFullscreen={()=>{}}/></main>:<main className="reader-content">
 <p>{sample.title}</p>
 {params.has('below')&&<div style={{height:1100}}/>}
 {params.has('raw')?<img id="standalone" style={{maxWidth:'100%'}} src={sample.source}/>:<SolutionMarkdown text={sample.markdown||`![${sample.title}](motion.svg)`} images={sample.images||{'motion.svg':sample.source}}/>}
 <div style={{height:1100}}/>
</main>);
