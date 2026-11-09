import {createHash} from 'node:crypto';

// Reviewed exact cross-platform identity. This is a scoring projection only:
// never use it as a browser URL, a submission destination or a contest slot ID.
// The two source rows and all previously settled rewards remain unchanged.
// Evidence: content-updates/20261109-new-xcpc-hubei/source-review.json
// #existingEquivalentTasks, original PDF p.11, matching complete native mirror.
export const REVIEWED_QUESTION_PAIRS=Object.freeze([
  Object.freeze({key:'luogu.com.cn/problem/P10865',aliases:Object.freeze([
    'luogu.com.cn/problem/P10865','codeforces.com/gym/105139/problem/H',
  ]),sourceUrls:Object.freeze(['https://www.luogu.com.cn/problem/P10865','https://codeforces.com/gym/105139/problem/H'])}),
]);
const digest=value=>createHash('sha256').update(value).digest('hex');
const keys=new Map(),hashes=new Map();
for(const pair of REVIEWED_QUESTION_PAIRS)for(const alias of pair.aliases){keys.set(alias,pair.key);hashes.set(digest(alias),digest(pair.key));}
export const questionIdentity=key=>keys.get(key)||key;
export const problemKeyIdentity=key=>hashes.get(key)||key;
// Historical replay p: keys hash the original full URL, whereas global AC
// keys hash the canonical question key. Accept only these reviewed exact URLs.
const replayHashes=new Map(hashes);
for(const pair of REVIEWED_QUESTION_PAIRS)for(const url of pair.sourceUrls)replayHashes.set(digest(url),digest(pair.key));
export const replayProblemKeyIdentity=key=>replayHashes.get(key)||key;
const groups=REVIEWED_QUESTION_PAIRS.map(pair=>pair.aliases.map(key=>`'${digest(key)}'`).join(','));
const aliasHashes=[...hashes.keys()].map(key=>`'${key}'`).join(',');
const column=value=>{if(!/^[a-z][a-z0-9_]*\.problem_key$/.test(value))throw Error('Internal identity column required');return value;};
export function sameQuestionSQL(left,right){
  column(left);column(right);
  return `(${left}=${right} OR ${groups.map(group=>`(${left} IN (${group}) AND ${right} IN (${group}))`).join(' OR ')})`;
}
// Select a real original row BEFORE applying daily/weekly filters. Counting
// DISTINCT within the requested period would falsely make today's mirror AC
// a new question after an earlier acceptance on the other platform.
export function firstOfficialEventsCTE(){
  return `first_official_ac AS (
    SELECT e.* FROM official_ac_events e WHERE e.problem_key NOT IN (${aliasHashes})
    OR NOT EXISTS (SELECT 1 FROM official_ac_events earlier
      WHERE earlier.user_id=e.user_id AND ${sameQuestionSQL('earlier.problem_key','e.problem_key')} AND (
        earlier.accepted_at<e.accepted_at OR (earlier.accepted_at=e.accepted_at AND (
          earlier.received_at<e.received_at OR (earlier.received_at=e.received_at AND earlier.problem_key<e.problem_key)))))
  )`;
}
export function questionNotExcludedSQL(alias='e'){
  if(!/^[a-z][a-z0-9_]*$/.test(alias))throw Error('Internal identity alias required');
  return `NOT EXISTS (SELECT 1 FROM ranking_exclusions x WHERE x.user_id=${alias}.user_id AND ${sameQuestionSQL('x.problem_key',`${alias}.problem_key`)})`;
}
