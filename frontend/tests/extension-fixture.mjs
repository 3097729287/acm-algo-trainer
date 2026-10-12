// Seed the disposable connector before Chromium starts its service worker.
// Its first heartbeat must never register with the user's real TB endpoint.
import assert from 'node:assert/strict';
import {cp,readFile,writeFile} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {promisify} from 'node:util';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const run=promisify(execFile);

export async function fixtureExtension(source,profile,base){
  assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);
  const destination=path.join(profile,'fixture-extension');
  if(path.resolve(source)===path.join(root,'build/browser-extension')&&!process.env.TB_BROWSER_EXTENSION){
    // A clean checkout has no bundle. Build current adapters in this disposable
    // profile so a stale local bundle cannot silently mask a source regression.
    const python=process.env.TB_PYTHON||(process.platform==='win32'?'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe':'python3');
    await run(python,['scripts/build_browser_extension.py',destination],{cwd:root,windowsHide:true,env:{...process.env,TB_OFFLINE:'1'}});
  }else{
    await cp(source,destination,{recursive:true});
  }
  const worker=path.join(destination,'worker.js');
  const text=await readFile(worker,'utf8');
  assert.ok(text.includes("'http://127.0.0.1:18765'"),'Connector default endpoint changed');
  await writeFile(worker,text.replaceAll("'http://127.0.0.1:18765'",JSON.stringify(base)),'utf8');
  return destination;
}
