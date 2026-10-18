import mysql from 'mysql2/promise';
import { readFile } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { listenFixture } from './listen.mjs';
import { MySQLStore } from '../src/mysql-store.mjs';
import { createApiServer } from '../src/server.mjs';

export async function startMySQLFixture({ now } = {}) {
  if (!process.env.TB_MYSQL_TEST_PORT) throw new Error('Set TB_MYSQL_TEST_PORT to an isolated MySQL test server');
  const options = { host: '127.0.0.1', port: Number(process.env.TB_MYSQL_TEST_PORT),
    user: 'root', password: process.env.TB_MYSQL_TEST_PASSWORD || '', charset: 'utf8mb4' };
  const admin = await mysql.createConnection(options);
  const database = 'tb_test_' + randomUUID().replaceAll('-', '');
  let STORE, server;
  try {
    await admin.query(`CREATE DATABASE ${database} CHARACTER SET utf8mb4 COLLATE utf8mb4_bin`);
    const pool = mysql.createPool({ ...options, database, connectionLimit: 10 });
    STORE = new MySQLStore(pool);
    const schema = (await Promise.all(['001_schema.sql', '002_official_ac.sql', '003_ranking_rewards_admin.sql', '004_accounts.sql', '005_account_state.sql', '006_public_progress.sql', '007_unique_nicknames.sql'].map(name => readFile(new URL('../mysql/' + name, import.meta.url), 'utf8')))).join('\n');
    for (const sql of schema.split(';').map(value => value.trim()).filter(Boolean)) await pool.query(sql);
    const env = { STORE, RATE_LIMIT_SALT: 'isolated-test-salt', ...(now ? { TEST_NOW: now } : {}) };
    server = createApiServer(env);
    await listenFixture(server);
    return { server, STORE, env, endpoint: `http://127.0.0.1:${server.address().port}`,
      async countEvents() { const [rows] = await pool.query('SELECT COUNT(*) AS n FROM official_ac_events'); return Number(rows[0].n); },
      async close() {
        await new Promise(resolve => server.close(resolve));
        await STORE.close();
        await admin.query(`DROP DATABASE ${database}`);
        await admin.end();
      } };
  } catch (error) {
    server?.close();
    if (STORE) await STORE.close();
    await admin.query(`DROP DATABASE IF EXISTS ${database}`);
    await admin.end();
    throw error;
  }
}
