"""TB progression and personal ranked points derived from official receipts."""
from collections import defaultdict
import datetime as dt
from progression import SHANGHAI, parse_time, local_date

TIERS = ('黑铁', '青铜', '白银', '黄金', '铂金', '翡翠', '钻石', '大师', '宗师', '王者')
TITLES = ('初入赛场', '坚毅学徒', '解题新秀', '独立先锋', '算法精英', '攻坚专家', '钻石领航', '算法大师', '巅峰宗师', '最强王者')
LEVEL_COSTS = tuple(200 * level for level in range(1, 10))
RANK_UNLOCK_XP = sum(LEVEL_COSTS)
RANK_THRESHOLDS = (0, 300, 700, 1200, 1800, 2500, 3300, 4200, 5300, 6500)


def growth(xp):
    xp = max(0, int(xp))
    remaining, level = xp, 1
    for cost in LEVEL_COSTS:
        if remaining < cost:
            break
        remaining -= cost
        level += 1
    ranked = level == 10
    cost = LEVEL_COSTS[level - 1] if not ranked else 0
    return {'xp': xp, 'totalXp': xp, 'level': level, 'levelName': TITLES[level - 1],
            'tier': TIERS[level - 1], 'badge': f'tier-{level - 1}',
            'currentLevelXp': remaining if not ranked else 0, 'nextLevelXp': cost,
            'rankedEligible': ranked, 'mode': 'ranked' if ranked else 'xp',
            'nextMilestone': '已解锁 TB 排位' if ranked else f'再积累 {cost - remaining} XP 升至 {level + 1} 级',
            'levelCosts': list(LEVEL_COSTS), 'rankUnlockXp': RANK_UNLOCK_XP}


def rank_index(score):
    return max(i for i, threshold in enumerate(RANK_THRESHOLDS) if score >= threshold)


def ranked(evidence, daily_evidence, unlocked_at, now):
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
        if timestamp and timestamp >= unlocked and item.get('independent') and isinstance(item.get('difficulty'), (int, float)):
            first[timestamp.astimezone(SHANGHAI).date()].append(item)
    daily = defaultdict(list)
    for item in daily_evidence:
        timestamp = parse_time(item.get('acceptedAt'))
        if timestamp and timestamp >= unlocked and item.get('independent') and isinstance(item.get('difficulty'), (int, float)):
            daily[timestamp.astimezone(SHANGHAI).date()].append(item)
    score, gained, lost, today_gain, today_qualified = 0, 0, 0, 0, 0
    day = start
    while day <= today:
        index = rank_index(score)
        minimum = min(3000, 800 + 250 * index)
        valid = [item for item in daily[day] if item['difficulty'] >= minimum]
        earned = 0
        for item in sorted(first[day], key=lambda item: item['acceptedAt']):
            required = min(3000, 800 + 250 * rank_index(score))
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
            today_gain, today_qualified = earned, len({item['key'] for item in valid})
        day += dt.timedelta(days=1)
    index = rank_index(score)
    division = min(3, (score - RANK_THRESHOLDS[index]) // 100)
    title = TITLES[index] + (' · ' + str(division + 1) + ' 星' if index < 9 else f' · {1 + (score - 6500) // 500} 星')
    return {'score': score, 'tier': TIERS[index], 'badge': f'tier-{index}', 'title': title,
            'nextScore': RANK_THRESHOLDS[index + 1] if index < 9 else 6500 + (1 + (score - 6500) // 500) * 500,
            'minDifficulty': min(3000, 800 + 250 * index), 'dailyRequired': int(index >= 5),
            'dailyQualified': today_qualified, 'todayPoints': today_gain, 'earnedPoints': gained,
            'decayedPoints': lost, 'unlockedAt': unlocked_at, 'date': today.isoformat(),
            'rules': '独立首次原站 AC 达到当前段位难度后加分，同题只奖励一次。翡翠及以上每天需独立 AC 一道达标题，次日结算缺勤扣分；重复 AC 可维持段位。王者星级持续提升。'}
