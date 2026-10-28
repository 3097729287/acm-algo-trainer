import {CHUNK_LIMIT,validateChunk,validateHashes} from './account-chunks.mjs';
import {validateAvatar} from './public-avatar.mjs';
import { EventConflict } from './errors.mjs';
import { bounds, REWARD_POLICY } from './ranking-rules.mjs';
import { AccountError, loginId, password, verifyPassword, hashPassword, tokenHash,
  session, publicAccount, registerAccount } from './accounts.mjs';
import { validateState, guardStateJson, STATE_LIMIT } from './account-state.mjs';
import { publicId, storedPublicProgress, validatePublicProgress } from './public-progress.mjs';
import { socialSnapshot, socialWrite, rankingSocial } from './social.mjs';
import {trainingListLikes} from './training-list-likes.mjs';

const VERSION = '1.2.8';
const NOTICE = '排行统计 TB 保存的原站已确认首次 AC 题数；样例、运行与重复题不计入。记录由客户端同步，暂不提供独立防作弊认证。';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const hashPattern = /^[a-f0-9]{64}$/;
class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

function json(value, status = 200, extra = {}) {
  return new Response(JSON.stringify(value), { status, headers: {
    'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff', ...extra,
  } });
}

async function digest(value) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function equalHash(a, b) {
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let index = 0; index < a.length; index++) difference |= a.charCodeAt(index) ^ b.charCodeAt(index);
  return difference === 0;
}

function nickname(value) {
  if (typeof value !== 'string' || /[\u0000-\u001f\u007f]/u.test(value)) throw new ApiError(400, '昵称无效');
  const result = value.trim();
  if ([...result].length < 1 || [...result].length > 32 || new TextEncoder().encode(result).length > 128) throw new ApiError(400, '昵称须为 1–32 个可显示字符');
  return result;
}

async function body(request, allowed, maximum = 65536, shallowEnvelope = true) {
  if (!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')) throw new ApiError(415, '请求须使用 application/json');
  const declared = Number(request.headers.get('Content-Length') || 0);
  if (!Number.isFinite(declared) || declared > maximum) throw new ApiError(413, '请求内容过大');
  if (!request.body) throw new ApiError(400, '缺少 JSON 请求');
  const reader = request.body.getReader();
  const chunks = []; let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > maximum) { await reader.cancel(); throw new ApiError(413, '请求内容过大'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  if (shallowEnvelope && maximum > 65536 && size > 65536) guardStateJson(bytes);
  let value;
  try { value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)); }
  catch { throw new ApiError(400, 'JSON 请求无效'); }
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).some(key => !allowed.includes(key))) throw new ApiError(400, '请求字段无效');
  return value;
}

function credentials(request) {
  const userId = request.headers.get('X-TB-User') || '';
  const bearer = /^Bearer ([A-Za-z0-9_-]{32,200})$/.exec(request.headers.get('Authorization') || '');
  if (!uuid.test(userId) || !bearer) throw new ApiError(401, '请先登录账号');
  return { userId, token: bearer[1] };
}

export async function authenticate(request, env, now) {
  const auth = credentials(request);
  const user = await env.STORE.findSession(auth.userId, tokenHash(auth.token), Math.floor(now / 1000));
  if (!user) throw new ApiError(401, '登录已失效，请重新登录');
  return user;
}

async function limit(env, bucket, maximum, windowSeconds, now) {
  const window = Math.floor(now / windowSeconds);
  const key = bucket + ':' + window;
  const count = await env.STORE.incrementLimit(key, (window + 1) * windowSeconds);
  if (count > maximum) throw new ApiError(429, '请求过于频繁，请稍后重试');
}

function rankingRow(row) {
  return { rank: row.rank, userId: row.user_id, publicId: publicId(row.user_id), nickname: row.nickname,
    displayName: row.nickname, count: row.count, avatarHash: row.avatar_hash||null, publicProgress: storedPublicProgress(row.public_progress) };
}

async function leaderboard(user, env, period, now) {
  if (!['daily', 'weekly', 'total'].includes(period)) throw new ApiError(400, '排行周期无效');
  const range = bounds(period, now);
  const { rows, own } = await env.STORE.rankings(user.user_id, period === 'total' ? null : range, range.day);
  const entries=rows.map(rankingRow), self=own ? rankingRow(own) : { ...rankingRow(user),rank:null,count:0 };
  const socialAvailable=await rankingSocial(env.STORE,user.user_id,[...entries,self],period,now);
  return { period, date: range.day, timezone: 'Asia/Shanghai', startDate: period === 'total' ? null : range.start,
    endDate: period === 'total' ? null : range.end, entries, isAdmin: Boolean(user.is_admin), rewardPolicy: REWARD_POLICY,
    self, socialAvailable, socialProtocol:1, notice: NOTICE };
}

function event(item, now) {
  const fields = ['eventId', 'problemKey', 'acceptedAt', 'difficulty', 'scope'];
  if (!item || typeof item !== 'object' || Array.isArray(item) || Object.keys(item).some(key => !fields.includes(key)) ||
      !hashPattern.test(item.eventId || '') || !hashPattern.test(item.problemKey || '') || item.scope !== 'official') throw new ApiError(400, '通过记录字段无效');
  if (typeof item.acceptedAt !== 'string' || item.acceptedAt.length > 40 || !/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(item.acceptedAt)) throw new ApiError(400, '通过时间无效');
  const time = Date.parse(item.acceptedAt);
  if (!Number.isFinite(time) || time < Date.parse('2000-01-01T00:00:00Z') || time > now + 5 * 60 * 1000) throw new ApiError(400, '通过时间超出有效范围');
  if (item.difficulty != null && (typeof item.difficulty !== 'number' || !Number.isFinite(item.difficulty) || item.difficulty < 0 || item.difficulty > 5000)) throw new ApiError(400, '题目难度无效');
  return { ...item, acceptedAt: new Date(time).toISOString(), day: bounds('daily', time).day };
}

export async function handle(request, env) {
  try {
    if (!env.STORE) throw new ApiError(503, '排行榜数据库尚未配置');
    const url = new URL(request.url), path = url.pathname.replace(/\/$/, '');
    if (env.READ_ONLY === '1' && !['GET', 'HEAD'].includes(request.method)) {
      return json({ error: '排行榜正在迁移，请稍后重试' }, 503, { 'Retry-After': '60' });
    }
    const now = env.TEST_NOW == null ? Date.now() : Number(env.TEST_NOW);
    const timestamp = new Date(now).toISOString();
    if (path === '/v1/health' && request.method === 'GET') {
      await env.STORE.health();
      return json({ ok: true, version: VERSION, eventScope: 'official', accountStateProtocol: 1, accountChunkProtocol:env.STORE.chunks&&await env.STORE.chunks.available()?2:0, singleSession: true, publicProgressProtocol: 1, publicAppearanceProtocol: 1, nicknameUnique: true, stateResumeProtocol: 1, socialProtocol:env.STORE.social && await env.STORE.social.available() ? 1 : 0, trainingListLikesProtocol:env.STORE.social && await env.STORE.social.listAvailable() ? 1 : 0 });
    }
    if (path === '/v1/profile/register') throw new ApiError(410, '请升级 TB 并注册账号后登录');
    if (['/v1/accounts/register', '/v1/accounts/login'].includes(path) && request.method === 'POST') {
      const registering = path.endsWith('/register');
      const value = await body(request, registering ? ['loginId', 'nickname', 'password'] : ['loginId', 'password']);
      const login = loginId(value.loginId), secret = password(value.password);
      const ipHash = await digest((env.RATE_LIMIT_SALT || 'tb-ranking-registration') + ':' + (request.headers.get('X-TB-Client-IP') || 'unknown'));
      const seconds = Math.floor(now / 1000);
      if (registering) {
        await limit(env, 'register-minute:' + ipHash, 10, 60, seconds);
        await limit(env, 'register-day:' + ipHash, Math.min(1000, Math.max(1, Number(env.REGISTRATIONS_PER_IP_DAY) || 100)), 86400, seconds);
        let legacy = null;
        if (request.headers.has('Authorization') || request.headers.has('X-TB-User')) {
          const auth = credentials(request), existing = await env.STORE.findUser(auth.userId);
          if (existing) {
            if (!equalHash(existing.token_hash, tokenHash(auth.token))) throw new ApiError(401, '旧身份已关联账号或验证失败，请使用登录号登录');
            legacy = existing;
          } else legacy = { user_id: auth.userId, token_hash: null };
        }
        const account = await registerAccount(env.STORE, { ...value, loginId: login, nickname: nickname(value.nickname) }, legacy, timestamp);
        return json({ account }, 201);
      }
      await limit(env, 'login-ip:' + ipHash, 30, 60, seconds);
      await limit(env, 'login-account:' + await digest(login), 10, 60, seconds);
      const user = await env.STORE.findAccount(login);
      if (!await verifyPassword(secret, user?.password_hash)) throw new ApiError(401, '登录号或密码错误');
      if (request.headers.get('X-TB-State-Protocol') !== '1' && await env.STORE.stateRevision(user.user_id) > 0)
        throw new ApiError(426, '该账号已启用跨电脑同步，请升级 TB 至 1.0.20 或更新版本后登录');
      if(env.STORE.chunks&&await env.STORE.chunks.available()&&await env.STORE.chunks.active(user.user_id)&&request.headers.get('X-TB-Chunk-Protocol')!=='2')throw new ApiError(426,'此账号已使用分块同步，请升级客户端后登录');
      const issued = session(now);
      await env.STORE.createSession(user, issued, timestamp, request.headers.get('X-TB-State-Protocol') === '1',request.headers.get('X-TB-Chunk-Protocol')==='2');
      return json({ account: publicAccount(user), token: issued.token, expiresAt: issued.expiresAt });
    }
    const user = await authenticate(request, env, now);
    if(!path.startsWith('/v2/accounts/state'))await limit(env, 'user:' + user.user_id, Math.min(600, Math.max(10, Number(env.REQUESTS_PER_USER_MINUTE) || 120)), 60, Math.floor(now / 1000));
    if (path === '/v1/social' && request.method === 'GET') return json(await socialSnapshot(env.STORE,user,now));
    if(path==='/v1/training-list-likes' && request.method==='GET')return json(await trainingListLikes(env.STORE,user,null,url.searchParams.getAll('id'),false,now));
    if(path==='/v1/training-list-likes' && request.method==='POST') {
      const value=await body(request,['listId','liked'],1024);
      if(Object.hasOwn(value,'liked')&&typeof value.liked!=='boolean')throw new ApiError(400,'题单点赞格式无效');
      await limit(env,'training-list-like:'+user.user_id,60,60,Math.floor(now/1000));
      return json(await trainingListLikes(env.STORE,user,credentials(request).token,[value.listId],true,now,value.liked!==false));
    }
    if (['/v1/social/likes','/v1/social/comments','/v1/social/read'].includes(path) && request.method === 'POST') {
      const fields=path.endsWith('/likes') ? ['targetId'] : path.endsWith('/comments') ? ['targetId','text','requestId'] : ['ids','all'];
      const value=await body(request,fields,8192);
      await limit(env,'social:'+path+':'+user.user_id,path.endsWith('/comments')?10:60,60,Math.floor(now/1000));
      return json(await socialWrite(env.STORE,user,credentials(request).token,path,value,now));
    }
    if (path === '/v1/accounts/me' && request.method === 'GET') {
      if (env.READ_ONLY !== '1') await env.STORE.recordLogin(user.user_id, bounds('daily', now).day, timestamp);
      return json({ account: publicAccount(user), stateRevision: await env.STORE.stateRevision(user.user_id), singleSession: true });
    }
    if(path.startsWith('/v2/accounts/state')) {
      if(!env.STORE.chunks||!await env.STORE.chunks.available())throw new ApiError(404,'分块同步暂不可用');
      await limit(env,'chunk:'+user.user_id,2000,60,Math.floor(now/1000));
      const chunks=env.STORE.chunks,hash=tokenHash(credentials(request).token),seconds=Math.floor(now/1000);
      if(path==='/v2/accounts/state'&&request.method==='GET') {
        const cached=Number(request.headers.get('X-TB-State-Revision'))||null;
        return json(await chunks.head(user.user_id,cached));
      }
      if(path==='/v2/accounts/state/missing'&&request.method==='POST') {
        const value=await body(request,['hashes'],16384);
        return json({missing:await chunks.missing(user.user_id,validateHashes(value.hashes),timestamp)});
      }
      if(path==='/v2/accounts/state/objects'&&request.method==='POST') {
        const value=await body(request,['objects'],CHUNK_LIMIT,false);
        if(!Array.isArray(value.objects)||!value.objects.length||value.objects.length>64)throw new ApiError(400,'同步分块批次无效');
        const validated=value.objects.map(item=>{
          if(!item||typeof item!=='object'||Array.isArray(item))throw new ApiError(400,'同步分块批次无效');
          const {hash:identity,...content}=item;
          return {identity,value:validateChunk(identity,content)};
        });
        if(new Set(validated.map(item=>item.identity)).size!==validated.length)throw new ApiError(400,'同步分块批次重复');
        // Objects remain private and immutable. A failed batch is retry safe;
        // only the later root CAS publishes a complete account version.
        for(const item of validated)await chunks.put(user.user_id,hash,seconds,item.identity,item.value,timestamp);
        return json({uploaded:validated.map(item=>item.identity)});
      }
      if(path==='/v2/accounts/state'&&request.method==='PUT') {
        const value=await body(request,['revision','root'],1024);
        return json(await chunks.commit(user.user_id,hash,seconds,value.revision,value.root,timestamp));
      }
      const object=/^\/v2\/accounts\/state\/objects\/([a-f0-9]{64})$/.exec(path);
      if(object&&request.method==='GET')return json(await chunks.get(user.user_id,object[1]));
      if(object&&request.method==='PUT') {
        const value=validateChunk(object[1],await body(request,['kind','data','children'],CHUNK_LIMIT,false));
        return json(await chunks.put(user.user_id,hash,seconds,object[1],value,timestamp));
      }
      throw new ApiError(404,'没有找到这个同步接口');
    }
    if(path==='/v1/accounts/state'&&env.STORE.chunks&&await env.STORE.chunks.available()&&await env.STORE.chunks.active(user.user_id)) {
      // Older clients keep retrying a saved-session restore on 426 and hide
      // their login-screen updater. Expire only that local restore with 401;
      // never issue an old session or expose/write the retained v1 snapshot.
      const legacyRestore=request.method==='GET'&&request.headers.get('X-TB-Chunk-Protocol')!=='2';
      throw new ApiError(legacyRestore?401:426,'此版本需要更新，请等待登录页自动更新，或从 https://47.82.84.74/updates/stable/index.html 安装新版');
    }
    if (path === '/v1/accounts/state' && request.method === 'GET') {
      const cached = request.headers.get('X-TB-State-Revision');
      if (/^[1-9]\d{0,14}$/.test(cached || '')) {
        const revision = await env.STORE.stateRevision(user.user_id);
        if (revision === Number(cached)) return json({revision, unchanged:true});
      }
      return json(await env.STORE.accountState(user.user_id));
    }
    if (path === '/v1/accounts/state' && request.method === 'PUT') {
      const value = await body(request, ['revision', 'state'], STATE_LIMIT);
      if (!Number.isSafeInteger(value.revision) || value.revision < 0) throw new ApiError(400, '账号同步版本无效');
      validateState(value.state, user.user_id);
      return json(await env.STORE.saveAccountState(user.user_id, tokenHash(credentials(request).token), Math.floor(now / 1000), value.revision, value.state, timestamp));
    }
    if (path === '/v1/accounts/logout' && request.method === 'POST') {
      await body(request, []);
      await env.STORE.deleteSession(tokenHash(credentials(request).token));
      return json({ ok: true });
    }
    if (path === '/v1/accounts/password' && request.method === 'POST') {
      const value = await body(request, ['oldPassword', 'newPassword']);
      await limit(env, 'password:' + user.user_id, 5, 300, Math.floor(now / 1000));
      if (!await verifyPassword(password(value.oldPassword), user.password_hash)) throw new ApiError(400, '原密码错误');
      const next = password(value.newPassword);
      if (next === value.oldPassword) throw new ApiError(400, '新密码不能与原密码相同');
      const encoded = await hashPassword(next), issued = session(now);
      await env.STORE.changePassword(user, encoded, issued, timestamp);
      return json({ account: publicAccount(user), token: issued.token, expiresAt: issued.expiresAt });
    }
    if (env.READ_ONLY !== '1') await env.STORE.settleRewards(now);
    if (path === '/v1/profile' && request.method === 'GET') return json({ ...publicAccount(user), publicId: publicId(user.user_id), publicProgressProtocol: 1, publicAppearanceProtocol: 1,
      publicProgress: await env.STORE.publicProgress(user.user_id) });
    if (path === '/v1/rewards' && request.method === 'GET') return json(await env.STORE.rewards(user.user_id));
    if (path === '/v1/admin/leaderboard/delete' && request.method === 'POST') {
      if (!user.is_admin) throw new ApiError(403, '只有管理员可以删除排行榜成绩');
      const value = await body(request, ['userId', 'period', 'confirmation']);
      if (!['daily', 'weekly', 'total'].includes(value.period) || value.confirmation !== 'delete' ||
          value.userId !== null && !uuid.test(value.userId || '')) throw new ApiError(400, '删除范围或确认无效');
      if (value.userId && !await env.STORE.findUser(value.userId)) throw new ApiError(404, '用户不存在');
      return json(await env.STORE.removeRankings(user.user_id, value.userId, value.period,
        value.period === 'total' ? null : bounds(value.period, now), timestamp));
    }
    if (path === '/v1/profile' && request.method === 'PUT') {
      const value = await body(request, ['nickname', 'publicProgress', 'avatarData']);
      if (!Object.keys(value).length) throw new ApiError(400, '缺少要更新的资料');
      const name = Object.hasOwn(value, 'nickname') ? nickname(value.nickname) : null;
      const progress = Object.hasOwn(value, 'publicProgress') ? validatePublicProgress(value.publicProgress) : null;
      const avatar=Object.hasOwn(value,'avatarData')?validateAvatar(value.avatarData):undefined;
      await env.STORE.savePublicProfile(user.user_id, tokenHash(credentials(request).token), Math.floor(now / 1000), name, progress, timestamp, avatar);
      return json({ userId: user.user_id, publicId: publicId(user.user_id), nickname: name ?? user.nickname,
        displayName: name ?? user.nickname, ...(avatar!==undefined?{avatarHash:avatar.hash}:{}), ...(progress ? { publicProgress: progress } : {}) });
    }
    if (path.startsWith('/v1/avatars/') && request.method === 'GET') {
      const id=path.slice('/v1/avatars/'.length);
      if(!uuid.test(id))throw new ApiError(400,'用户编号无效');
      const avatar=await env.STORE.publicAvatar(id);
      return json({avatarData:avatar.data,avatarHash:avatar.hash});
    }
    if (path === '/v1/events' && request.method === 'POST') {
      const value = await body(request, ['events']);
      if (!Array.isArray(value.events) || value.events.length < 1 || value.events.length > 100) throw new ApiError(400, '每次须提交 1–100 条通过记录');
      const events = value.events.map(item => event(item, now));
      await env.STORE.recordEvents(user.user_id, events, timestamp);
      return json({ processed: events.length, scope: 'official', notice: NOTICE });
    }
    if (path === '/v1/leaderboard' && request.method === 'GET') return json(await leaderboard(user, env, url.searchParams.get('period') || 'daily', now));
    throw new ApiError(404, '没有找到这个接口');
  } catch (error) {
    if (error instanceof EventConflict) return json({ error: '通过记录编号与原题不匹配' }, 409);
    if (error instanceof ApiError || error instanceof AccountError) return json({ error: error.message }, error.status, error.status === 429 ? { 'Retry-After': '60' } : {});
    // Do not log tokens, metadata bodies or SQL with bound parameters.
    return json({ error: '排行榜服务暂时无法完成请求' }, 503);
  }
}
