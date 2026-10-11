import React from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import ReadingImage, { readingUrlTransform } from '../src/components/ReadingImage.jsx';
import { normalizeMarkdown } from '../src/lib/normalizeMarkdown.js';
import 'katex/dist/katex.min.css';

document.head.insertAdjacentHTML('beforeend','<style>body{font:17px/1.85 Microsoft YaHei,sans-serif;margin:0;background:#f1f5f9;color:#1f2937}main{max-width:940px;padding:24px 40px;margin:auto;background:white}pre{overflow:auto;background:#f6f8fa;padding:18px}table{border-collapse:collapse}td,th{border:1px solid #cbd5e1;padding:8px}h3{color:#245eb2}.katex-display{overflow:auto}</style>');
const root=createRoot(document.getElementById('root'));
window.renderDocument=async record=>{
 flushSync(()=>root.render(<main key={record.id}><ReactMarkdown remarkPlugins={[remarkGfm,remarkMath]} rehypePlugins={[rehypeKatex]}
   urlTransform={readingUrlTransform} components={{img:props=><ReadingImage {...props} images={record.images||{}}/>}}>{normalizeMarkdown(record.markdown)}</ReactMarkdown></main>));
 await Promise.race([
  Promise.all([...document.querySelectorAll('.reading-image-open img')].map(img=>{img.loading='eager';return img.decode();})),
  new Promise((resolve,reject)=>setTimeout(()=>reject(new Error('Image decoding exceeded 10 seconds')),10000)),
 ]);
 return {mathErrors:[...document.querySelectorAll('.katex-error')].map(n=>({text:n.textContent,error:n.title})),
  missing:[...document.querySelectorAll('.reading-image-missing')].map(n=>n.textContent),
  images:document.querySelectorAll('.reading-image-open img').length,
  math:document.querySelectorAll('.katex').length};
};
