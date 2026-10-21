import { tokenHash, AccountError } from './accounts.mjs';
import { bounds } from './ranking-rules.mjs';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export const socialEvent = row => ({
  id:row.id, kind:row.kind, actor:{ userId:row.actor_id,nickname:row.actor_name },
  recipient:{ userId:row.recipient_id,nickname:row.recipient_name },
  text:row.body, createdAt:row.created_at, read:Boolean(row.read_at),
});
// Public activity never discloses private message text or inbox read receipts.
const socialActivity = row => ({
  id:row.id, kind:row.kind, actor:{userId:row.actor_id,nickname:row.actor_name},
  recipient:{userId:row.recipient_id,nickname:row.recipient_name}, createdAt:row.created_at,
});
export async function socialSnapshot(store,user,now) {
  if (!store.social || !await store.social.available()) return { available:false,protocol:1,totalLikes:0,todayLikes:0,unreadCount:0,notifications:[],activity:[] };
  const [summary,inbox,activity] = await Promise.all([
    store.social.summary(user.user_id,[user.user_id],bounds('daily',now).day),store.social.inbox(user.user_id),store.social.activity(),
  ]);
  return { available:true,protocol:1,totalLikes:summary.get(user.user_id).total,todayLikes:summary.get(user.user_id).today,unreadCount:inbox.unreadCount,notifications:inbox.rows.map(socialEvent),activity:activity.map(socialActivity) };
}
export async function rankingSocial(store,viewer,rows,day) {
  if (!store.social || !await store.social.available()) return false;
  const values = await store.social.summary(viewer,rows.map(row => row.userId),day);
  for (const row of rows) { const value=values.get(row.userId);row.likes={total:value?.total || 0,likedToday:value?.likedToday || false}; }
  return true;
}
export async function socialWrite(store,user,token,path,value,now) {
  if (!store.social || !await store.social.available()) throw new AccountError(503,'互动服务正在升级，请稍后重试');
  const hash=tokenHash(token), seconds=Math.floor(now/1000), timestamp=new Date(now).toISOString();
  if (path === '/v1/social/read') {
    const fields=Object.keys(value), all=fields.length===1 && fields[0]==='all' && value.all===true;
    const batch=fields.length===1 && fields[0]==='ids' && Array.isArray(value.ids) && value.ids.length<=100 && value.ids.every(id => typeof id==='string' && uuid.test(id));
    if (!all && !batch) throw new AccountError(400,'通知编号无效');
    return store.social.read(user.user_id,hash,seconds,all ? [] : [...new Set(value.ids)],timestamp,all);
  }
  if (!uuid.test(value.targetId || '') || value.targetId === user.user_id) throw new AccountError(400,'请选择其他训练者');
  if (!await store.findUser(value.targetId)) throw new AccountError(404,'用户不存在');
  if (path === '/v1/social/likes') {
    const result=await store.social.like(user.user_id,hash,seconds,value.targetId,bounds('daily',now).day,timestamp);
    const counts=await store.social.summary(user.user_id,[value.targetId],bounds('daily',now).day);
    return { ...result,targetId:value.targetId,likes:{total:counts.get(value.targetId).total,likedToday:counts.get(value.targetId).likedToday} };
  }
  if (typeof value.text !== 'string' || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value.text) || !value.text.trim() || [...value.text.trim()].length>500 || !uuid.test(value.requestId || '')) throw new AccountError(400,'留言须为 1–500 字');
  return store.social.comment(user.user_id,hash,seconds,value.targetId,value.text.trim(),value.requestId,timestamp);
}
