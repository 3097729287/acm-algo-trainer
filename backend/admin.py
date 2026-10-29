"""Local administrator controls. This workspace never authenticates to cloud services."""
import json
from training import ServiceError, iso

DEFAULTS = {'level': 100, 'tier': 8, 'allAchievements': True}

def controls(service, body=None):
    if not getattr(service, 'admin_mode', False):
        raise ServiceError(404, '没有找到这个接口')
    with service.lock:
        row = service.connection.execute("SELECT value FROM account_preferences WHERE key='admin-controls'").fetchone()
        stored = json.loads(row['value']) if row else {}
        value = {key: stored.get(key, default) for key, default in DEFAULTS.items()}
        if type(stored.get('previewVersion')) is not int or stored['previewVersion'] < 1:
            # One admin-only display migration; later explicit off is retained.
            # A read does not manufacture achievement/XP claims or user state.
            value['allAchievements'] = True
        if row and stored.get('rankLadderVersion', 1) < 2:
            # The previous ten-tier ladder included platinum at index 4.
            previous = max(0, min(9, int(value['tier'])))
            value['tier'] = previous - 1 if previous >= 4 else previous
        if body is not None:
            if (not isinstance(body, dict) or set(body) != set(DEFAULTS)
                    or type(body['level']) is not int or not 1 <= body['level'] <= 100
                    or type(body['tier']) is not int or not 0 <= body['tier'] <= 8
                    or type(body['allAchievements']) is not bool):
                raise ServiceError(400, '管理员等级、段位或成就选项无效')
            value = dict(body)
            with service._write() as connection:
                if value['allAchievements']:
                    connection.execute("INSERT OR IGNORE INTO account_preferences VALUES('admin-granted-at',?,?)",(iso(service._now()),iso(service._now())))
                connection.execute("INSERT INTO account_preferences VALUES('admin-controls',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at", (json.dumps({**value, 'rankLadderVersion': 2, 'previewVersion': 1}), iso(service._now())))
        return value

def decorate(service, value):
    from tb_rank import growth, LEVEL_COSTS, RANK_THRESHOLDS, TIERS
    from progression import ACHIEVEMENT_DEFINITIONS, earned_titles
    setting = controls(service)
    index = setting['tier']
    value['growth'].update(growth(sum(LEVEL_COSTS[:setting['level'] - 1])))
    value['growth'].update(admin=True, rankedEligible=True, rankUnlockLevel=1, tier=TIERS[index], badge=f'tier-{index}',
                           ranked={'qualified':True, 'tier':TIERS[index], 'badge':f'tier-{index}', 'score':RANK_THRESHOLDS[index], 'abilityScore':RANK_THRESHOLDS[index], 'levelGate':1, 'rules':'管理员工作区手动设置'})
    if setting['allAchievements']:
        granted=service.connection.execute("SELECT value FROM account_preferences WHERE key='admin-granted-at'").fetchone()
        timestamp=granted['value'] if granted else iso(service._now())
        for item in value['achievements']:
            item.update(unlocked=True, progress=item.get('target',1), unlockedAt=timestamp, rewardClaimed=True, adminGranted=True)
        titles,equipped=earned_titles({key:{'unlockedAt':timestamp} for key in ACHIEVEMENT_DEFINITIONS})
        value.update(titles=titles,equippedTitles=equipped)
        value['growth'].update(titles=titles,equippedTitles=equipped)
    value['admin']=True
    return value
