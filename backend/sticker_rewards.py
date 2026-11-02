"""Fixed cosmetic rewards. Native claims remain the eligibility authority;
inventory/box randomness and every transfer remain on the account service.
"""
from functools import lru_cache
import json
from paths import resource

@lru_cache(maxsize=1)
def catalogue():
    return json.loads(resource('sticker-rewards.json').read_text(encoding='utf-8'))

def achievement_sticker(identity):
    source=catalogue()
    sticker=source['achievements'].get(identity)
    return next((dict(item) for item in source['stickers'] if item['id']==sticker),None)

def grant_pending(training):
    from gameplay import _request
    from training import iso
    import hashlib
    import uuid
    owner=training._ranking_profile()['user_id']
    def deliver(marker,path,body):
        with training.lock:
            if training.connection.execute('SELECT 1 FROM account_preferences WHERE key=?',(marker,)).fetchone():return
        identity=str(uuid.UUID(hashlib.sha256((owner+'\0'+marker).encode()).hexdigest()[:32],version=4))
        _request(training,'POST',path,{'requestId':identity,**body},expected_owner=owner)
        with training.lock,training._write() as db:
            if training._ranking_profile()['user_id']!=owner:
                from training import ServiceError
                raise ServiceError(409,'账号已切换')
            db.execute('INSERT OR IGNORE INTO account_preferences VALUES(?,?,?)',(marker,'true',iso(training._now())))
    level=training.public_progress().get('level',1)
    if level>=5:deliver('sticker-levels-v1:'+str(level),'/v1/stickers/levels',{'level':level})
    with training.lock:
        claims={row[0] for row in training.connection.execute('SELECT achievement_id FROM achievement_xp_claims')}
    for identity in catalogue()['achievements']:
        if identity in claims:deliver('sticker-achievement:'+identity,'/v1/stickers/achievement',{'achievementId':identity})
