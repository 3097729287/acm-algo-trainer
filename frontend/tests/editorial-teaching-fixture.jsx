import React from 'react';
import {createRoot} from 'react-dom/client';
import SolutionMarkdown from '../src/components/SolutionMarkdown.jsx';
import {LectureDisclosure} from '../src/pages/LecturesPanel.jsx';
import {solutionBlocks} from '../src/lib/practiceMetadata.js';
import 'katex/dist/katex.min.css';

const style=document.createElement('style');
style.textContent=`:root{font-family:"Microsoft YaHei",sans-serif;--panel:#fff;--text:#243449;--muted:#64748b;--line:#dce3ed;--accent:#12805c}*{box-sizing:border-box}body{margin:0;color:var(--text);background:#f1f5f9}body.dark{--panel:#191d25;--text:#e8edf3;--muted:#acb8c6;--line:#354254;background:#11151d}main{width:min(100%,1080px);margin:auto;padding:24px;background:var(--panel)}main.narrow{max-width:520px}.markdown,.lecture-markdown{font-size:17px;line-height:1.85;overflow-wrap:anywhere}.markdown p,.lecture-markdown p{margin:12px 0}pre{white-space:pre;overflow:auto;padding:14px;background:#8795aa16;border-radius:8px;font-size:14px}table{display:block;max-width:100%;overflow:auto;border-collapse:collapse}td,th{padding:7px 10px;border:1px solid var(--line)}.katex-display{overflow:auto;max-width:100%}h3{margin-top:30px}details{margin:12px 0;padding:12px;border:1px solid var(--line);border-radius:8px}summary{cursor:pointer;display:flex;gap:8px;align-items:center}summary small{margin-left:auto;white-space:nowrap;font-size:12px;color:var(--muted)}.code-block{position:relative}.copy-code{display:none}a{color:var(--accent)}.lecture-source{display:none}`;
document.head.append(style);
const fixture=window.editorialTeaching;
document.body.classList.toggle('dark',Boolean(fixture.dark));
const blocks=solutionBlocks(fixture.solution.markdown,fixture.lectures);
createRoot(document.getElementById('root')).render(<main className={fixture.narrow?'narrow':''}>
  {blocks.map((block,index)=>block.type==='lecture'
    ? <LectureDisclosure key={index} lecture={block.lecture||{title:block.heading}} inlineMarkdown={block.markdown} images={fixture.solution.images}/>
    : <SolutionMarkdown key={index} text={block.markdown} images={fixture.solution.images}/>) }
</main>);
