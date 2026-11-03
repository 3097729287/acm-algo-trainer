import { readFileSync, realpathSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const root=fileURLToPath(new URL('.',import.meta.url)),modules=fileURLToPath(new URL('./node_modules',import.meta.url));
// Bundle PDF fonts/maps/decoders for offline reading. The dev route serves the
// same exact public-file allowlist, without exposing surrounding dependencies.
const pdfDirectory=realpathSync(modules+'/pdfjs-dist'),pdfVersion=JSON.parse(readFileSync(pdfDirectory+'/package.json','utf8')).version;
const pdfFiles=new Map();
for(const group of ['cmaps','standard_fonts','wasm','iccs'])for(const name of readdirSync(pdfDirectory+'/'+group)){
 if(/^[A-Za-z0-9_.-]+$/.test(name))pdfFiles.set(`pdfjs/${pdfVersion}/${group}/${name}`,pdfDirectory+'/'+group+'/'+name);
}
pdfFiles.set(`pdfjs/${pdfVersion}/LICENSE`,pdfDirectory+'/LICENSE');
const pdfAssets={name:'offline-pdf-assets',configureServer(server){server.middlewares.use((request,response,next)=>{
 let key;try{key=decodeURIComponent(new URL(request.url,'http://localhost').pathname).slice(1);}catch{return next();}
 const file=pdfFiles.get(key);if(!file)return next();
 response.setHeader('Content-Type',key.endsWith('.wasm')?'application/wasm':key.endsWith('.js')||key.endsWith('.mjs')?'text/javascript':'application/octet-stream');
 response.end(request.method==='HEAD'?undefined:readFileSync(file));
});},generateBundle(){for(const [fileName,file]of pdfFiles)this.emitFile({type:'asset',fileName,source:readFileSync(file)});}};
// Vite's static server skips dot directories, including shared Windows
// dependencies intentionally stored below .backups. Serve only known KaTeX
// font names from that already allowed dependency; never broaden fs access.
const sharedFonts={name:'shared-katex-fonts',apply:'serve',configureServer(server){
 if(process.platform!=='win32'||!existsSync(modules))return;
 const directory=realpathSync(modules).replaceAll('\\','/')+'/katex/dist/fonts/';
 if(!directory.includes('/.'))return;
 const prefix='/@fs/'+directory;
 server.middlewares.use((request,response,next)=>{
  let pathname;try{pathname=decodeURIComponent(new URL(request.url,'http://localhost').pathname);}catch{return next();}
  if(!pathname.startsWith(prefix))return next();
  const name=pathname.slice(prefix.length),match=/^KaTeX_[A-Za-z0-9-]+\.(woff2?|ttf)$/.exec(name);
  if(!match||!existsSync(directory+name))return next();
  response.setHeader('Content-Type',match[1]==='ttf'?'font/ttf':'font/'+match[1]);
  response.setHeader('Cache-Control','no-cache');
  response.end(request.method==='HEAD'?undefined:readFileSync(directory+name));
 });
}};
export default defineConfig({ cacheDir:fileURLToPath(new URL('../.backups/next-150/vite-cache',import.meta.url)), plugins: [react(),sharedFonts,pdfAssets], resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } }, define: { __TB_VERSION__: JSON.stringify(readFileSync(new URL('../VERSION', import.meta.url), 'utf8').trim()) }, server: { fs:{allow:[root,...(existsSync(modules)?[realpathSync(modules)]:[]),pdfDirectory]}, proxy: { '/api': { target: process.env.TB_API_URL || 'http://127.0.0.1:18765', changeOrigin: true, configure(proxy) { proxy.on('proxyReq', (request) => { request.removeHeader('origin'); request.removeHeader('sec-fetch-site'); }); } } } }, build: { target: 'es2022' } });
