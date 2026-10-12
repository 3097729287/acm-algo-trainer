// Seed the disposable connector before Chromium starts its service worker.
// Its first heartbeat must never register with the user's real TB endpoint.
import assert from 'node:assert/strict';
import {cp,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';

export async function fixtureExtension(source,profile,base){
  assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);
  const destination=path.join(profile,'fixture-extension');
  await cp(source,destination,{recursive:true});
  const worker=path.join(destination,'worker.js');
  const text=await readFile(worker,'utf8');
  assert.ok(text.includes("'http://127.0.0.1:18765'"),'Connector default endpoint changed');
  await writeFile(worker,text.replaceAll("'http://127.0.0.1:18765'",JSON.stringify(base)),'utf8');
  return destination;
}
