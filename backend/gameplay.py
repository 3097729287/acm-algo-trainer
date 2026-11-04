"""Account-bound relay. Inventory and match authority stay on the shared service."""
import hashlib
import json
import uuid
from training import ServiceError, iso
from leaderboard import RankingRequestError

def daily_pack_rarity(owner, day, task_id):
    from sticker_rewards import catalogue
    roll=int.from_bytes(hashlib.sha256((owner+'\0'+day+'\0'+task_id+'\0pack-v1').encode()).digest()[:4],'big')%10000
    for tier,weight in catalogue()['dailyPacks']['probabilities'].items():
        roll-=weight
        if roll<0:return tier
    raise ValueError('卡包概率配置无效')

def rarity(task):
    difficulty=task.get('minDifficulty') or 0
    xp=task.get('xp') or 0
    return 'legendary' if difficulty>=2200 or xp>=100 else 'epic' if difficulty>=1800 or xp>=60 else 'rare' if difficulty>=1400 or xp>=30 else 'common'

def _request(training, method, path, value=None, *, expected_owner=None):
    profile=training._ranking_profile()
    if expected_owner is not None and profile['user_id']!=expected_owner:
        raise ServiceError(409,'账号已切换')
    if training.admin_mode or not profile['endpoint'] or not profile['auth_token']:
        raise ServiceError(503,'在线对战与贴纸需要连接账号服务')
    try:
        result=training.leaderboard._request(profile,method,path,value)
    except RankingRequestError as error:
        raise ServiceError(error.status,str(error)) from error
    except (OSError,ValueError,RuntimeError) as error:
        raise ServiceError(503,'账号服务暂时无法连接') from error
    if training._ranking_profile()['user_id']!=profile['user_id']:
        raise ServiceError(409,'账号已切换')
    if result.get('owner')!=profile['user_id']:
        raise ServiceError(502,'账号服务回执无效')
    return result

def _grant_pending(training, only=None):
    """Committed claims form a durable outbox. A lost response is safe to replay.

    This does not trust posted UI completion flags, or award historical tasks.
    Server grants have a unique owner/day/task identity independent of snapshots.
    """
    owner=training._ranking_profile()['user_id']
    with training.lock:
        query="SELECT key,value FROM account_preferences p WHERE key LIKE 'sticker-eligible:%' AND NOT EXISTS(SELECT 1 FROM account_preferences done WHERE done.key='sticker-grant:'||substr(p.key,18))"
        records=[dict(row) for row in training.connection.execute(query+(" AND p.key=?" if only is not None else '')+" ORDER BY key LIMIT 100",('sticker-eligible:'+only,) if only is not None else ())]
    inventory=None
    for row in records:
        if only is not None and row['key']!='sticker-eligible:'+only:continue
        suffix=row['key'][len('sticker-eligible:'):]
        day,task_id=suffix[:10],suffix[11:]
        marker='sticker-grant:'+suffix
        task=json.loads(row['value'])
        identity=str(uuid.UUID(hashlib.sha256((owner+'\0'+marker).encode()).hexdigest()[:32],version=4))
        delivered=_request(training,'POST','/v1/stickers/grant',{'requestId':identity,'day':day,'taskId':task_id,'xp':task.get('stickerXp',task['xp']),'minDifficulty':task.get('minDifficulty',0),**({'rewardSlot':task['stickerSlot']} if task.get('stickerSlot') else {})},expected_owner=owner)
        with training.lock,training._write() as db:
            if training._ranking_profile()['user_id']!=owner:
                raise ServiceError(409,'账号已切换')
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO NOTHING',(marker,'true',iso(training._now())))
        inventory=delivered.get('inventory') or inventory
    return inventory

def stickers(training,kind=None,value=None):
    owner=training._ranking_profile()['user_id']
    mutation={}
    if kind:
        allowed={'open-background':{'requestId','rewardId'},'place':{'requestId','unitId','revision','x','y','angle','scale'},'recycle':{'requestId','unitId','revision'},'open-box':{'requestId','boxId'},'open-packs':{'requestId','rarity','count'},'outfit':{'requestId','unitId','revision','appearance'},'scene-save':{'requestId','name','presetId','inventoryRevision'},'scene-apply':{'requestId','presetId','inventoryRevision'},'scene-delete':{'requestId','presetId','inventoryRevision'}}
        if kind not in allowed or not isinstance(value,dict) or set(value)-allowed[kind]:raise ServiceError(400,'贴纸操作无效')
        mutation=_request(training,'POST','/v1/stickers/'+kind,value,expected_owner=owner)
        # The inventory view has already delivered the durable reward outbox.
        # An individual open/place/recycle must not wait for a full growth scan
        # and unrelated pending grants again. Keep those on the next read.
        result=mutation.get('inventory')
        if result is not None:
            if not isinstance(result,dict) or result.get('owner')!=owner or not isinstance(result.get('units'),list):
                raise ServiceError(502,'贴纸库存响应无效')
        else:
            result=_request(training,'GET','/v1/stickers',expected_owner=owner)
        from fun_moments import confirmed_gameplay
        confirmed_gameplay(training,result,kind)
        if mutation.get('opening'):result['opening']=mutation['opening']
        if mutation.get('scene'):result['scene']=mutation['scene']
        return result
    error=None
    try:
        from background_rewards import deliver_completed
        deliver_completed(training)
        _grant_pending(training)
        from sticker_rewards import grant_pending
        grant_pending(training)
    except ServiceError as issue:error=str(issue)
    result=_request(training,'GET','/v1/stickers',expected_owner=owner)
    from fun_moments import confirmed_gameplay
    confirmed_gameplay(training,result,kind)
    if error:result['rewardSyncError']=error
    if mutation.get('opening'):result['opening']=mutation['opening']
    return result

def duel(training,kind=None,value=None):
    owner=training._ranking_profile()['user_id']
    if not kind:
        result=_request(training,'GET','/v1/duels',expected_owner=owner)
        from fun_moments import confirmed_gameplay
        confirmed_gameplay(training,result)
        return result
    if kind not in {'join','cancel','poll','dismiss','ready','decline'} or not isinstance(value,dict) or set(value)-{'requestId','ticket','matchId','readyCheck'}:
        raise ServiceError(400,'对战操作无效')
    if kind=='join':
        with training.lock:
            if training.active_contest():raise ServiceError(409,'请先结束当前模拟赛')
        settings=training.store.extensions.snapshot().get('settings',{})
        handle=settings.get('accounts',{}).get('codeforces','')
        value={**value,'handle':handle}
    result=_request(training,'POST','/v1/duels/'+kind,value,expected_owner=owner)
    from fun_moments import confirmed_gameplay
    confirmed_gameplay(training,result)
    return result


def claimed_pack(training, day, identity):
    owner=training._ranking_profile()['user_id']
    inventory=_grant_pending(training, only=day+':'+identity)
    return inventory or _request(training,'GET','/v1/stickers',expected_owner=owner)
