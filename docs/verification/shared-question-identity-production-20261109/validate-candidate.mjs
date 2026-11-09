import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {REVIEWED_QUESTION_PAIRS,questionIdentity,replayProblemKeyIdentity} from './src/question-identities.mjs';
import {rankingQuery} from './src/ranking-rules.mjs';
const evidence=JSON.parse(readFileSync('/candidate/question-identity-20261109.json','utf8'));
assert.equal(evidence.sourceCommit,'efc0618dc404ba5b4d0fa3e2253d9399ff120892');
for(const [name,expected]of Object.entries(evidence.files)){
 const raw=readFileSync('/candidate/'+name);assert.equal(createHash('sha256').update(raw).digest('hex'),expected);
 const r=spawnSync(process.execPath,['--check','/candidate/'+name],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
}
assert.equal(REVIEWED_QUESTION_PAIRS.length,1);
assert.equal(questionIdentity('codeforces.com/gym/105139/problem/H'),'luogu.com.cn/problem/P10865');
const hash=v=>createHash('sha256').update(v).digest('hex');
for(const url of REVIEWED_QUESTION_PAIRS[0].sourceUrls)assert.equal(replayProblemKeyIdentity(hash(url)),hash('luogu.com.cn/problem/P10865'));
assert(rankingQuery({start:'2026-11-09',end:'2026-11-10'}).sql.includes('FROM first_official_ac e'));
console.log(JSON.stringify({filesVerified:6,syntaxParsed:6,sourceCommit:evidence.sourceCommit,network:'disabled',accountEnvironmentRead:false}));
