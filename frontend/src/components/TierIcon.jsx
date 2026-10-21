import MedalEmblem from './MedalEmblem.jsx';
import './TierIcon.css';
export const TIER_NAMES = ['黑铁','青铜','白银','黄金','铂金','翡翠','钻石','大师','宗师','王者'];
export default function TierIcon({badge='tier-0',size=24}) {
  const index=Number(String(badge).replace('tier-',''));
  return <MedalEmblem index={Number.isFinite(index)?index:0} size={size}/>;
}
