import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {publicRuntimeFiles,verifyRestoreReceipt} from '../scripts/verify-gameplay-restore.mjs';

test('production restore gate binds the exact baseline, backup, source and rehearsal',async()=>{
  // Retain disposable fixtures for Windows Recycle Bin retirement.
  const root=await mkdtemp(join(tmpdir(),'tb-restore-gate-')),stage=join(root,'stage'),baseline=join(root,'baseline');
  await mkdir(stage);await mkdir(baseline);
  for(const dir of ['src','mysql','scripts'])await mkdir(join(baseline,dir));
  await writeFile(join(baseline,'package.json'),JSON.stringify({version:'1.2.9'}));
  await writeFile(join(baseline,'package-lock.json'),'{}');
  await writeFile(join(baseline,'src/server.mjs'),'export const version="1.2.9";');
  const commit='a'.repeat(40),manifest='verified fixture manifest\n',now=Date.now();
  await writeFile(join(stage,'BUILD-INFO.json'),JSON.stringify({version:'1.4.0',sourceCommit:commit}));
  await writeFile(join(stage,'runtime-manifest.sha256'),manifest);
  const receipt={format:'tb-production-gameplay-restore-v1',passed:true,productionChanged:false,
    baselineRuntime:'1.2.9',candidateRuntime:'1.4.0',candidateSourceCommit:commit,restoreEngineVersion:'8.4.11',
    runtimeManifestSha256:createHash('sha256').update(manifest).digest('hex'),verifiedAt:new Date(now).toISOString(),
    checks:Object.fromEntries(['allTablesRestored','existingTablesUnchanged','oldClientCompatible',
      'runtimeRollbackPreservesNewData','reupgradeIdempotent','postMigrationBackupRestored'].map(key=>[key,true])),
    backup:{sha256:'b'.repeat(64),bytes:100000,serverPath:'/opt/tb-leaderboard/backups/preflight-150-20261102T000000Z/mysql-online.sql.gz',gzipVerified:true,downloadVerified:true},
    baselineFiles:await publicRuntimeFiles(baseline)};
  const save=async value=>writeFile(join(stage,'restore-verification.json'),JSON.stringify(value));
  await save(receipt);assert.deepEqual(await verifyRestoreReceipt(stage,baseline,commit,now),receipt.backup);
  for(const mutate of [r=>r.candidateSourceCommit='c'.repeat(40),r=>r.runtimeManifestSha256='d'.repeat(64),
    r=>r.restoreEngineVersion='8.0.27',r=>r.checks.runtimeRollbackPreservesNewData=false,
    r=>r.backup.gzipVerified=false,r=>r.backup.serverPath='/etc/passwd',r=>r.backup.bytes=536870913,
    r=>r.verifiedAt=new Date(now-86400001).toISOString(),r=>r.verifiedAt=new Date(now+1000).toISOString()]){
    const changed=structuredClone(receipt);mutate(changed);await save(changed);
    await assert.rejects(verifyRestoreReceipt(stage,baseline,commit,now));
  }
  await save(receipt);await writeFile(join(baseline,'src/server.mjs'),'changed runtime');
  await assert.rejects(verifyRestoreReceipt(stage,baseline,commit,now),/changed/);
});
