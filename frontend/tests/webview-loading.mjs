// Production bundle isolation and unchanged workspace sharing; no live account.
import assert from 'node:assert/strict';
import {readFile, readdir} from 'node:fs/promises';
import {createServer} from 'vite';
const server = await createServer({server:{host:'127.0.0.1',port:0}});
try {
  const {shareWorkspace, progressRows} = await server.ssrLoadModule('/src/models/workspaceModel.js');
  const previous = {now:'2026-10-16T01:00:00Z',training:[{id:'a',accepted:false}],sets:[],contests:[],activeContest:null,summary:{total:1}};
  const clockOnly = shareWorkspace(previous, {...structuredClone(previous),now:'2026-10-16T01:00:15Z'});
  assert.notEqual(clockOnly, previous);
  for (const key of ['training','sets','contests','summary']) assert.equal(clockOnly[key],previous[key]);
  const accepted = shareWorkspace(clockOnly,{...structuredClone(clockOnly),training:[{id:'a',accepted:true}]});
  assert.notEqual(accepted.training,clockOnly.training);
  assert.equal(accepted.sets,clockOnly.sets);
  assert.equal(previous.training[0].accepted,false,'sharing never mutates the previous snapshot');
  assert.equal(progressRows([{id:'a',difficulty:1200}],accepted)[0].accepted,true);
  const locked = shareWorkspace(accepted,{...structuredClone(accepted),activeContest:{slots:[{id:'a'}]}});
  assert.equal(progressRows([{id:'a',difficulty:1200}],locked)[0].difficulty,null,'contest locks still invalidate rows');
  assert.deepEqual(shareWorkspace({items:[1,2]},{items:[1]}),{items:[1]},'deletions are retained');
  const files = await readdir('dist/assets');
  const main = files.find(file => /^index-.*\.js$/.test(file));
  const text = await readFile(`dist/assets/${main}`,'utf8');
  assert.ok(Buffer.byteLength(text)<500000,'the startup chunk excludes Markdown/math and editor engines');
  assert.ok(files.some(file => /^MathTitle-.*\.js$/.test(file)));
  assert.ok(files.some(file => /^SolutionMarkdown-.*\.js$/.test(file)));
  console.log(JSON.stringify({ok:true,startupBytes:Buffer.byteLength(text),unchangedTrainingReused:true,acceptanceAndLocksInvalidate:true,readerAndEditorDeferred:true}));
} finally { await server.close(); }
