"""Independent XP levels and evidence-based skill tiers.

The old ranked-points replay remains available under ``legacyPoints``. It is
never used to award a current skill tier or to rewrite a user's earned XP.
"""
from collections import defaultdict
import datetime as dt
import math
from progression import SHANGHAI, parse_time

TIERS = ('黑铁', '青铜', '白银', '黄金', '翡翠', '钻石', '大师', '宗师', '王者')
TITLES = ('编程入门', '基础研习', '算法实践', '结构分析', '构造与证明', '复杂度掌控', '算法设计', '竞赛研究', '算法专家')
LEGACY_TIERS = ('黑铁', '青铜', '白银', '黄金', '铂金', '翡翠', '钻石', '大师', '宗师', '王者')
LEGACY_TITLES = ('编程入门', '基础研习', '算法实践', '结构分析', '状态建模', '构造与证明', '复杂度掌控', '算法设计', '竞赛研究', '算法专家')
LEVEL_CAP = 100  # Public progress protocol 1 accepts levels 1 through 100.
LEVEL_COSTS = tuple(200 * level for level in range(1, LEVEL_CAP))
RANK_UNLOCK_LEVEL = 5
RANK_UNLOCK_XP = sum(LEVEL_COSTS[:RANK_UNLOCK_LEVEL - 1])
MIN_RANK_EVIDENCE = 5
RANK_THRESHOLDS = (0, 800, 1000, 1200, 1600, 1800, 2000, 2100, 2200)
LEGACY_RANK_THRESHOLDS = (0, 300, 700, 1200, 1800, 2500, 3300, 4200, 5300, 6500)


def growth(xp):
    xp = max(0, int(xp))
    remaining, level = xp, 1
    for cost in LEVEL_COSTS:
        if remaining < cost:
            break
        remaining -= cost
        level += 1
    capped = level == LEVEL_CAP
    cost = LEVEL_COSTS[level - 1] if not capped else 0
    return {'xp': xp, 'totalXp': xp, 'level': level, 'levelName': f'Lv.{level}',
            # Protocol-1 fallback fields remain present; XP no longer assigns
            # a skill badge. TrainingService fills these from qualified rank.
            'tier': TIERS[0], 'badge': None,
            'currentLevelXp': remaining if not capped else 0, 'nextLevelXp': cost,
            'rankedEligible': level >= RANK_UNLOCK_LEVEL, 'mode': 'xp',
            'nextMilestone': '已达等级上限' if capped else f'再积累 {cost - remaining} XP 升至 {level + 1} 级',
            'levelCosts': list(LEVEL_COSTS), 'levelCap': LEVEL_CAP,
            'rankUnlockXp': RANK_UNLOCK_XP, 'rankUnlockLevel': RANK_UNLOCK_LEVEL}


def rank_index(score, thresholds=RANK_THRESHOLDS):
    return max(i for i, threshold in enumerate(thresholds) if score >= threshold)


def legacy_ranked_points(evidence, daily_evidence, unlocked_at, now):
    """First independent AC earns points; daily qualifying AC maintains rank.

    Historical ACs cannot earn again after unlock. Maintenance can use a repeat
    AC once per day. Deduction is replayed by Beijing date, including offline
    days, without multiplying it on refresh. Titles follow the current score.
    """
    unlocked = parse_time(unlocked_at)
    today = now.astimezone(SHANGHAI).date()
    start = unlocked.astimezone(SHANGHAI).date()
    first = defaultdict(list)
    for item in evidence:
        timestamp = parse_time(item.get('acceptedAt'))
        difficulty = item.get('difficulty')
        if (timestamp and unlocked <= timestamp <= now and item.get('independent')
                and item.get('scope', 'official') == 'official' and item.get('verdict', 'AC') == 'AC'
                and type(difficulty) in (int, float) and 0 < difficulty <= 1_000_000 and math.isfinite(difficulty)):
            first[timestamp.astimezone(SHANGHAI).date()].append(item)
    daily = defaultdict(list)
    for item in daily_evidence:
        timestamp = parse_time(item.get('acceptedAt'))
        difficulty = item.get('difficulty')
        if (timestamp and unlocked <= timestamp <= now and item.get('independent')
                and item.get('scope', 'official') == 'official' and item.get('verdict', 'AC') == 'AC'
                and type(difficulty) in (int, float) and 0 < difficulty <= 1_000_000 and math.isfinite(difficulty)):
            daily[timestamp.astimezone(SHANGHAI).date()].append(item)
    score, gained, lost, today_gain, today_qualified = 0, 0, 0, 0, 0
    day = start
    while day <= today:
        index = rank_index(score, LEGACY_RANK_THRESHOLDS)
        minimum = min(3000, 800 + 250 * index)
        valid = [item for item in daily[day] if item['difficulty'] >= minimum]
        earned = 0
        for item in sorted(first[day], key=lambda item: item['acceptedAt']):
            required = min(3000, 800 + 250 * rank_index(score, LEGACY_RANK_THRESHOLDS))
            if item['difficulty'] >= required:
                points = 20 + min(180, (int(item['difficulty']) - required) // 10)
                score += points
                earned += points
        gained += earned
        # Complete days only; unlock day is free. Higher tiers require daily AC.
        if day != start and day < today and index >= 5 and not valid:
            deduction = min(score, 10 + 5 * (index - 5))
            score -= deduction
            lost += deduction
        if day == today:
            today_gain, today_qualified = earned, len({item.get('key') or item.get('problemKey') or item.get('problemId') for item in valid})
        day += dt.timedelta(days=1)
    index = rank_index(score, LEGACY_RANK_THRESHOLDS)
    division = min(3, (score - LEGACY_RANK_THRESHOLDS[index]) // 100)
    title = LEGACY_TITLES[index] + (' · ' + str(division + 1) + ' 星' if index < 9 else f' · {1 + (score - 6500) // 500} 星')
    return {'score': score, 'tier': LEGACY_TIERS[index], 'badge': f'tier-{index}', 'title': title,
            'nextScore': LEGACY_RANK_THRESHOLDS[index + 1] if index < 9 else 6500 + (1 + (score - 6500) // 500) * 500,
            'minDifficulty': min(3000, 800 + 250 * index), 'dailyRequired': int(index >= 5),
            'dailyQualified': today_qualified, 'todayPoints': today_gain, 'earnedPoints': gained,
            'decayedPoints': lost, 'unlockedAt': unlocked_at, 'date': today.isoformat(),
            'rules': '独立首次原站 AC 达到当前段位难度后加分，同题只奖励一次。翡翠及以上每天需独立 AC 一道达标题，次日结算缺勤扣分；重复 AC 可维持段位。王者星级持续提升。'}


def _skill_evidence(evidence, now):
    """Defensively deduplicate normalized official facts before filtering.

    The first AC fixes independence: a later replay after reading a solution
    cannot turn a non-independent first AC into a skill credential. Unknown
    public-history independence is never assumed. Existing verified receipts
    from before the XP unlock count; an unlock does not erase proven ability.
    """
    from insights import canonical_url
    facts = []
    for item in evidence:
        if item.get('scope') != 'official' or item.get('verdict', 'AC') != 'AC':
            continue
        identity = item.get('key') or item.get('problemKey') or item.get('problemId')
        stamp = parse_time(item.get('acceptedAt'))
        if not isinstance(identity, str) or not identity.strip() or not stamp or stamp > now:
            continue
        difficulty = item.get('abilityDifficulty', item.get('difficulty'))
        known = (type(difficulty) in (int, float) and 0 < difficulty <= 1_000_000
                 and math.isfinite(difficulty))
        independent = item.get('independent') is True and item.get('independentKnown') is True
        # Conservative ties keep unknown/non-independent facts first.
        facts.append((stamp, canonical_url(identity) or identity, independent and known,
                      int(difficulty) if known else 0))
    first = {}
    for stamp, key, qualified, difficulty in sorted(facts):
        first.setdefault(key, (qualified, difficulty))
    return sorted((difficulty for qualified, difficulty in first.values() if qualified), reverse=True)


def ranked(evidence, daily_evidence, unlocked_at, now, diagnostics=None):
    """Derived Rasch assessment; earned XP and historical awards are untouched."""
    from ability_assessment import assess,from_successes
    evidence, daily_evidence = list(evidence), list(daily_evidence)
    assessment=assess(diagnostics if diagnostics is not None else from_successes(evidence,now),now)
    qualified=assessment['qualified'];ability=assessment['abilityScore']
    index = rank_index(ability) if qualified else None
    next_ability = RANK_THRESHOLDS[index + 1] if index is not None and index + 1 < len(TIERS) else None
    requirements = [{'tier': tier, 'badge': f'tier-{position}', 'minAbilityScore': minimum}
                    for position, (tier, minimum) in enumerate(zip(TIERS, RANK_THRESHOLDS))]
    return {**assessment,'score': ability if qualified else 0, 'abilityScore': ability,
            'tier': TIERS[index] if qualified else None, 'badge': f'tier-{index}' if qualified else None,
            'title': TITLES[index] if qualified else '定级中', 'qualified': qualified,
            'nextScore': next_ability, 'nextAbilityScore': next_ability,
            'minDifficulty': RANK_THRESHOLDS[index] if qualified else None,
            'levelGate': RANK_UNLOCK_LEVEL, 'tierRequirements': requirements, 'thresholds': requirements,
            'unlockedAt': unlocked_at, 'date': now.astimezone(SHANGHAI).date().isoformat(),
            'scoreScale': 'CF 参考能力',
            'legacyPoints': legacy_ranked_points(evidence, daily_evidence, unlocked_at, now)}
