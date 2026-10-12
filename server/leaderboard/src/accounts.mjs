import { randomBytes, randomUUID, scrypt, timingSafeEqual, createHash } from 'node:crypto';

export class AccountError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
export const tokenHash = value => createHash('sha256').update(value).digest('hex');
export const SESSION_SECONDS = 30 * 86400;
const options = { N: 16384, r: 8, p: 5, maxmem: 24 * 1024 * 1024 };
let active = 0;
const waiting = [];

// Two bounded native jobs fit the small production server. Passwords never
// enter a worker log, a database column or an application response.
async function derive(password, salt) {
  if (active >= 2) {
    if (waiting.length >= 16) throw new AccountError(429, '登录请求较多，请稍后重试');
    await new Promise(resolve => waiting.push(resolve));
  } else active++;
  try {
    return await new Promise((resolve, reject) => scrypt(password, salt, 32, options,
      (error, result) => error ? reject(error) : resolve(result)));
  } finally {
    const next = waiting.shift();
    if (next) next(); else active--;
  }
}

export function loginId(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9_]{4,32}$/.test(value))
    throw new AccountError(400, '登录号须为 4–32 位字母、数字或下划线');
  return value.toLowerCase();
}
export function password(value) {
  if (typeof value !== 'string' || [...value].length < 8 || [...value].length > 128 || Buffer.byteLength(value) > 512)
    throw new AccountError(400, '密码须为 8–128 个字符');
  return value;
}
export async function hashPassword(value) {
  const salt = randomBytes(16);
  const hash = await derive(value, salt);
  return `scrypt$16384$8$5$${salt.toString('hex')}$${hash.toString('hex')}`;
}
export async function verifyPassword(value, encoded) {
  const match = /^scrypt\$16384\$8\$5\$([a-f0-9]{32})\$([a-f0-9]{64})$/.exec(encoded || '');
  // Unknown login IDs do the same expensive work as known IDs.
  const salt = match ? Buffer.from(match[1], 'hex') : Buffer.alloc(16);
  const expected = match ? Buffer.from(match[2], 'hex') : Buffer.alloc(32);
  const actual = await derive(value, salt);
  return timingSafeEqual(actual, expected) && Boolean(match);
}
export function session(now) {
  const token = randomBytes(32).toString('base64url');
  return { token, hash: tokenHash(token), expiresAt: Math.floor(now / 1000) + SESSION_SECONDS };
}
export function publicAccount(user) {
  return { userId: user.user_id, loginId: user.login_id, nickname: user.nickname,
    displayName: user.nickname, createdAt: user.created_at, isAdmin: Boolean(user.is_admin) };
}
export async function registerAccount(store, value, legacy, timestamp) {
  const id = loginId(value.loginId), encoded = await hashPassword(password(value.password));
  const userId = legacy?.user_id || randomUUID();
  await store.createAccount({ userId, loginId: id, nickname: value.nickname,
    passwordHash: encoded, legacyHash: legacy?.token_hash || null,
    // Retire the old install token even for a newly created user.
    retiredHash: tokenHash(randomBytes(32)), timestamp });
  return publicAccount(await store.findAccount(id));
}
