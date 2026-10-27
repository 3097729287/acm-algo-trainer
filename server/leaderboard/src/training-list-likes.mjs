import {readFileSync} from 'node:fs';
import {tokenHash, AccountError} from './accounts.mjs';
import {bounds} from './ranking-rules.mjs';

const publicLists=new Set(JSON.parse(readFileSync(new URL('./training-list-ids.json',import.meta.url),'utf8')));
export async function trainingListLikes(store,user,token,ids,write,now,liked=true) {
  if(!Array.isArray(ids)||ids.length>100||ids.some(id=>typeof id!=='string'||!publicLists.has(id)))throw new AccountError(400,'题单编号无效');
  const unique=ids.length?[...new Set(ids)]:write?[]:[...publicLists],day=bounds('daily',now).day;
  if(!store.social||!await store.social.listAvailable()) {
    if(write)throw new AccountError(503,'题单点赞暂不可用，请稍后重试');
    return {available:false,day,likes:{}};
  }
  let result;
  if(write)result=await store.social.likeList(user.user_id,tokenHash(token),Math.floor(now/1000),unique[0],day,new Date(now).toISOString(),liked);
  const likes=await store.social.listSummary(user.user_id,unique,day);
  return write?{...result,listId:unique[0],likes:likes[unique[0]],day}:{available:true,likes,day};
}
