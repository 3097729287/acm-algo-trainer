import RULES from '../../../backend/resources/rank-tiers.json' with {type:'json'};
export const TIER_NAMES=RULES.tiers.map(tier=>tier.name);
export const RANK_THRESHOLDS=RULES.tiers.map(tier=>tier.minimum);

export function rankIndex(rank={}) {
 // Current score maps through the same rules as the backend. This also keeps
 // old public snapshots consistent until their owners next synchronize.
 const score=rank.abilityScore??rank.rankScore;
 if(rank.qualified!==false&&typeof score==='number'&&Number.isFinite(score))return Math.max(0,RANK_THRESHOLDS.findLastIndex(value=>score>=value));
 const name=typeof rank==='string'?rank:rank.rankTier||rank.tier;
 const named=TIER_NAMES.indexOf(name);
 if(named>=0)return named;
 // Old public snapshots remain readable without rewriting anyone's history.
 if(name==='铂金')return 3;
 const badge=Number(String(rank.badge||'').replace('tier-',''));
 return Number.isFinite(badge)?Math.max(0,Math.min(8,Math.floor(badge))):0;
}
