import { EventConflict } from './errors.mjs';
import { bounds, REWARD_POLICY } from './ranking-rules.mjs';
import { AccountError, loginId, password, verifyPassword, hashPassword, tokenHash,
  session, publicAccount, registerAccount } from './accounts.mjs';

const VERSION = '0.10.4';
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

async function body(request, allowed) {
  if (!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')) throw new ApiError(415, '请求须使用 application/json');
  const declared = Number(request.headers.get('Content-Length') || 0);
  if (!Number.isFinite(declared) || declared > 65536) throw new ApiError(413, '请求不能超过 64 KB');
  if (!request.body) throw new ApiError(400, '缺少 JSON 请求');
  const reader = request.body.getReader();
  const chunks = []; let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > 65536) { await reader.cancel(); throw new ApiError(413, '请求不能超过 64 KB'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
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

async function authenticate(request, env, now) {
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
  return { rank: row.rank, userId: row.user_id, nickname: row.nickname, displayName: row.nickname, count: row.count };
}

async function leaderboard(user, env, period, now) {
  if (!['daily', 'weekly', 'total'].includes(period)) throw new ApiError(400, '排行周期无效');
  const range = bounds(period, now);
  const { rows, own } = await env.STORE.rankings(user.user_id, period === 'total' ? null : range);
  return { period, date: range.day, timezone: 'Asia/Shanghai', startDate: period === 'total' ? null : range.start,
    endDate: period === 'total' ? null : range.end, entries: rows.map(rankingRow), isAdmin: Boolean(user.is_admin), rewardPolicy: REWARD_POLICY,
    self: own ? rankingRow(own) : { rank: null, userId: user.user_id, nickname: user.nickname, displayName: user.nickname, count: 0 }, notice: NOTICE };
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
      return json({ ok: true, version: VERSION, eventScope: 'official' });
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
      const issued = session(now);
      await env.STORE.createSession(user, issued, timestamp);
      return json({ account: publicAccount(user), token: issued.token, expiresAt: issued.expiresAt });
    }
    const user = await authenticate(request, env, now);
    await limit(env, 'user:' + user.user_id, Math.min(600, Math.max(10, Number(env.REQUESTS_PER_USER_MINUTE) || 120)), 60, Math.floor(now / 1000));
    if (path === '/v1/accounts/me' && request.method === 'GET') return json({ account: publicAccount(user) });
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
    if (path === '/v1/profile' && request.method === 'GET') return json(publicAccount(user));
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
      const value = await body(request, ['nickname']), name = nickname(value.nickname);
      await env.STORE.updateNickname(user.user_id, name, timestamp);
      return json({ userId: user.user_id, nickname: name, displayName: name });
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
