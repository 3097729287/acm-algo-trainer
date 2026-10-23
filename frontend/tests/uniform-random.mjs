import assert from 'node:assert/strict';
import {uniformIndex} from '../src/lib/uniformRandom.js';
let samples=[0xffffffff,5],reads=0;
const crypto={getRandomValues(array){array[0]=samples.shift();reads++;return array;}};
assert.equal(uniformIndex(3,crypto),2);assert.equal(reads,2,'reject the incomplete high bucket before applying modulo');
for(let ticket=0;ticket<12;ticket++)assert.equal(uniformIndex(3,{getRandomValues(array){array[0]=ticket;return array;}}),ticket%3);
for(const count of [1,2,120,5811])assert.equal(uniformIndex(count,{getRandomValues(array){array[0]=count-1;return array;}}),count-1);
assert.throws(()=>uniformIndex(0),RangeError);assert.throws(()=>uniformIndex(5,{}),/随机数源/);
console.log('PASS: uniform random rejection sampling, all ticket positions, whole-catalogue sizes and invalid input.');
