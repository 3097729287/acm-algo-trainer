import { randomBytes } from 'node:crypto';
import { AccountError, hashPassword, tokenHash } from './accounts.mjs';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const login = /^[a-z0-9_]{4,32}$/;
const resetPassword = '123456'; // Explicit maintenance reset only; never a response field.

function lookup(value) {
  if (typeof value !== 'string' || value.length > 80) throw new AccountError(400,'请输入完整登录号或公开 ID');
  let query=value.trim().toLowerCase();
  if (/^tb-[a-f0-9]{32}$/.test(query)) {
    const raw=query.slice(3);query=[raw.slice(0,8),raw.slice(8,12),raw.slice(12,16),raw.slice(16,20),raw.slice(20)].join('-');
  }
  if (!login.test(query) && !uuid.test(query)) throw new AccountError(400,'请输入完整登录号或公开 ID');
  return query;
}

function publicTarget(row,actor) {
  return {userId:row.user_id,loginId:row.login_id,nickname:row.nickname,createdAt:row.created_at,
    protected:row.user_id===actor || row.login_id==='admin' || Boolean(row.is_admin)};
}

// Every operation rechecks session and role inside its transaction. Selecting
// explicit public identity columns prevents accidental password/hash exposure.
export class AccountAdministration {
  constructor(database,dialect='mysql') {this.database=database;this.dialect=dialect;this.passwordHash=hashPassword;}
  async available() {
    try {await this.database.execute('SELECT action FROM account_admin_actions LIMIT 0');return true;}
    catch(error) {if(error.code==='ER_NO_SUCH_TABLE'||/no such table/i.test(error.message||''))return false;throw error;}
  }
  lock() {return this.dialect==='mysql'?' FOR UPDATE':'';}
  share() {return this.dialect==='mysql'?' FOR SHARE':'';}
  async liveSession(connection,actor,hash,clock) {
    const now=typeof clock==='function'?clock():clock;
    const [sessions]=await connection.execute(`SELECT s.token_hash FROM account_sessions s JOIN accounts a ON a.user_id=s.user_id
      WHERE s.user_id=? AND s.token_hash=? AND s.expires_at>? AND s.password_version=a.password_version`+this.share(),[actor,hash,now]);
    if(!sessions.length)throw new AccountError(401,'管理员登录已失效，请重新登录');
  }
  async actor(connection,actor,hash,clock) {
    await connection.execute('SELECT user_id FROM accounts WHERE user_id=?'+this.lock(),[actor]);
    // Sample the clock after potentially waiting for the account lock.
    await this.liveSession(connection,actor,hash,clock);
    const [roles]=await connection.execute('SELECT user_id FROM ranking_admins WHERE user_id=?'+this.share(),[actor]);
    if(!roles.length)throw new AccountError(403,'账号没有管理员权限');
  }
  async search(actor,hash,now,value) {
    const query=lookup(value);
    return this.database.transaction(async connection=>{
      await this.actor(connection,actor,hash,now);
      const [rows]=await connection.execute(`SELECT a.user_id,a.login_id,u.nickname,u.created_at,
        EXISTS(SELECT 1 FROM ranking_admins r WHERE r.user_id=a.user_id) AS is_admin
        FROM accounts a JOIN users u ON u.user_id=a.user_id WHERE ${uuid.test(query)?'a.user_id':'a.login_id'}=? LIMIT 1`,[query]);
      return {accounts:rows.map(row=>publicTarget(row,actor))};
    });
  }
  async target(connection,actor,value,action) {
    if (!value || Object.keys(value).sort().join(',')!=='confirmation,loginId,userId' || !uuid.test(value.userId||'')
      || typeof value.loginId!=='string' || !login.test(value.loginId) || value.confirmation!==action)
      throw new AccountError(400,'账号或操作确认无效');
    if(value.userId===actor)throw new AccountError(403,'不能修改当前管理员账号');
    const [rows]=await connection.execute(`SELECT a.user_id,a.login_id,u.nickname,u.created_at
      FROM accounts a JOIN users u ON u.user_id=a.user_id WHERE a.user_id=?`+this.lock(),[value.userId]);
    if(!rows.length)throw new AccountError(404,'账号不存在');
    const target=rows[0];
    const [roles]=await connection.execute('SELECT user_id FROM ranking_admins WHERE user_id=?'+this.share(),[target.user_id]);
    if(target.login_id==='admin'||roles.length)throw new AccountError(403,'不能修改管理员账号');
    if(target.login_id!==value.loginId)throw new AccountError(409,'账号信息已变化，请重新查找');
    return target;
  }
  async reset(actor,hash,now,value,timestamp) {
    // Scrypt is deliberately outside the SQL transaction; authority is checked
    // again after hashing, so an expired or revoked actor cannot use a late job.
    const encoded=await this.passwordHash(resetPassword);
    return this.database.transaction(async connection=>{
      await this.actor(connection,actor,hash,now);
      const target=await this.target(connection,actor,value,'reset-password');
      await this.liveSession(connection,actor,hash,now);
      await connection.execute('UPDATE accounts SET password_hash=?,password_version=password_version+1,updated_at=? WHERE user_id=?',[encoded,timestamp,target.user_id]);
      await connection.execute('DELETE FROM account_sessions WHERE user_id=?',[target.user_id]);
      await connection.execute('UPDATE users SET token_hash=?,updated_at=? WHERE user_id=?',[tokenHash(randomBytes(32)),timestamp,target.user_id]);
      await connection.execute('INSERT INTO account_admin_actions(actor_id,target_id,action,created_at) VALUES(?,?,?,?)',[actor,target.user_id,'reset-password',timestamp]);
      return {ok:true,userId:target.user_id,loginId:target.login_id,sessionsRevoked:true};
    });
  }
  async remove(actor,hash,now,value,timestamp) {
    return this.database.transaction(async connection=>{
      await this.actor(connection,actor,hash,now);
      const target=await this.target(connection,actor,value,'delete-account');
      await this.liveSession(connection,actor,hash,now);
      const id=target.user_id;
      // Explicit FK order works for existing schemas without destructive ALTERs.
      // Unknown new dependencies fail and roll back rather than disable FKs.
      await connection.execute('DELETE FROM social_notifications WHERE actor_id=? OR recipient_id=?',[id,id]);
      await connection.execute('DELETE FROM social_likes WHERE actor_id=? OR recipient_id=?',[id,id]);
      for(const table of ['training_list_likes','ranking_exclusions','official_ac_events','ac_events','ranking_rewards',
        'account_chunk_heads','account_chunks','account_chunk_usage','account_public_avatars','account_public_progress',
        'account_state','account_login_days','account_nicknames','account_sessions','accounts','users']) {
        const column=table==='training_list_likes'?'actor_id':'user_id';
        await connection.execute(`DELETE FROM ${table} WHERE ${column}=?`,[id]);
      }
      // No FK: maintenance history survives target deletion; contains no secret.
      await connection.execute('INSERT INTO account_admin_actions(actor_id,target_id,action,created_at) VALUES(?,?,?,?)',[actor,id,'delete-account',timestamp]);
      return {ok:true,userId:id,loginId:target.login_id,deleted:true};
    });
  }
}

export async function adminAccounts(request,env,user,now,{body,json,credentials,limit}) {
  if(!user.is_admin)throw new AccountError(403,'账号没有管理员权限');
  const store=env.STORE.accountAdmin;
  if(!store || !await store.available())throw new AccountError(503,'管理员账号维护服务尚未升级');
  const url=new URL(request.url),path=url.pathname.replace(/\/$/,''),hash=tokenHash(credentials(request).token),seconds=Math.floor(now/1000);
  // A request's initial timestamp is suitable for rate buckets, but not for
  // authorizing writes after scrypt/SQL lock waits. Tests inject their clock.
  const sessionClock=()=>Math.floor((env.TEST_NOW==null?Date.now():Number(env.TEST_NOW))/1000);
  if(path==='/v1/admin/accounts' && request.method==='GET') {
    await limit(env,'admin-account-search:'+user.user_id,30,60,seconds);
    return json(await store.search(user.user_id,hash,sessionClock,url.searchParams.get('q')));
  }
  if(['/v1/admin/accounts/delete','/v1/admin/accounts/reset-password'].includes(path)&&request.method==='POST') {
    await limit(env,'admin-account-write:'+user.user_id,10,300,seconds);
    const value=await body(request,['userId','loginId','confirmation'],2048);
    const method=path.endsWith('/delete')?'remove':'reset';
    return json(await store[method](user.user_id,hash,sessionClock,value,new Date(now).toISOString()));
  }
  throw new AccountError(404,'没有找到这个接口');
}
