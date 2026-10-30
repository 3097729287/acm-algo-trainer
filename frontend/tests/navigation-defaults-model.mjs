import assert from 'node:assert/strict';
import {NAVIGATION_ORDER,navigationOrder} from '../src/lib/navigationDefaults.js';

assert.deepEqual(NAVIGATION_ORDER,['mine','library','training-lists','competitions','mock','growth','records','activity','rankings','paths','templates','lectures']);
for(const value of [undefined,null,[],['today']])assert.deepEqual(navigationOrder(value,2),NAVIGATION_ORDER);
for(const legacy of [
 ['training-lists'],
 ['mine','library','training-lists','competitions','mock','rankings','growth','records','paths','templates','lectures','activity'],
 ['mine','library','training-lists','competitions','mock','paths','rankings','growth','records','activity','lectures'],
 ['mine','library','training-lists','competitions','mock','paths','rankings','growth','records','activity','lectures','templates'],
 ['mine','library','training-lists','competitions','mock','records','growth','activity','lectures','templates','paths','rankings'],
]){const before=[...legacy];assert.deepEqual(navigationOrder(legacy,2),NAVIGATION_ORDER);assert.deepEqual(legacy,before);}
const custom=['templates','mine','library','training-lists','growth','paths'];
assert.deepEqual(navigationOrder(custom,2),custom);
assert.deepEqual(navigationOrder(custom,undefined),custom);
assert.deepEqual(navigationOrder(['paths','library','mine'],2),['paths','library','training-lists','mine']);
assert.deepEqual(navigationOrder([...NAVIGATION_ORDER],2),NAVIGATION_ORDER);
assert.deepEqual(navigationOrder(navigationOrder(custom,2),2),custom);
assert.deepEqual(navigationOrder(navigationOrder(undefined,2),2),NAVIGATION_ORDER);
console.log('Navigation defaults: explicit order, five shipped migrations, reset, custom preservation and idempotence PASS');
