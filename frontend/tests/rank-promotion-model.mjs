import assert from 'node:assert/strict';
import {emptyRankPromotion, restoreRankPromotion, observeRankPromotion, acknowledgeRankPromotion} from '../src/lib/rankPromotions.js';
const owner = 'rank-fixture', scores = [200, 850, 1000, 1150, 1300, 1450, 1650, 1850, 2050];
const growth = (index, revision, options = {}) => ({level: 11, confirmed: true, rankedEligible: true,
  authority: {owner: options.owner ?? owner, epoch: options.epoch ?? 'first', revision},
  ranked: {qualified: index !== null, abilityScore: index === null ? 0 : scores[index], badge: `tier-${index}`, levelGate: 5}, ...options.growth});
let state = observeRankPromotion(emptyRankPromotion(owner), growth(3, 1), owner);
assert.equal(state.rank, 3); assert.equal(state.pending, null, 'Existing accounts do not replay historical promotions');
state = observeRankPromotion(state, growth(3, 2, {growth: {...growth(3, 2), level: 12}}), owner);
assert.equal(state.pending, null, 'An XP level increase is not a skill-tier promotion');
state = observeRankPromotion(state, {...growth(3, 3), ranked: {...growth(3, 3).ranked, abilityScore: 1190}}, owner);
assert.equal(state.pending, null, 'Score changes within one tier stay silent');
state = observeRankPromotion(state, growth(4, 4), owner);
assert.deepEqual(state.pending, {id: 1, from: 3, to: 4, score: scores[4]});
const pending = state;
for (const value of [growth(8, 3), growth(8, 4), growth(8, 10, {owner: 'another'}),
  {...growth(8, 10), confirmed: false}, {...growth(8, 10), ranked: {qualified: true, abilityScore: NaN}},
  {...growth(8, 10), rankedEligible: false}, {...growth(8, 10), level: 2}, {...growth(8, 10), ranked: null}]) {
  assert.equal(observeRankPromotion(pending, value, owner), pending, 'Unconfirmed, stale and cross-account snapshots are ignored');
}
state = observeRankPromotion(state, growth(6, 5), owner);
assert.deepEqual(state.pending, {id: 2, from: 3, to: 6, score: scores[6]}, 'Deferred multi-tier promotions merge');
assert.equal(acknowledgeRankPromotion(state, 1), state, 'An older visible animation cannot acknowledge a newer event');
state = acknowledgeRankPromotion(state, 2); assert.equal(state.pending, null);
assert.equal(observeRankPromotion(state, growth(6, 5), owner), state);
state = observeRankPromotion(state, growth(6, 6), owner); assert.equal(state.pending, null);
state = observeRankPromotion(state, growth(5, 7), owner); assert.equal(state.rank, 5); assert.equal(state.pending, null);
state = observeRankPromotion(state, growth(6, 8), owner); assert.equal(state.pending.from, 5); assert.equal(state.pending.to, 6);
state = observeRankPromotion(state, growth(4, 9), owner); assert.equal(state.pending, null, 'A superseded higher rank must not be announced');
state = observeRankPromotion(state, growth(5, 1, {epoch: 'restart'}), owner); assert.equal(state.pending.to, 5);
assert.equal(observeRankPromotion(state, growth(8, 99), owner), state, 'Retired server epochs cannot resurrect stale promotions');
const restored = restoreRankPromotion(JSON.parse(JSON.stringify(state)), owner);
assert.deepEqual(restored.pending, state.pending); assert.equal(restored.authority, null, 'Reload needs a fresh server confirmation');
assert.equal(restoreRankPromotion(state, 'another').initialized, false);
for (const bad of [null, {}, {...state, version: 2}, {...state, rank: 99}, {...state, serial: -1}])
  assert.equal(restoreRankPromotion(bad, owner).initialized, false);
assert.equal(restoreRankPromotion({...state, pending: {...state.pending, to: 8}}, owner).pending, null);
let placement = observeRankPromotion(emptyRankPromotion(owner), growth(null, 1), owner);
placement = observeRankPromotion(placement, growth(0, 2), owner);
assert.deepEqual(placement.pending, {id: 1, from: null, to: 0, score: scores[0]}, 'Completing initial placement is a real rank reveal');
for (let index = 1; index < 9; index++) {
  let pair = observeRankPromotion(emptyRankPromotion(owner), growth(index - 1, 1), owner);
  pair = observeRankPromotion(pair, growth(index, 2), owner);
  assert.equal(pair.pending.from, index - 1); assert.equal(pair.pending.to, index);
}
console.log(JSON.stringify({ok: true, noHistoricalReplay: true, realTierChanges: true, placement: true, allEightPromotions: true,
  noXpOrWithinTierAnimation: true, coalescing: true, ownerRevisionEpochGuards: true, reloadNeedsConfirmation: true, downgradeInvalidates: true}));
