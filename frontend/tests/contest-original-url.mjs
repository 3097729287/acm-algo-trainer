import assert from 'node:assert/strict';
import {contestOriginalUrl} from '../src/lib/contestOriginalUrl.js';
for(const [row,expected] of [
 [{url:'https://codeforces.com/contest/2218/problem/D'},'https://codeforces.com/contest/2218'],
 [{url:'https://m1.codeforces.com/gym/726517/problem/B?locale=en'},'https://codeforces.com/gym/726517'],
 [{url:'https://codeforces.com/problemset/problem/2218/D'},'https://codeforces.com/contest/2218'],
 [{url:'https://atcoder.jp/contests/arc225/tasks/arc225_a'},'https://atcoder.jp/contests/arc225'],
 [{url:'https://ac.nowcoder.com/acm/contest/125954/C'},'https://ac.nowcoder.com/acm/contest/125954'],
 [{url:'https://www.luogu.com.cn/problem/P17590',collectionSource:'https://www.luogu.com.cn/contest/334135'},'https://www.luogu.com.cn/contest/334135'],
 [{url:'https://www.luogu.com.cn/problem/P17790',contestId:'366453'},'https://www.luogu.com.cn/contest/366453'],
 [{url:'https://qoj.ac/problem/15032',contestId:'2693'},'https://qoj.ac/contest/2693'],
 [{url:'https://qoj.ac/contest/2693/problem/15032'},'https://qoj.ac/contest/2693'],
 [{url:'https://unknown.example/problem/A',contestUrl:'https://unknown.example/event/5'},'https://unknown.example/event/5'],
])assert.equal(contestOriginalUrl([row]),expected);
for(const row of [{},{url:'https://www.luogu.com.cn/problem/P17590'},{url:'https://qoj.ac/problem/15032'},{contestUrl:'javascript:alert(1)'},{contestUrl:'file:///C:/private'},{contestUrl:'https://user:pass@example.com/contest/1'}])assert.equal(contestOriginalUrl([row]),null,'Do not invent a contest URL from an unsupported problem address');
assert.equal(contestOriginalUrl([{}, {url:'https://codeforces.com/gym/726517/problem/B'}]),'https://codeforces.com/gym/726517');
console.log('PASS original contest provenance for five platforms, gym and problemset aliases, incomplete metadata and unavailable sources');
