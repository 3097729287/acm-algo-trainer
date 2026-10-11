import React from 'react';
import { createRoot } from 'react-dom/client';
import ReactMarkdown from 'react-markdown';
import ReadingImage, { readingUrlTransform } from '@/components/ReadingImage.jsx';
import { LectureDisclosure, LecturesPanel } from '@/pages/LecturesPanel.jsx';
import { solutionBlocks } from '@/lib/practiceMetadata.js';
import formats from './image-formats.json';
import '@/styles/workspace.css';
import 'katex/dist/katex.min.css';

const svg='<svg xmlns="http://www.w3.org/2000/svg" width="880" height="230" viewBox="0 0 880 230"><rect width="880" height="230" fill="white"/><path d="M140 100L440 100L740 100" fill="none" stroke="#2867bd" stroke-width="5"/><g fill="#eaf2ff" stroke="#2867bd" stroke-width="2"><circle cx="140" cy="100" r="36"/><circle cx="440" cy="100" r="36"/><circle cx="740" cy="100" r="36"/></g><g font-family="Microsoft YaHei" font-size="25" text-anchor="middle"><text x="140" y="108">1</text><text x="440" y="108">2</text><text x="740" y="108">3</text><text x="440" y="186">以 1 为根：先删 3，再删 2</text></g></svg>';
const data='data:image/svg+xml;base64,'+btoa(String.fromCharCode(...new TextEncoder().encode(svg)));
const images={'配图/树 (1).svg':data,...formats};
const md='![树结构](<配图/树 (1).svg> "树的删除顺序")\n\n'+Object.keys(formats).map(key=>`![${key}](${key})`).join('\n\n');
const lecture={id:'illustration',title:'从零讲：树形 DP',concept:'树形 DP',category:'动态规划',sourceProblemIds:['test::A'],markdown:'## 先看一个例子\n\n'+md,images};
window.inlineLectureRequests=0;
const split='### 从零讲：引用图\n\n![引用式配图][tree]\n\n### 思路\n\n原题思路只出现一次。\n\n[tree]: <配图/树 (1).svg> "定义在另一段"';
function App(){return <main style={{maxWidth:940,margin:'24px auto',padding:16}}>
  <h1>题解配图</h1><div className="markdown"><ReactMarkdown urlTransform={readingUrlTransform} components={{img:({node,...props})=><ReadingImage {...props} images={images}/>}}>{md+'\n\n![直接嵌入]('+data+')\n\n![缺图](missing.svg)\n\n[不安全链接](javascript:alert(1))'}</ReactMarkdown></div>
  <LectureDisclosure lecture={{id:'inline-lesson',title:'从零讲：树'}} inlineMarkdown={'### 从零讲：树\n\n'+md} images={images} api={()=>{window.inlineLectureRequests++;return Promise.resolve({...lecture,markdown:'不应重复的完整上下文'});}}/>
  <section aria-label="分段引用式图片">{solutionBlocks(split).map((block,i)=>block.type==='lecture'?
    <LectureDisclosure key={i} lecture={{title:block.heading}} inlineMarkdown={block.markdown} images={images} api={()=>Promise.reject(new Error('Inline sections must not fetch'))}/>:
    <ReactMarkdown key={i} urlTransform={readingUrlTransform} components={{img:({node,...props})=><ReadingImage {...props} images={images}/>}}>{block.markdown}</ReactMarkdown>)}</section>
  <LecturesPanel lectures={{lectures:[lecture]}} initialLecture={lecture.id} api={()=>Promise.resolve(lecture)}/>
</main>}
createRoot(document.getElementById('root')).render(<App/>);
