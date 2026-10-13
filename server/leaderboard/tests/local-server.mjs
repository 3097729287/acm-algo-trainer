// Offline SQLite fixture using the same HTTP adapter as production.
import { listenFixture } from './listen.mjs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { createApiServer } from '../src/server.mjs';
import { SQLiteStore } from './sqlite-store.mjs';

export async function startFixture({ database = ':memory:', now } = {}) {
  const STORE = new SQLiteStore(database);
  const env = { STORE, RATE_LIMIT_SALT: 'test-only', ...(now ? { TEST_NOW: now } : {}) };
  const server = createApiServer(env);
  await listenFixture(server);
  return { server, STORE, env, endpoint: `http://127.0.0.1:${server.address().port}`,
    async countEvents() { return STORE.database.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n; },
    async close() { await new Promise(resolve => server.close(resolve)); await STORE.close(); } };
}

if (process.argv[1] && fileURLToPath(import.meta.url).toLowerCase() === resolve(process.argv[1]).toLowerCase()) {
  const fixture = await startFixture();
  process.stdout.write(JSON.stringify({ endpoint: fixture.endpoint }) + '\n');
  process.on('SIGTERM', async () => { await fixture.close(); process.exit(0); });
  process.on('SIGINT', async () => { await fixture.close(); process.exit(0); });
}
