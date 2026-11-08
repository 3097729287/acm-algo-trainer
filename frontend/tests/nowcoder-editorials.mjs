import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const root=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const out=join(root,'.backups/nowcoder-editorials/browser');await mkdir(out,{recursive:true});
const ledger=JSON.parse(await readFile(join(root,'data/nowcoder-editorials/reviewed.json'),'utf8'));
const ids=[];
for(const [id,entry] of Object.entries(ledger)){
 const article=await readFile(join(root,entry.articles.default),'utf8');
 if(article.includes('.gif)'))ids.push(id);
}
const source=String.raw`import json,sqlite3,pathlib
db=sqlite3.connect((pathlib.Path.cwd()/'data/library.sqlite3').as_uri()+'?mode=ro',uri=True)
ids=${JSON.stringify(ids)}
rows=[]
for identity in ids:
 r=db.execute('select markdown,images from solutions where problem_id=?',(identity,)).fetchone()
 rows.append({'id':identity,'markdown':r[0],'images':json.loads(r[1])})
print(json.dumps(rows))`;
const payload=execFileSync(process.env.TB_PYTHON||'python',['-c',source],{cwd:root,encoding:'utf8',windowsHide:true,maxBuffer:16*1024*1024});
const rows=JSON.parse(payload);for(const row of rows)assert(Object.values(row.images).some(v=>v.startsWith('data:image/gif;base64,')),row.id);
let vite,browser;const errors=[];const results=[];
try{
 vite=await createServer({root:join(root,'frontend'),server:{host:'127.0.0.1',port:0},
  optimizeDeps:{entries:['tests/nowcoder-editorials-fixture.html']},
  plugins:[{name:'verified-nowcoder-payload',configureServer(server){server.middlewares.use((req,res,next)=>{
   if(req.url!=='/__nowcoder_editorials')return next();res.setHeader('Content-Type','application/json');res.end(payload);
  });}}]});
 await vite.listen();const url='http://127.0.0.1:'+vite.httpServer.address().port;
 browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1480,height:940}});
 page.on('pageerror',e=>errors.push(e.message));await page.goto(url+'/tests/nowcoder-editorials-fixture.html');
 await page.locator('nav button').first().waitFor();
 for(const id of ids){
  await page.locator('nav button').filter({hasText:id}).click();
  await page.locator('main[data-problem-id="'+id+'"]').waitFor();
  const gif=page.locator('.reading-image-open img[src^="data:image/gif"]').first();
  await gif.scrollIntoViewIfNeeded();await gif.evaluate(img=>img.decode());
  assert.equal(await gif.evaluate(img=>img.naturalWidth),940);
  assert.equal(await page.locator('.reading-image-missing').count(),0);
  let before=createHash('sha256').update(await gif.screenshot()).digest('hex'),advanced=false;
  for(let attempt=0;attempt<6;attempt++){
   await page.waitForTimeout(900);const after=createHash('sha256').update(await gif.screenshot()).digest('hex');
   if(after!==before){advanced=true;break;}
  }
  assert(advanced,'GIF visibly advances in real ReadingImage: '+id);
  await gif.click();const dialog=page.locator('dialog[open]');await dialog.waitFor();
  assert.equal(await dialog.locator('img').evaluate(img=>img.naturalWidth),940);
  await dialog.getByRole('button',{name:'关闭',exact:true}).click();
  const block=page.locator('.editorial-code').last();await block.scrollIntoViewIfNeeded();
  const displayed=await block.locator('code').textContent();
  await block.getByRole('button',{name:'复制',exact:true}).click();
  assert.equal(await page.evaluate(()=>window.__nowcoderCopiedCode),displayed);
  assert(await block.locator('code span[class*="tok-"]').count()>0,'Syntax colors are present');
  results.push({id,gifAnimated:true,zoomPassed:true,copyMatchesDisplay:true,syntaxColorPassed:true});
 }
 await page.setViewportSize({width:740,height:900});
 await page.locator('nav button').first().click();const image=page.locator('.reading-image-open img[src^="data:image/gif"]').first();await image.scrollIntoViewIfNeeded();
 const bounds=await image.boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=740);
 await page.screenshot({path:join(out,'reader-narrow.png')});
 await page.evaluate(()=>document.documentElement.dataset.theme='dark');await page.screenshot({path:join(out,'reader-dark.png')});
 assert.deepEqual(errors,[]);await writeFile(join(out,'report.json'),JSON.stringify({problems:results,narrowWidth:740,darkThemePassed:true,errors},null,2)+'\n');
 console.log(JSON.stringify({animatedProblems:results.length,gifPlaybackPassed:true,zoomPassed:true,formattedCopyPassed:true,narrowAndDarkPassed:true,errors}));
}finally{await browser?.close();await vite?.close();}
