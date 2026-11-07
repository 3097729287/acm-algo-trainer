import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkSourceMath from '../src/lib/remarkSourceMath.js';
import {normalizeMarkdown} from '../src/lib/normalizeMarkdown.js';

for(const source of ['$0&lt;5$','$$\n0&lt;5\n$$',String.raw`$u^'_1$`,String.raw`$\[l,r\]$`,String.raw`$n\$`,String.raw`$\texttt{#}$`,String.raw`$\text{intersection_length}$`,String.raw`$#1$`,String.raw`$$x\tag{1}$$`,String.raw`$$$$$$\begin{array}{l}a_i \leftarrow a_j \times a_k\end{array}$$$$$$`,'- Definition:\n\n  $$\n  x+y\n  $$\n\n  Where $x$ is given.']){
 const normalized=normalizeMarkdown(source);
 const html=renderToStaticMarkup(React.createElement(ReactMarkdown,{remarkPlugins:[remarkMath,remarkSourceMath],rehypePlugins:[[rehypeKatex,{strict:false}]],children:normalized}));
 assert(!html.includes('katex-error'),source+' must render its actual normalized TeX');
 assert(html.includes('katex'),source+' must retain its mathematical display');
 assert.equal(normalizeMarkdown(normalized),normalized);
}
assert.equal(normalizeMarkdown('$$$a$$$$$$b$$$'),'$a$ $b$');
assert.equal(normalizeMarkdown(String.raw`optional \[ \__object_\] and \[1, $10^6$\]`),String.raw`optional \[ \__object_\] and \[1, $10^6$\]`);
for(const source of [String.raw`$\begin{equation*}x+y\end{equation*}$`,String.raw`$(&).$`]){
 const html=renderToStaticMarkup(React.createElement(ReactMarkdown,{remarkPlugins:[remarkMath,remarkSourceMath],rehypePlugins:[[rehypeKatex,{strict:false}]],children:normalizeMarkdown(source)}));
 assert(!html.includes('katex-error'));assert.equal(normalizeMarkdown(normalizeMarkdown(source)),normalizeMarkdown(source));
}
const node={type:'inlineMath',value:String.raw`a\\[2pt]b\\`};remarkSourceMath()({children:[node]});assert.equal(node.value,String.raw`a\\[2pt]b\\`);
assert.equal(normalizeMarkdown('```text\n$$$$$$\\begin{array}$$$$$$\n```'),'```text\n$$$$$$\\begin{array}$$$$$$\n```');
console.log('PASS source math HTML entities, superscript primes, duplicate CF display wrappers, adjacent formulas and literal code.');
