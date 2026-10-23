import { LoaderCircle, LockKeyhole, UserRound } from 'lucide-react';
import AvatarFrame from './AvatarFrame.jsx';
import Tooltip from './Tooltip.jsx';
import TierIcon from './TierIcon.jsx';
import {rankIndex} from '@/lib/rankTiers.js';
import './ProfileBadge.css';

export const MAX_AVATAR_DATA_LENGTH = 48 * 1024;

export function isAvatarData(value) {
  return typeof value === 'string' && value.length <= MAX_AVATAR_DATA_LENGTH
    && /^data:image\/(?:png|jpeg|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(value);
}

function finite(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function number(value) {
  return Math.max(0, Math.round(finite(value))).toLocaleString('zh-CN');
}

/** XP belongs to the avatar ring; rank belongs to the separate skill emblem. */
export default function ProfileBadge({ growth, avatar, nickname, onClick, onAvatarClick, compact = true, showXp = true }) {
  const ready = Number.isFinite(growth?.level);
  const level = ready ? Math.max(1, Math.floor(growth.level)) : null;
  const rank = growth?.ranked;
  const unlockLevel = finite(rank?.levelGate ?? growth?.rankUnlockLevel ?? growth?.levelGate, 5);
  const unlocked = ready && level >= unlockLevel;
  const qualified = unlocked && Boolean(rank) && rank.qualified !== false;
  const badge = `tier-${qualified?rankIndex(rank):0}`;
  const currentXp = Math.max(0, finite(growth?.currentLevelXp));
  const nextXp = Math.max(0, finite(growth?.nextLevelXp));
  const maximumLevel = ready && nextXp === 0 && level >= finite(growth?.levelCap ?? growth?.maxLevel, 100);
  const progress = maximumLevel ? 100 : nextXp > 0 ? Math.min(100, currentXp / nextXp * 100) : 0;
  const capXp = Array.isArray(growth?.levelCosts)
    ? growth.levelCosts.reduce((sum, cost) => sum + Math.max(0, finite(cost)), 0)
    : Math.max(0, finite(growth?.totalXp ?? growth?.xp));
  const xpText = ready
    ? maximumLevel
      ? `经验值:${number(growth?.totalXp ?? growth?.xp)}/${number(capXp)} · 已达到最高等级`
      : `经验值:${number(currentXp)}/${number(nextXp)}`
    : '正在读取等级与经验值';
  const rankName = !unlocked ? `${number(unlockLevel)} 级解锁段位` : qualified ? rank.tier || '黑铁' : '定级中';
  const ability = rank?.abilityScore ?? rank?.score;
  const minimumEvidence = Math.max(1, finite(rank?.minimumEvidence, 5));
  const rankText = !unlocked ? rankName : qualified
    ? `${rankName} · 能力分 ${number(ability)}${rank?.nextAbilityScore != null ? ` · 下一段位 ${number(rank.nextAbilityScore)}` : ''}`
    : `定级中 · 独立通过 ${number(minimumEvidence)} 道已知难度的题目后评估段位${rank?.evidenceCount != null ? `（${number(rank.evidenceCount)}/${number(minimumEvidence)}）` : ''}`;
  const AvatarControl = onAvatarClick ? 'button' : 'span';
  const OverviewControl = onClick ? 'button' : 'span';
  const initials = Array.from(String(nickname || '').trim())[0]?.toLocaleUpperCase();
  const image = isAvatarData(avatar) ? avatar : null;

  return <div className={`profile-badge ${badge}${compact ? ' profile-badge-compact' : ''}${qualified ? '' : ' profile-badge-unplaced'}`}>
    <Tooltip text={showXp ? xpText : `等级 ${level ?? '—'} · ${rankName}`}>
      <AvatarControl className="profile-avatar-button" {...(onAvatarClick ? { type: 'button', onClick: onAvatarClick, 'aria-label': '设置头像' } : { tabIndex: 0, 'aria-label': `等级 ${level ?? '读取中'}` })}>
        {showXp && <svg className="profile-xp-ring" viewBox="0 0 44 44" role="meter" aria-label="本级经验进度" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress)} aria-valuetext={xpText}>
          <circle className="profile-xp-track" cx="22" cy="22" r="19.5" />
          <circle className="profile-xp-value" cx="22" cy="22" r="19.5" pathLength="100" strokeDasharray={`${progress} 100`} />
        </svg>}
        <AvatarFrame index={Number(badge.slice(5)) || 0}/>
        <span className="profile-avatar-face" aria-hidden="true">{image ? <img src={image} alt="" /> : <UserRound size={19} />}</span>
        <b className="profile-level-number" aria-hidden="true">{level ?? '—'}</b>
      </AvatarControl>
    </Tooltip>
    <Tooltip text={rankText}>
      <OverviewControl className="profile-overview" {...(onClick ? { type: 'button', onClick, 'aria-label': '训练概览', 'aria-haspopup': 'dialog', 'aria-busy': !ready } : { tabIndex: 0, 'aria-label': rankText })}>
        {nickname && <strong className="profile-nickname">{nickname}</strong>}

      </OverviewControl>
    </Tooltip>
  </div>;
}
