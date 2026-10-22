// Standalone reading copy: math, fonts and figures are embedded, no API/server.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {solutionBlocks} from '../src/lib/practiceMetadata.js';
import {normalizeMarkdown} from '../src/lib/normalizeMarkdown.js';

const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const repo=path.dirname(frontend),output=path.resolve(process.argv[2]||path.join(repo,'.backups/editorial-teaching-20261022/reading'));
fs.mkdirSync(output,{recursive:true});
const katex=path.join(frontend,'node_modules/katex/dist');
let css=fs.readFileSync(path.join(katex,'katex.min.css'),'utf8');
css=css.replace(/url\(([^)]+)\)/g,(match,src)=>{
  const file=path.join(katex,src.replace(/["']/g,''));
  return fs.existsSync(file)?'url(data:font/'+path.extname(file).slice(1)+';base64,'+fs.readFileSync(file).toString('base64')+')':match;
});
css+='\n'+fs.readFileSync(path.join(repo,'docs/foundations/reading.css'),'utf8');
const lectures=JSON.parse(fs.readFileSync(path.join(repo,'data/library/lectures.json'),'utf8')).map(row=>row.content);
const identity='remote:nowcoder:141877::C';
const files=[];
for (const [variant,label,filename] of [['solutions','默认题解','小月的长廊-默认题解.html'],['detailed_solutions','详细题解','小月的长廊-详细题解.html']]) {
  const solution=JSON.parse(fs.readFileSync(path.join(repo,'data/library',variant+'.json'),'utf8')).find(row=>row.problem_id===identity);
  const body=solutionBlocks(solution.markdown,lectures).map(block=>{
    const content=React.createElement(ReactMarkdown,{remarkPlugins:[remarkGfm,remarkMath],rehypePlugins:[[rehypeKatex,{strict:'ignore'}]],components:{img:({node,src,alt})=>React.createElement('img',{src:solution.images[src]||src,alt,loading:'lazy'})}},normalizeMarkdown(block.markdown));
    return renderToStaticMarkup(block.type==='lecture'?React.createElement('details',null,React.createElement('summary',null,'从零讲：'+block.heading),React.createElement('div',{className:'lesson'},content)):React.createElement('section',null,content));
  }).join('\n');
  const nav=variant==='solutions'?'<a href="小月的长廊-详细题解.html">阅读详细题解</a>':'<a href="小月的长廊-默认题解.html">阅读默认题解</a>';
  const html='<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>小月的长廊 · '+label+'</title><style>'+css+'</style></head><body><main><nav>'+nav+'<span>基础课可展开阅读 · 图片可直接查看</span></nav>'+body+'</main></body></html>';
  const file=path.join(output,filename);fs.writeFileSync(file,html);files.push(file);
}
console.log(JSON.stringify({standalone:true,files},null,2));
