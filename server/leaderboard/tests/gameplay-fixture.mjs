import {readFile} from 'node:fs/promises';
import {startFixture as sqliteFixture} from './local-server.mjs';
import {startMySQLFixture} from './mysql-fixture.mjs';
import {preservedData,assertPreserved} from '../scripts/audit-preserved-data.mjs';
export async function migrateGameplay(fixture){
 const before=await preservedData(fixture.STORE.pool);
 for(const name of ['015_gameplay.sql','016_social_replies.sql']){
  const source=await readFile(new URL('../mysql/'+name,import.meta.url),'utf8');
  for(let repeat=0;repeat<2;repeat++)for(const statement of source.split(';').map(value=>value.trim()).filter(Boolean))await fixture.STORE.pool.query(statement);
 }
 assertPreserved(before,await preservedData(fixture.STORE.pool),{requireAvatar:true,requireChunks:true,requireLists:true,requireAdmin:true});
}
export async function startGameplayFixture(options){
 if(process.env.TB_GAMEPLAY_MYSQL!=='1')return sqliteFixture(options);
 const fixture=await startMySQLFixture(options);
 try{await migrateGameplay(fixture);return fixture;}catch(error){await fixture.close();throw error;}
}
