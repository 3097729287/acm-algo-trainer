import assert from 'node:assert/strict';
import {availablePages,pageAvailable,hiddenPages} from '../src/lib/navigationVisibility.js';
assert.deepEqual(availablePages(1),['mine','training-lists','records','settings']);
assert(!pageAvailable('mock',2));assert(pageAvailable('mock',3));
assert(pageAvailable('growth',5));assert(pageAvailable('rankings',2));
assert.deepEqual(hiddenPages(['mine','records','settings','library','library','bad']),['library']);
assert(!pageAvailable('training-lists',11,{hiddenNavPages:['training-lists']}));
await import('./next-actions-model.mjs');
console.log('PASS navigation levels, protected pages and complete learning recommendation scenarios');
