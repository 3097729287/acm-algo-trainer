// Run with an explicit, isolated JSON export; this never scans a personal DB.
import fs from 'node:fs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkTableBreaks from '../src/lib/remarkTableBreaks.js';
import remarkSourceMath from '../src/lib/remarkSourceMath.js';
import {normalizeMarkdown} from '../src/lib/normalizeMarkdown.js';
import {normalizeStatement} from '../src/lib/normalizeStatement.js';
const input=process.argv[2], output=process.argv[3];
if(!input||!output)throw new Error('Supply isolated corpus JSON and result path');
const rows=JSON.parse(fs.readFileSync(input,'utf8')),issues=[];
let rendered=0,nativePdf=0;
for(const row of rows){
  if(row.nativePdf){nativePdf++;continue;}
  try {
    const html=renderToStaticMarkup(React.createElement(ReactMarkdown,{
      remarkPlugins:[remarkGfm,remarkMath,remarkTableBreaks,remarkSourceMath],
      rehypePlugins:[[rehypeKatex,{throwOnError:false,strict:false,trust:false}]],
      children:normalizeMarkdown(normalizeStatement(row.markdown,row.samples,row.title)),
    }));
    const errors=[...html.matchAll(/class="katex-error"[^>]*title="([^"]*)"/g)].map(m=>m[1]);
    if(errors.length)issues.push({id:row.id,issues:[...new Set(errors)]});
    if(!html.length)throw new Error('Empty rendered statement');
    rendered++;
  } catch(error){issues.push({id:row.id,error:String(error)});}
}
const result={total:rows.length,rendered,nativePdf,issues};
fs.writeFileSync(output,JSON.stringify(result,null,2));
console.log(JSON.stringify({total:rows.length,rendered,nativePdf,problemsWithRenderIssues:issues.length}));
process.exitCode=issues.some(item=>item.error)?1:0;
