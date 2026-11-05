import {acceptGrowth, confirmedGrowth} from './levelNotices.js';
import {rankIndex, TIER_NAMES} from './rankTiers.js';

const tier = value => Number.isInteger(value) && value >= 0 && value < TIER_NAMES.length;
const serial = value => Number.isSafeInteger(value) && value >= 0;
const score = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
export const rankPromotionKey = owner => `tb.rank-promotion.v1.${owner}`;
export const emptyRankPromotion = owner => ({version: 1, owner, initialized: false, rank: null, serial: 0, pending: null, authority: null});

// A display receipt only: this cache never assigns a tier, score or reward.
export function restoreRankPromotion(value, owner) {
  const empty = emptyRankPromotion(owner);
  if (!owner || value?.version !== 1 || value.owner !== owner || value.initialized !== true ||
      !(value.rank === null || tier(value.rank)) || !serial(value.serial)) return empty;
  const pending = value.pending;
  const validPending = pending && serial(pending.id) && pending.id > 0 && pending.id <= value.serial &&
    (pending.from === null || tier(pending.from)) && tier(pending.to) && pending.to === value.rank &&
    (pending.from === null || pending.from < pending.to) && score(pending.score);
  return {...empty, initialized: true, rank: value.rank, serial: value.serial,
    pending: validPending ? {id: pending.id, from: pending.from, to: pending.to, score: pending.score} : null};
}

export function observeRankPromotion(state, growth, owner) {
  if (!owner || !confirmedGrowth(growth, owner)) return state;
  const rank = growth.ranked;
  if (!rank || typeof rank.qualified !== 'boolean') return state;
  const ability = rank.abilityScore ?? rank.score;
  if (rank.qualified && (!score(ability) || growth.rankedEligible === false || growth.level < (rank.levelGate ?? 5))) return state;
  const authority = acceptGrowth(state?.owner === owner ? state.authority : null, growth, owner);
  if (!authority) return state;
  const previous = state?.owner === owner ? state : emptyRankPromotion(owner);
  const current = rank.qualified ? rankIndex(rank) : null;
  if (!previous.initialized) return {...previous, initialized: true, rank: current, authority};
  let pending = previous.pending, nextSerial = previous.serial;
  if (current === null || previous.rank !== null && current < previous.rank) pending = null;
  else if (current !== null && (previous.rank === null || current > previous.rank)) {
    pending = {id: ++nextSerial, from: pending ? pending.from : previous.rank, to: current, score: ability};
  } else if (pending) pending = {...pending, score: ability};
  return {...previous, rank: current, authority, serial: nextSerial, pending};
}

export function acknowledgeRankPromotion(state, id) {
  return state.pending?.id === id ? {...state, pending: null} : state;
}
