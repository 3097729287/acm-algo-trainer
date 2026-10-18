import { Award } from 'lucide-react';

export default function TitleMedals({ titles = [], compact = false }) {
  const items = Array.isArray(titles) ? titles : [];
  if (!items.length) return null;
  return <span className={`title-medals${compact ? ' title-medals-compact' : ''}`} aria-label="已获得称号">{items.map(item => <span className={`title-medal title-medal-${item.category || 'ac'}`} key={item.id} title={`${item.category === 'streak' ? '连续训练' : 'AC'} ${Number(item.target).toLocaleString('zh-CN')} ${item.category === 'streak' ? '天' : '题'} · ${item.name}`}><Award size={compact ? 14 : 17} aria-hidden="true" /><span>{item.name}</span></span>)}</span>;
}
