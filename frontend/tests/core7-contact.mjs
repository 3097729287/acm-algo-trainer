import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const folder=path.join(root,'.backups/core7-editorials-20261030');
const images=fs.readdirSync(path.join(folder,'render')).filter(p=>p.endsWith('-default-1440-figure-0.png')).sort();
const out=path.join(folder,'visual-review');fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
try{const page=await browser.newPage({viewport:{width:1560,height:1100}});
  for(let i=0;i<images.length;i+=4){
    const cells=images.slice(i,i+4).map(name=>`<article><p>${name}</p><img src="data:image/png;base64,${fs.readFileSync(path.join(folder,'render',name)).toString('base64')}"></article>`).join('');
    await page.setContent(`<style>body{margin:0;display:grid;grid-template-columns:780px 780px;font:14px Arial}article{height:550px;background:#edf0f4;padding:8px;box-sizing:border-box}p{margin:0 0 12px}img{display:block;width:100%;max-height:500px;object-fit:contain;object-position:top}</style>${cells}`);
    await page.screenshot({path:path.join(out,`figures-${i/4+1}.png`)});
  }
  console.log(JSON.stringify({figures:images.length,sheets:Math.ceil(images.length/4),out}));
}finally{await browser.close();}
