import {build} from 'vite';
import react from '@vitejs/plugin-react';
import {writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const result=await build({configFile:false,root,base:'./',logLevel:'warn',resolve:{alias:{'@':path.join(root,'src')}},plugins:[react()],define:{__TB_VERSION__:JSON.stringify('1.6.1')},build:{write:false,assetsInlineLimit:Infinity,rolldownOptions:{input:path.join(root,'design-reviews/task-workspace.html'),output:{codeSplitting:false}}}});
const output=(Array.isArray(result)?result[0]:result).output;let html=output.find(item=>item.fileName.endsWith('.html')).source.toString();
for(const item of output){if(item.type==='chunk')html=html.replace(/<script\b[^>]*src="[^"]+"[^>]*><\/script>/,()=>'<script type="module">'+item.code.replace(/<\/script/gi,'<\\/script')+'</script>');else if(item.fileName.endsWith('.css'))html=html.replace(/<link\b[^>]*rel="stylesheet"[^>]*>/,()=>'<style>'+item.source.toString()+'</style>');}
html=html.replace(/<link\b[^>]*rel="modulepreload"[^>]*>/g,'');
const out=path.resolve(process.argv[2]||path.join(root,'../.backups/atmosphere-20261105/ToBe-任务工作台-修订.html'));await mkdir(path.dirname(out),{recursive:true});await writeFile(out,html);console.log(JSON.stringify({ok:true,output:out,bytes:Buffer.byteLength(html)}));
