// Read-only migration evidence. No identities, code, payloads or secrets leave SQL.
import { readFile } from 'node:fs/promises';
import { isDeepStrictEqual } from 'node:util';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { openStore } from '../src/mysql-store.mjs';

const coreTables = ['users','accounts','account_state','account_sessions','account_public_progress',
  'account_nicknames','account_login_days','ac_events','official_ac_events','ranking_admins',
  'ranking_exclusions','ranking_schedule','ranking_cycles','ranking_rewards','ranking_admin_actions'];
const socialTables = ['social_likes','social_notifications'];
const appearanceTables=['account_public_avatars'];
const listTables=['training_list_likes'];
const chunkTables=['account_chunk_heads','account_chunk_usage','account_chunks'];
const adminTables=['account_admin_actions'];
const identifier = name => '`' + name.replaceAll('`','``') + '`';

export async function preservedData(pool) {
  const [existing] = await pool.execute('SELECT TABLE_NAME AS name FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()');
  const present = new Set(existing.map(row=>row.name));
  if (coreTables.some(name=>!present.has(name))) throw new Error('Existing account migrations 001–007 are required.');
  const tables = {};
  // A consistent SQL snapshot and order-independent SHA-256 row fingerprints
  // avoid loading all historical ACs or private state into Node memory.
  const connection = await pool.getConnection();
  try {
    await connection.query('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
    await connection.query('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY');
    for (const table of [...coreTables,...socialTables,...appearanceTables,...listTables,...chunkTables,...adminTables].sort()) {
      if (!present.has(table)) continue;
      const [columns] = await connection.execute('SELECT COLUMN_NAME AS name,DATA_TYPE AS kind FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? ORDER BY ORDINAL_POSITION',[table]);
      const names = columns.map(row=>row.name);
      // Chunk payloads are gzip bytes. JSON must receive their lossless hex,
      // rather than attempting to decode arbitrary binary as UTF-8 text.
      const values=columns.map(row=>/blob|binary/i.test(row.kind)?`HEX(${identifier(row.name)})`:identifier(row.name));
      const hash = `SHA2(CAST(JSON_ARRAY(${values.join(',')}) AS CHAR CHARACTER SET utf8mb4),256)`;
      // Keep each lane within the signed 64-bit range. Some MySQL expression
      // combinations clamp an unsigned 64-bit BIT_XOR through COALESCE/HEX;
      // eight 32-bit lanes preserve all 256 SHA bits without that conversion.
      const parts = [1,9,17,25,33,41,49,57].map((offset,index)=>`LPAD(HEX(COALESCE(BIT_XOR(CAST(CONV(SUBSTRING(h,${offset},8),16,10) AS UNSIGNED)),0)),8,'0') AS h${index}`);
      const [[row]] = await connection.query(`SELECT COUNT(*) AS n,${parts.join(',')} FROM (SELECT ${hash} AS h FROM ${identifier(table)}) AS fingerprints`);
      tables[table] = {rows:Number(row.n),columns:names,xorSha256:Array.from({length:8},(_,index)=>row['h'+index]).join('').toLowerCase()};
    }
    const [[rewards]] = await connection.query('SELECT COALESCE(SUM(xp),0) AS xp FROM ranking_rewards');
    const [[state]] = await connection.query('SELECT COALESCE(SUM(OCTET_LENGTH(payload)),0) AS bytes,COALESCE(SUM(revision),0) AS revisions FROM account_state');
    await connection.commit();
    return {format:'tb-preserved-data-v1',tables,totals:{rankingRewardXp:Number(rewards.xp),accountStateBytes:Number(state.bytes),accountStateRevisions:Number(state.revisions)}};
  } catch (error) { await connection.rollback(); throw error; }
  finally { connection.release(); }
}

export function assertPreserved(before,after,{requireAvatar=false,requireLists=false,requireChunks=false,requireAdmin=false}={}) {
  if (before?.format!=='tb-preserved-data-v1' || after?.format!==before.format ||
      !isDeepStrictEqual(before.totals,after.totals)) throw new Error('Preserved data totals differ.');
  for (const table of coreTables) {
    if (!before.tables?.[table] || !isDeepStrictEqual(before.tables[table],after.tables?.[table]))
      throw new Error('Preserved account data differs: '+table);
  }
  for (const table of [...socialTables,...appearanceTables.filter(name=>requireAvatar||before.tables?.[name]||after.tables?.[name]),...listTables.filter(name=>requireLists||before.tables?.[name]||after.tables?.[name]),...chunkTables.filter(name=>requireChunks||before.tables?.[name]||after.tables?.[name]),...adminTables.filter(name=>requireAdmin||before.tables?.[name]||after.tables?.[name])]) {
    if (!after.tables?.[table]) throw new Error('Additive migration is incomplete.');
    if (before.tables?.[table] ? !isDeepStrictEqual(before.tables[table],after.tables[table]) : after.tables[table].rows!==0)
      throw new Error('Existing social data differs: '+table);
  }
}

async function main() {
  const mode=process.argv[2];
  if (mode==='--compare'||mode==='--compare-chunks'||mode==='--compare-admin') {
    const chunks=[];
    let bytes=0;
    for await (const chunk of process.stdin) {
      bytes+=chunk.length;
      if (bytes>131072) throw new Error('Audit input exceeds its bound.');
      chunks.push(chunk);
    }
    const input=Buffer.concat(chunks).toString('utf8');
    const lines=input.trim().split('\n');
    if (lines.length!==2) throw new Error('Provide exactly two fingerprint documents.');
    assertPreserved(...lines.map(line=>JSON.parse(line)),{requireAvatar:true,requireLists:true,requireChunks:mode!=='--compare',requireAdmin:mode==='--compare-admin'});
    process.stdout.write('Preserved account, snapshot, receipt and XP fingerprints match.\n');
    return;
  }
  if (mode==='--stage') {
    const value=JSON.parse(await readFile(new URL('../BUILD-INFO.json',import.meta.url),'utf8'));
    if (value.format!=='tb-account-runtime-v1' || value.version!=='1.2.9' ||
        !/^[0-9a-f]{40}$/.test(value.sourceCommit) || value.sourceCommit!==process.argv[3])
      throw new Error('Staged source identity does not match the reviewed commit.');
    process.stdout.write('Staged source identity verified.\n');
    return;
  }
  if (mode!==undefined) throw new Error('Unknown audit mode.');
  const store=await openStore();
  try { process.stdout.write(JSON.stringify(await preservedData(store.pool))+'\n'); }
  finally { await store.close(); }
}

if (process.argv[1] && fileURLToPath(import.meta.url).toLowerCase()===resolve(process.argv[1]).toLowerCase()) {
  try { await main(); }
  catch { process.stderr.write('Data preservation audit failed; inspect the private deployment evidence.\n'); process.exitCode=1; }
}
