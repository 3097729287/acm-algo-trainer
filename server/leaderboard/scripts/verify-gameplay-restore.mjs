// Deployment evidence must identify the actual production baseline and artifact.
// No SQL, credentials or personal payloads are read by this check.
import {readFile,readdir,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const sha=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
export async function publicRuntimeFiles(root) {
  const result={};
  async function visit(name) {
    const path=join(root,name),stat=await lstat(path);
    if(stat.isSymbolicLink())throw new Error('Baseline public runtime contains a symbolic link.');
    if(stat.isDirectory()) {
      for(const child of (await readdir(path)).sort())await visit(name+'/'+child);
    } else if(stat.isFile()) result[name]=hash(await readFile(path));
    else throw new Error('Unsupported baseline public file.');
  }
  for(const name of ['package.json','package-lock.json','src','mysql','scripts'])await visit(name);
  return result;
}
export async function verifyRestoreReceipt(stage,baseline,commit,now=Date.now()) {
  const receipt=JSON.parse(await readFile(join(stage,'restore-verification.json'),'utf8'));
  const build=JSON.parse(await readFile(join(stage,'BUILD-INFO.json'),'utf8'));
  const baselinePackage=JSON.parse(await readFile(join(baseline,'package.json'),'utf8'));
  if(receipt.format!=='tb-production-gameplay-restore-v1'||receipt.passed!==true||receipt.productionChanged!==false||
    receipt.baselineRuntime!=='1.2.9'||receipt.candidateRuntime!=='1.4.0'||baselinePackage.version!=='1.2.9'||
    receipt.restoreEngineVersion!=='8.4.11'||!/^[a-f0-9]{40}$/.test(commit)||
    receipt.candidateSourceCommit!==commit||build.sourceCommit!==commit||build.version!=='1.4.0'||
    receipt.runtimeManifestSha256!==hash(await readFile(join(stage,'runtime-manifest.sha256'))))
    throw new Error('Restore receipt does not identify the reviewed production baseline and candidate.');
  const age=now-Date.parse(receipt.verifiedAt);
  if(!Number.isFinite(age)||age<0||age>86400000)throw new Error('Restore verification must be reviewed within 24 hours.');
  for(const check of ['allTablesRestored','existingTablesUnchanged','oldClientCompatible',
    'runtimeRollbackPreservesNewData','reupgradeIdempotent','postMigrationBackupRestored'])
    if(receipt.checks?.[check]!==true)throw new Error('Missing restore or rollback verification: '+check);
  const backup=receipt.backup;
  if(!sha(backup?.sha256)||!Number.isSafeInteger(backup.bytes)||backup.bytes<1024||backup.bytes>536870912||
    !/^\/opt\/tb-leaderboard\/backups\/preflight-150-\d{8}T\d{6}Z\/mysql-online\.sql\.gz$/.test(backup.serverPath)||
    backup.gzipVerified!==true||backup.downloadVerified!==true)
    throw new Error('A complete, bounded and verified production backup is required.');
  const actual=await publicRuntimeFiles(baseline),expected=receipt.baselineFiles;
  if(!expected||Object.keys(actual).length!==Object.keys(expected).length||
    Object.entries(actual).some(([name,digest])=>expected[name]!==digest))
    throw new Error('Production runtime changed after its restore rehearsal.');
  return backup;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  try {
    const backup=await verifyRestoreReceipt(...process.argv.slice(2));
    process.stdout.write(`${backup.sha256} ${backup.bytes} ${backup.serverPath}\n`);
  }catch(error){process.stderr.write(error.message+'\n');process.exitCode=1;}
}
