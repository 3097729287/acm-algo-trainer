import { randomUUID } from 'node:crypto';
import { AccountError } from './accounts.mjs';

// Storage-only adapter. API names and user snapshots never depend on SQL column order.
export class SocialStore {
  constructor(database, dialect = 'mysql') {
    this.database = database;
    this.dialect = dialect;
    this.checkedAt = 0;
    this.enabled = false;
  }
  async available() {
    if (Date.now() - this.checkedAt < 10000) return this.enabled;
    try {
      await this.database.execute('SELECT actor_id,recipient_id,liked_day,created_at FROM social_likes LIMIT 0');
      await this.database.execute('SELECT id,kind,actor_id,recipient_id,body,created_at,read_at FROM social_notifications LIMIT 0');
      this.enabled = true;
    } catch (error) {
      if (!['ER_NO_SUCH_TABLE','ER_BAD_FIELD_ERROR'].includes(error.code) && !/no such (?:table|column)/i.test(error.message || '')) throw error;
      this.enabled = false;
    }
    this.checkedAt = Date.now();
    return this.enabled;
  }
  async summary(viewer, ids, day, range=null) {
    const unique = [...new Set(ids)].slice(0, 201);
    if (!unique.length) return new Map();
    const [rows] = await this.database.execute(`SELECT recipient_id,COUNT(*) AS total,
      SUM(CASE WHEN liked_day=? THEN 1 ELSE 0 END) AS received_today,
      ${range?'SUM(CASE WHEN liked_day>=? AND liked_day<? THEN 1 ELSE 0 END)':'COUNT(*)'} AS received_period,
      SUM(CASE WHEN actor_id=? AND liked_day=? THEN 1 ELSE 0 END) AS liked_today
      FROM social_likes WHERE recipient_id IN (${unique.map(() => '?').join(',')}) GROUP BY recipient_id`, [day,...range?[range.start,range.end]:[],viewer,day,...unique]);
    const result = new Map(unique.map(id => [id,{ total:0, today:0, period:0, likedToday:false }]));
    for (const row of rows) result.set(row.recipient_id,{ total:Number(row.total), today:Number(row.received_today), period:Number(row.received_period), likedToday:Boolean(Number(row.liked_today)) });
    return result;
  }
  async listAvailable() {
    try {
      await this.database.execute('SELECT list_id FROM training_list_likes LIMIT 0');
      return true;
    } catch(error) {
      if (error.code==='ER_NO_SUCH_TABLE' || /no such table/i.test(error.message||'')) return false;
      throw error;
    }
  }
  async listSummary(viewer, ids, day) {
    const result=Object.fromEntries(ids.map(id=>[id,{total:0,likedToday:false}]));
    if(!ids.length)return result;
    const [rows]=await this.database.execute(`SELECT list_id,COUNT(DISTINCT actor_id) AS total,
      MAX(CASE WHEN actor_id=? THEN 1 ELSE 0 END) AS liked_today
      FROM training_list_likes WHERE list_id IN (${ids.map(()=>'?').join(',')}) GROUP BY list_id`,[viewer,...ids]);
    for(const row of rows)result[row.list_id]={total:Number(row.total),likedToday:Boolean(Number(row.liked_today))};
    return result;
  }
  async likeList(actor, hash, now, identity, day, timestamp, liked=true) {
    return this.database.transaction(async connection=>{
      await this.assertSession(connection,actor,hash,now);
      if(!liked){const [removed]=await connection.execute('DELETE FROM training_list_likes WHERE actor_id=? AND list_id=?',[actor,identity]);return {created:false,removed:removed.affectedRows>0};}
      const [existing]=await connection.execute('SELECT list_id FROM training_list_likes WHERE actor_id=? AND list_id=? LIMIT 1',[actor,identity]);
      if(existing.length)return {created:false};
      const insert=this.dialect==='mysql'?'INSERT IGNORE':'INSERT OR IGNORE';
      const [result]=await connection.execute(`${insert} INTO training_list_likes(actor_id,list_id,liked_day,created_at) VALUES(?,?,?,?)`,[actor,identity,day,timestamp]);
      return {created:result.affectedRows===1};
    });
  }
  async inbox(id) {
    const [rows] = await this.database.execute(`SELECT n.id,n.kind,n.actor_id,n.recipient_id,n.body,n.created_at,n.read_at,
      a.nickname AS actor_name,r.nickname AS recipient_name FROM social_notifications n
      JOIN users a ON a.user_id=n.actor_id JOIN users r ON r.user_id=n.recipient_id
      WHERE n.recipient_id=? ORDER BY n.created_at DESC,n.id DESC LIMIT 100`, [id]);
    const [unread] = await this.database.execute('SELECT COUNT(*) AS n FROM social_notifications WHERE recipient_id=? AND read_at IS NULL', [id]);
    return { rows, unreadCount:Number(unread[0].n) };
  }
  async activity() {
    const [rows] = await this.database.execute(`SELECT n.id,n.kind,n.actor_id,n.recipient_id,n.created_at,
      a.nickname AS actor_name,r.nickname AS recipient_name FROM social_notifications n
      JOIN users a ON a.user_id=n.actor_id JOIN users r ON r.user_id=n.recipient_id
      WHERE n.kind='like' ORDER BY n.created_at DESC,n.id DESC LIMIT 30`);
    return rows;
  }
  async assertSession(connection, actor, hash, now) {
    await connection.execute('SELECT user_id FROM accounts WHERE user_id=?' + (this.dialect === 'mysql' ? ' FOR UPDATE' : ''), [actor]);
    const [sessions] = await connection.execute(`SELECT s.token_hash FROM account_sessions s JOIN accounts a ON a.user_id=s.user_id
      WHERE s.user_id=? AND s.token_hash=? AND s.expires_at>? AND s.password_version=a.password_version`, [actor,hash,now]);
    if (!sessions.length) throw new AccountError(401,'登录已失效，请重新登录');
  }
  async like(actor, hash, now, recipient, day, timestamp) {
    return this.database.transaction(async connection => {
      await this.assertSession(connection,actor,hash,now);
      const insert = this.dialect === 'mysql' ? 'INSERT IGNORE' : 'INSERT OR IGNORE';
      const [result] = await connection.execute(`${insert} INTO social_likes(actor_id,recipient_id,liked_day,created_at) VALUES(?,?,?,?)`, [actor,recipient,day,timestamp]);
      const created = result.affectedRows === 1;
      if (created) await connection.execute('INSERT INTO social_notifications(id,kind,actor_id,recipient_id,body,created_at) VALUES(?,?,?,?,?,?)', [randomUUID(),'like',actor,recipient,'',timestamp]);
      return { created };
    });
  }
  async comment(actor, hash, now, recipient, text, requestId, timestamp) {
    return this.database.transaction(async connection => {
      await this.assertSession(connection,actor,hash,now);
      const [existing] = await connection.execute('SELECT actor_id,recipient_id,body FROM social_notifications WHERE id=?', [requestId]);
      if (existing.length) {
        const row = existing[0];
        if (row.actor_id !== actor || row.recipient_id !== recipient || row.body !== text) throw new AccountError(409,'留言请求已被使用，请重新发送');
        return { created:false, id:requestId };
      }
      await connection.execute('INSERT INTO social_notifications(id,kind,actor_id,recipient_id,body,created_at) VALUES(?,?,?,?,?,?)', [requestId,'comment',actor,recipient,text,timestamp]);
      return { created:true, id:requestId };
    });
  }
  async read(actor, hash, now, ids, timestamp, all=false) {
    return this.database.transaction(async connection => {
      await this.assertSession(connection,actor,hash,now);
      if (all===true) await connection.execute('UPDATE social_notifications SET read_at=? WHERE recipient_id=? AND read_at IS NULL', [timestamp,actor]);
      else if (ids.length) await connection.execute(`UPDATE social_notifications SET read_at=? WHERE recipient_id=? AND read_at IS NULL AND id IN (${ids.map(() => '?').join(',')})`, [timestamp,actor,...ids]);
      return { ok:true };
    });
  }
}
