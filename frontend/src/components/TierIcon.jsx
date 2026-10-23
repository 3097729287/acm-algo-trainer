import MedalEmblem from './MedalEmblem.jsx';
import './TierIcon.css';
import {rankIndex} from '@/lib/rankTiers.js';
export {TIER_NAMES} from '@/lib/rankTiers.js';
export default function TierIcon({badge='tier-0',tier,size=24}) {
  return <MedalEmblem index={rankIndex({badge,tier})} size={size}/>;
}
