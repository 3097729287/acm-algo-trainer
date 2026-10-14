import { Shield, ShieldCheck, Star, Crown, Gem, Leaf, Diamond, Flame, Swords, Trophy } from 'lucide-react';

const icons = [Shield, ShieldCheck, Star, Crown, Gem, Leaf, Diamond, Flame, Swords, Trophy];
export default function TierIcon({ badge = 'tier-0', size = 22 }) {
  const index = Number(String(badge).replace('tier-', ''));
  const Icon = icons[index] || Shield;
  return <Icon size={size} aria-hidden="true" />;
}
