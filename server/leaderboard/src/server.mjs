import { createServer } from 'node:http';
import { isIP } from 'node:net';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { once } from 'node:events';
import { handle } from './api.mjs';
import { openStore, secret } from './mysql-store.mjs';

export function createApiServer(env, { trustProxy = false } = {}) {
  const server = createServer(async (request, response) => {
    try {
      // Only the Docker-internal Caddy proxy may supply the real client address.
      // Replace the internal client-address header supplied by public callers.
      const headers = new Headers();
      for (const [name, value] of Object.entries(request.headers)) {
        if (value != null && name !== 'x-tb-client-ip') headers.set(name, Array.isArray(value) ? value.join(', ') : value);
      }
      const forwarded = request.headers['x-forwarded-for'];
      const candidate = typeof forwarded === 'string' ? forwarded.split(',').at(-1).trim() : '';
      const address = trustProxy && isIP(candidate) ? candidate : request.socket.remoteAddress || 'unknown';
      headers.set('X-TB-Client-IP', address);
      const length = Number(headers.get('content-length') || 0);
      if (!Number.isFinite(length) || length > 65536) {
        response.writeHead(413, { 'Content-Type': 'application/json', Connection: 'close' });
        response.end(JSON.stringify({ error: '请求不能超过 64 KB' }));
        return;
      }
      const chunks = []; let size = 0;
      for await (const chunk of request) {
        size += chunk.length;
        if (size > 65536) {
          response.writeHead(413, { 'Content-Type': 'application/json', Connection: 'close' });
          response.end(JSON.stringify({ error: '请求不能超过 64 KB' }));
          return;
        }
        chunks.push(chunk);
      }
      const init = { method: request.method, headers };
      if (!['GET', 'HEAD'].includes(request.method)) init.body = Buffer.concat(chunks);
      const result = await handle(new Request('http://localhost' + request.url, init), env);
      response.writeHead(result.status, Object.fromEntries(result.headers));
      response.end(Buffer.from(await result.arrayBuffer()));
    } catch {
      if (!response.headersSent) response.writeHead(503, { 'Content-Type': 'application/json' });
      response.end(JSON.stringify({ error: '排行榜服务暂时无法完成请求' }));
    }
  });
  server.requestTimeout = 15000;
  server.headersTimeout = 10000;
  server.setTimeout(15000, socket => socket.destroy());
  return server;
}

export async function start(env = process.env) {
  const STORE = await openStore(env);
  let server;
  try {
    await STORE.health();
    if (env.READ_ONLY !== '1') await STORE.settleRewards(Date.now());
    const apiEnv = { STORE, RATE_LIMIT_SALT: await secret(env, 'RATE_LIMIT_SALT'),
      READ_ONLY: env.READ_ONLY,
      REGISTRATIONS_PER_IP_DAY: env.REGISTRATIONS_PER_IP_DAY, REQUESTS_PER_USER_MINUTE: env.REQUESTS_PER_USER_MINUTE };
    if (!apiEnv.RATE_LIMIT_SALT) throw new Error('RATE_LIMIT_SALT is required');
    server = createApiServer(apiEnv, { trustProxy: env.TRUST_PROXY === '1' });
    server.listen(Number(env.PORT || 8080), env.HOST || '0.0.0.0');
    await once(server, 'listening');
  } catch (error) {
    if (server?.listening) await new Promise(resolveClose => server.close(resolveClose));
    await STORE.close();
    throw error;
  }
  const cleanup = setInterval(() => STORE.cleanup(Math.floor(Date.now() / 1000)).catch(() => {
    process.stderr.write('Rate-limit cleanup failed\n');
  }), 60 * 60 * 1000);
  cleanup.unref();
  // The shared service settles at Beijing midnight even when clients are closed.
  // Database cursors catch up completed cycles after downtime without duplicate XP.
  let closing = false;
  let rewards;
  const scheduleRewards = (retry = false) => {
    if (closing) return;
    const delay = retry ? 60000 : 86400000 - (Date.now() + 8 * 3600 * 1000) % 86400000;
    rewards = setTimeout(async () => {
      try {
        if (env.READ_ONLY !== '1') await STORE.settleRewards(Date.now());
        scheduleRewards();
      } catch {
        process.stderr.write('Ranking reward settlement failed\n');
        scheduleRewards(true);
      }
    }, delay);
    rewards.unref();
  };
  scheduleRewards();
  const close = async () => {
    if (closing) return;
    closing = true;
    clearInterval(cleanup);
    clearTimeout(rewards);
    await new Promise(resolveClose => server.close(resolveClose));
    await STORE.close();
  };
  process.stdout.write(`TB leaderboard listening on port ${server.address().port}\n`);
  return { server, STORE, close };
}

if (process.argv[1] && fileURLToPath(import.meta.url).toLowerCase() === resolve(process.argv[1]).toLowerCase()) {
  try {
    const instance = await start();
    for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => instance.close().catch(() => { process.exitCode = 1; }));
  } catch {
    // Drivers include SQL and connection details in errors; keep them out of logs.
    process.stderr.write('TB leaderboard startup failed; check database availability and secret files\n');
    process.exitCode = 1;
  }
}
