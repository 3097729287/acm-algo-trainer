import { Shield, ShieldCheck, Star, Crown, Gem, Leaf, Diamond, Flame, Swords, Trophy } from 'lucide-react';
import './TierIcon.css';

const icons = [Shield, ShieldCheck, Star, Crown, Gem, Leaf, Diamond, Flame, Swords, Trophy];
export const TIER_NAMES = ['黑铁', '青铜', '白银', '黄金', '铂金', '翡翠', '钻石', '大师', '宗师', '王者'];
export default function TierIcon({ badge = 'tier-0', size = 22 }) {
  const index = Number(String(badge).replace('tier-', ''));
  const Icon = icons[index] || Shield;
  return <Icon size={size} aria-hidden="true" />;
}
