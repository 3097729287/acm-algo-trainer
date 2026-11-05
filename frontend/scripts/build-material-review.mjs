import {build} from 'vite';
import react from '@vitejs/plugin-react';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {STICKERS} from '../../server/leaderboard/src/gameplay.mjs';
const front=fileURLToPath(new URL('../',import.meta.url));
const input=await readFile(process.argv[2]||fileURLToPath(new URL('../../docs/reviews/background-approval-20261105.json',import.meta.url)));
const approval=JSON.parse(input.toString('utf8').replace(/^\uFEFF/,'')),inputSha256=createHash('sha256').update(input).digest('hex');
const result=await build({configFile:false,root:front,base:'./',logLevel:'warn',resolve:{alias:{'@':path.join(front,'src')}},plugins:[react(),{name:'material-review-data',resolveId(id){if(id==='virtual:material-review')return '\0'+id;},load(id){if(id==='\0virtual:material-review')return `export const catalogue=${JSON.stringify(STICKERS)};export const approval=${JSON.stringify(approval)};export const inputSha256=${JSON.stringify(inputSha256)};`;}}],build:{write:false,assetsInlineLimit:Infinity,rolldownOptions:{input:path.join(front,'reviews/atmosphere/index.html'),output:{codeSplitting:false}}}});
const output=Array.isArray(result)?result[0].output:result.output;
let html=output.find(item=>item.fileName.endsWith('.html')).source.toString();
for(const item of output){if(item.type==='chunk')html=html.replace(/<script\b[^>]*src="[^"]+"[^>]*><\/script>/,()=>'<script type="module">'+item.code.replace(/<\/script/gi,'<\\/script')+'</script>');else if(item.fileName.endsWith('.css'))html=html.replace(/<link\b[^>]*rel="stylesheet"[^>]*>/,()=>'<style>'+item.source.toString()+'</style>');}
html=html.replace(/<link\b[^>]*rel="modulepreload"[^>]*>/g,'');
const out=path.resolve(process.argv[3]||path.join(front,'../.backups/background-review-20261105/ToBe-背景重制.html'));
await mkdir(path.dirname(out),{recursive:true});await writeFile(out,html);
console.log(JSON.stringify({ok:true,backgrounds:STICKERS.filter(item=>item.kind==='background').length,stickers:STICKERS.filter(item=>item.kind!=='background').length,bytes:Buffer.byteLength(html),output:out,inputSha256}));
