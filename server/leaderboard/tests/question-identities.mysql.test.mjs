import assert from 'node:assert/strict';
import path from 'node:path';
import mysql from 'mysql2/promise';
import {startGameplayFixture} from './gameplay-fixture.mjs';
import {questionIdentitiesSuite} from './question-identities-suite.mjs';

async function verifiedFixture(options){
  assert.equal(process.env.TB_GAMEPLAY_MYSQL,'1','Explicit disposable MySQL mode required');
  assert(process.env.TB_MYSQL_TEST_PORT&&process.env.TB_MYSQL_TEST_DATADIR,'Explicit owned datadir/loopback port required');
  const db=await mysql.createConnection({host:'127.0.0.1',port:Number(process.env.TB_MYSQL_TEST_PORT),user:'root',password:process.env.TB_MYSQL_TEST_PASSWORD||''});
  try{
    const [[actual]]=await db.query('SELECT @@datadir AS datadir');
    assert.equal(path.resolve(actual.datadir).toLowerCase(),path.resolve(process.env.TB_MYSQL_TEST_DATADIR).toLowerCase(),'Refuse any MySQL instance outside the owned temporary datadir');
  }finally{await db.end();}
  return startGameplayFixture(options);
}
questionIdentitiesSuite(verifiedFixture);
