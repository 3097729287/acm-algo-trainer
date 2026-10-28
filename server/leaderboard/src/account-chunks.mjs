import {createHash} from 'node:crypto';
import {AccountError} from './accounts.mjs';

export const CHUNK_LIMIT=128*1024;
export const CHUNK_BYTES=66*1024;
const hashPattern=/^[a-f0-9]{64}$/;
export function chunkHash(kind,bytes,children) {
  return createHash('sha256').update(kind+'\n'+children.join('')+'\n').update(bytes).digest('hex');
}
export function validateChunk(hash,value) {
  if(!hashPattern.test(hash)||!value||Object.keys(value).some(k=>!['kind','data','children'].includes(k))||
     !['data','concat'].includes(value.kind)||typeof value.data!=='string'||value.data.length>Math.ceil(CHUNK_BYTES/3)*4||
     !/^[A-Za-z0-9+/]+={0,2}$/.test(value.data)||!Array.isArray(value.children)||value.children.length>256||
     value.children.some((h,i)=>!hashPattern.test(h)||i&&h<=value.children[i-1]))
    throw new AccountError(400,'同步分块格式无效');
  const bytes=Buffer.from(value.data,'base64');
  if(bytes.length<1||bytes.length>CHUNK_BYTES||bytes.toString('base64')!==value.data||chunkHash(value.kind,bytes,value.children)!==hash)
    throw new AccountError(400,'同步分块校验失败');
  // Opaque gzip bytes are never expanded in the service's small Node heap.
  return {kind:value.kind,bytes,children:value.children};
}
export function validateHashes(value) {
  if(!Array.isArray(value)||value.length>128||value.some(h=>!hashPattern.test(h))||new Set(value).size!==value.length)
    throw new AccountError(400,'同步分块清单无效');
  return value;
}

export class AccountChunks {
  constructor(database,dialect='mysql') {this.database=database;this.dialect=dialect;this.checkedAt=0;this.enabled=false;}
  async available() {
    if(Date.now()-this.checkedAt<10000)return this.enabled;
    try {await this.database.execute('SELECT root_hash FROM account_chunk_heads LIMIT 0');await this.database.execute('SELECT hash FROM account_chunks LIMIT 0');this.enabled=true;}
    catch(error) {if(error.code!=='ER_NO_SUCH_TABLE'&&!/no such table/i.test(error.message||''))throw error;this.enabled=false;}
    this.checkedAt=Date.now();return this.enabled;
  }
  async head(id,cached) {
    const [rows]=await this.database.execute('SELECT revision,root_hash,updated_at FROM account_chunk_heads WHERE user_id=?',[id]);
    const row=rows[0];
    if(row&&Number(row.revision)===cached)return {protocol:2,revision:cached,unchanged:true};
    if(row)return {protocol:2,revision:Number(row.revision),root:row.root_hash,savedAt:row.updated_at};
    const [legacy]=await this.database.execute('SELECT revision FROM account_state WHERE user_id=?',[id]);
    return {protocol:2,revision:Number(legacy[0]?.revision||0),root:null,legacy:true};
  }
  async active(id) {
    const [rows]=await this.database.execute('SELECT revision FROM account_chunk_heads WHERE user_id=?',[id]);
    return rows[0]?Number(rows[0].revision):0;
  }
  async assertSession(connection,id,token,now) {
    if(this.dialect==='mysql')await connection.execute('SELECT user_id FROM accounts WHERE user_id=? FOR UPDATE',[id]);
    const [sessions]=await connection.execute('SELECT token_hash FROM account_sessions WHERE user_id=? AND token_hash=? AND expires_at>?',[id,token,now]);
    if(!sessions.length)throw new AccountError(401,'账号已在另一台设备登录，请重新登录');
  }
  async missing(id,hashes,timestamp) {
    if(!hashes.length)return [];
    const slots=hashes.map(()=>'?').join(',');
    const [rows]=await this.database.execute(`SELECT hash FROM account_chunks WHERE user_id=? AND hash IN (${slots})`,[id,...hashes]);
    // A resumed upload protects every already present dependency from age GC.
    await this.database.execute(`UPDATE account_chunks SET seen_at=? WHERE user_id=? AND hash IN (${slots})`,[timestamp,id,...hashes]);
    const found=new Set(rows.map(r=>r.hash));return hashes.filter(h=>!found.has(h));
  }
  async get(id,hash) {
    if(!hashPattern.test(hash))throw new AccountError(400,'同步分块编号无效');
    const [rows]=await this.database.execute('SELECT kind,payload,children FROM account_chunks WHERE user_id=? AND hash=?',[id,hash]);
    if(!rows.length)throw new AccountError(404,'没有找到账号同步分块');
    const row=rows[0];return {kind:row.kind,data:Buffer.from(row.payload).toString('base64'),children:JSON.parse(row.children)};
  }
  async put(id,token,now,hash,value,timestamp) {
    return this.database.transaction(async connection=>{
      await this.assertSession(connection,id,token,now);
      const [old]=await connection.execute('SELECT hash FROM account_chunks WHERE user_id=? AND hash=?',[id,hash]);
      if(old.length){await connection.execute('UPDATE account_chunks SET seen_at=? WHERE user_id=? AND hash=?',[timestamp,id,hash]);return {ok:true,existing:true};}
      // Require dependencies first, making the immutable object graph acyclic.
      if(value.children.length) {
        const [children]=await connection.execute(`SELECT hash FROM account_chunks WHERE user_id=? AND hash IN (${value.children.map(()=>'?').join(',')})`,[id,...value.children]);
        if(children.length!==value.children.length)throw new AccountError(409,'同步分块尚未完整上传，请重试');
      }
      let [usage]=await connection.execute('SELECT byte_count AS bytes,object_count AS n FROM account_chunk_usage WHERE user_id=?',[id]);
      if(!usage.length) {
        [usage]=await connection.execute('SELECT COALESCE(SUM(byte_count),0) AS bytes,COUNT(*) AS n FROM account_chunks WHERE user_id=?',[id]);
        await connection.execute('INSERT INTO account_chunk_usage(user_id,byte_count,object_count) VALUES(?,?,?)',[id,Number(usage[0].bytes),Number(usage[0].n)]);
      }
      if(Number(usage[0].bytes)+value.bytes.length>1024*1024*1024||Number(usage[0].n)>=200000)
        throw new AccountError(413,'账号同步存储已达容量，请联系维护者；本机数据已保留');
      await connection.execute('INSERT INTO account_chunks(user_id,hash,kind,payload,children,byte_count,created_at,seen_at) VALUES(?,?,?,?,?,?,?,?)',
        [id,hash,value.kind,value.bytes,JSON.stringify(value.children),value.bytes.length,timestamp,timestamp]);
      await connection.execute('UPDATE account_chunk_usage SET byte_count=byte_count+?,object_count=object_count+1 WHERE user_id=?',[value.bytes.length,id]);
      return {ok:true,existing:false};
    });
  }
  async commit(id,token,now,revision,root,timestamp) {
    if(!Number.isSafeInteger(revision)||revision<0||!hashPattern.test(root||''))throw new AccountError(400,'同步版本或根分块无效');
    return this.database.transaction(async connection=>{
      await this.assertSession(connection,id,token,now);
      const [heads]=await connection.execute('SELECT revision,root_hash FROM account_chunk_heads WHERE user_id=?',[id]);
      const [legacy]=heads.length?[[]]:await connection.execute('SELECT revision FROM account_state WHERE user_id=?',[id]);
      const previous=heads[0],current=Number(previous?.revision||legacy[0]?.revision||0);
      if(current!==revision)throw new AccountError(409,'账号数据已更新，请重新同步');
      const [chunks]=await connection.execute('SELECT hash FROM account_chunks WHERE user_id=? AND hash=?',[id,root]);
      if(!chunks.length)throw new AccountError(409,'根分块尚未完整上传');
      const values=[id,revision+1,root,previous?.root_hash||null,timestamp];
      const sql=this.dialect==='mysql'?
        'INSERT INTO account_chunk_heads(user_id,revision,root_hash,previous_root,updated_at) VALUES(?,?,?,?,?) ON DUPLICATE KEY UPDATE revision=VALUES(revision),root_hash=VALUES(root_hash),previous_root=VALUES(previous_root),updated_at=VALUES(updated_at)':
        'INSERT INTO account_chunk_heads(user_id,revision,root_hash,previous_root,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET revision=excluded.revision,root_hash=excluded.root_hash,previous_root=excluded.previous_root,updated_at=excluded.updated_at';
      await connection.execute(sql,values);
      return {protocol:2,revision:revision+1,root,savedAt:timestamp};
    });
  }
  async collect(id,cutoff) {
    // Run only at a maintenance boundary, under the same account lock as
    // upload/commit. Keep current + previous complete graphs, and 30 days of
    // uncommitted/recovery chunks. No code reachable from either root is lost.
    return this.database.transaction(async connection=>{
      if(this.dialect==='mysql')await connection.execute('SELECT user_id FROM accounts WHERE user_id=? FOR UPDATE',[id]);
      const [heads]=await connection.execute('SELECT root_hash,previous_root FROM account_chunk_heads WHERE user_id=?',[id]);
      if(!heads.length)return {removed:0};
      const keep=new Set(),pending=[heads[0].root_hash,heads[0].previous_root].filter(Boolean);
      while(pending.length) {
        const batch=[...new Set(pending.splice(0,128))].filter(h=>!keep.has(h));
        if(!batch.length)continue;
        for(const h of batch)keep.add(h);
        const [rows]=await connection.execute(`SELECT hash,children FROM account_chunks WHERE user_id=? AND hash IN (${batch.map(()=>'?').join(',')})`,[id,...batch]);
        if(rows.length!==batch.length)throw new AccountError(503,'同步图不完整，已停止清理');
        for(const row of rows)for(const h of JSON.parse(row.children))if(!keep.has(h))pending.push(h);
        if(keep.size>200000)throw new AccountError(503,'同步图校验未通过，已停止清理');
      }
      const [rows]=await connection.execute('SELECT hash,byte_count FROM account_chunks WHERE user_id=? AND seen_at<?',[id,cutoff]);
      const removed=rows.filter(r=>!keep.has(r.hash)),remove=removed.map(r=>r.hash);
      for(let i=0;i<remove.length;i+=128){const batch=remove.slice(i,i+128);await connection.execute(`DELETE FROM account_chunks WHERE user_id=? AND hash IN (${batch.map(()=>'?').join(',')})`,[id,...batch]);}
      if(remove.length)await connection.execute('UPDATE account_chunk_usage SET byte_count=byte_count-?,object_count=object_count-? WHERE user_id=?',[removed.reduce((n,r)=>n+Number(r.byte_count),0),remove.length,id]);
      await connection.execute('UPDATE account_chunk_usage SET last_gc_at=? WHERE user_id=?',[new Date().toISOString(),id]);
      return {removed:remove.length};
    });
  }
  async maintain(now=Date.now()) {
    if(!await this.available())return;
    const stamp=new Date(now-86400000).toISOString(),cutoff=new Date(now-30*86400000).toISOString();
    const [owners]=await this.database.execute('SELECT user_id FROM account_chunk_usage WHERE last_gc_at<? ORDER BY last_gc_at,user_id LIMIT 8',[stamp]);
    for(const row of owners)await this.collect(row.user_id,cutoff);
  }
}
