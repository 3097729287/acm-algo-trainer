"""Account-bound relay. Inventory and match authority stay on the shared service."""
import hashlib
import json
import uuid
from training import ServiceError, iso
from leaderboard import RankingRequestError

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

def _grant_pending(training):
    """Committed claims form a durable outbox. A lost response is safe to replay.

    This does not trust posted UI completion flags, or award historical tasks.
    Server grants have a unique owner/day/task identity independent of snapshots.
    """
    owner=training._ranking_profile()['user_id']
    with training.lock:
        records=[dict(row) for row in training.connection.execute("SELECT key,value FROM account_preferences p WHERE key LIKE 'sticker-eligible:%' AND NOT EXISTS(SELECT 1 FROM account_preferences done WHERE done.key='sticker-grant:'||substr(p.key,18)) ORDER BY key LIMIT 100")]
    for row in records:
        suffix=row['key'][len('sticker-eligible:'):]
        day,task_id=suffix[:10],suffix[11:]
        marker='sticker-grant:'+suffix
        task=json.loads(row['value'])
        identity=str(uuid.UUID(hashlib.sha256((owner+'\0'+marker).encode()).hexdigest()[:32],version=4))
        _request(training,'POST','/v1/stickers/grant',{'requestId':identity,'day':day,'taskId':task_id,'xp':task['xp'],'minDifficulty':task.get('minDifficulty',0)},expected_owner=owner)
        with training.lock,training._write() as db:
            if training._ranking_profile()['user_id']!=owner:
                raise ServiceError(409,'账号已切换')
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO NOTHING',(marker,'true',iso(training._now())))

def stickers(training,kind=None,value=None):
    if kind:
        allowed={'requestId','unitId','revision','x','y','angle'} if kind=='place' else {'requestId','unitId','revision'}
        if kind not in {'place','recycle'} or not isinstance(value,dict) or set(value)-allowed:raise ServiceError(400,'贴纸操作无效')
        _request(training,'POST','/v1/stickers/'+kind,value)
    error=None
    try:_grant_pending(training)
    except ServiceError as issue:error=str(issue)
    result=_request(training,'GET','/v1/stickers')
    if error:result['rewardSyncError']=error
    return result

def duel(training,kind=None,value=None):
    if not kind:return _request(training,'GET','/v1/duels')
    if kind not in {'join','cancel','poll','dismiss'} or not isinstance(value,dict) or set(value)-{'requestId','ticket','matchId'}:
        raise ServiceError(400,'对战操作无效')
    if kind=='join':
        with training.lock:
            if training.active_contest():raise ServiceError(409,'请先结束当前模拟赛')
        settings=training.store.extensions.snapshot().get('settings',{})
        handle=settings.get('accounts',{}).get('codeforces','')
        value={**value,'handle':handle}
    return _request(training,'POST','/v1/duels/'+kind,value)
