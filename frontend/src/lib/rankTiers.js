export const TIER_NAMES=['黑铁','青铜','白银','黄金','翡翠','钻石','大师','宗师','王者'];
export const RANK_THRESHOLDS=[0,800,1000,1200,1600,1800,2000,2100,2200];

export function rankIndex(rank={}) {
 const name=typeof rank==='string'?rank:rank.tier||rank.rankTier;
 const named=TIER_NAMES.indexOf(name);
 if(named>=0)return named;
 // Old public snapshots remain readable without rewriting anyone's history.
 if(name==='铂金')return 3;
 const score=rank.abilityScore??rank.rankScore;
 if(typeof score==='number'&&Number.isFinite(score))return Math.max(0,RANK_THRESHOLDS.findLastIndex(value=>score>=value));
 const badge=Number(String(rank.badge||'').replace('tier-',''));
 return Number.isFinite(badge)?Math.max(0,Math.min(8,Math.floor(badge))):0;
}
