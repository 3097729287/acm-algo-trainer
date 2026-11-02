"""One-time XP ledger for achievements computed by the trusted backend.

There is deliberately no HTTP endpoint accepting achievement definitions or
unlock flags. Training.insights supplies build_insights/extra_achievements output
derived from actual records. This module uses a caller-owned SQLite connection
and transaction; it does not commit, open connections, or perform network I/O.
"""
from __future__ import annotations

import datetime as dt
import math
import json

from progression import ACHIEVEMENT_DEFINITIONS, achievement_title, parse_time
from sticker_rewards import achievement_sticker


def preserve_completion(training,achievements):
    """Remember earned milestones without paying them before an explicit claim."""
    saved={}
    for row in training.connection.execute("SELECT key,value FROM account_preferences WHERE key LIKE 'achievement-unlock:%'"):
        try:value=json.loads(row[1])
        except (ValueError,TypeError):continue
        if isinstance(value,dict):saved[row[0].split(':',1)[1]]=value
    updates=[];now=training._now().astimezone(dt.timezone.utc).isoformat()
    for item in achievements:
        identity=item.get('id');definition=ACHIEVEMENT_DEFINITIONS.get(identity)
        if not definition:continue
        completed=saved.get(identity)
        if completed:
            item.update(unlocked=True,progress=definition['target'],unlockedAt=completed.get('unlockedAt') or completed.get('observedAt'))
        elif item.get('unlocked') is True and item.get('target')==definition['target'] and isinstance(item.get('progress'),(int,float)) and item['progress']>=definition['target']:
            stamp=parse_time(item.get('unlockedAt'))
            at=stamp.astimezone(dt.timezone.utc).isoformat() if stamp else now
            updates.append(('achievement-unlock:'+identity,json.dumps({'unlockedAt':at,'observedAt':now}),now))
            item['unlockedAt']=at
    if updates:
        with training._write() as connection:connection.executemany('INSERT OR IGNORE INTO account_preferences VALUES(?,?,?)',updates)


def award_achievement_xp(connection, achievements, now=None, *, claim_ids=None):
    """Persist newly earned known bonuses and return ``xp/newXp/claims``.

    ``achievements`` must be the complete server-computed collection, never an
    HTTP request body. The fixed definition supplies both target and reward;
    incoming rewardXp and unknown IDs cannot grant arbitrary XP. Both unlocked
    and measured progress must agree before a first claim. Existing claims keep
    their original XP even after a definition or public evidence later changes.
    The caller owns the surrounding write transaction and rollback/backup rules.
    Reads pass an empty collection; a claim passes only its validated stable ID.
    None retains the old helper behavior for restoring legacy award batches.
    """
    stamp = now or dt.datetime.now(dt.timezone.utc)
    stamp = stamp if isinstance(stamp, dt.datetime) else parse_time(stamp)
    if stamp is None:
        raise ValueError('Invalid achievement claim time')
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.timezone.utc)
    claimed_at = stamp.astimezone(dt.timezone.utc).isoformat()
    connection.execute('''CREATE TABLE IF NOT EXISTS achievement_xp_claims (
        achievement_id TEXT PRIMARY KEY,
        unlocked_at TEXT,
        awarded_xp INTEGER NOT NULL CHECK(awarded_xp >= 0),
        claimed_at TEXT NOT NULL
    )''')
    claims = {row[0]: {'unlockedAt': row[1], 'awardedXp': row[2], 'claimedAt': row[3]}
              for row in connection.execute('SELECT achievement_id,unlocked_at,awarded_xp,claimed_at FROM achievement_xp_claims')}
    new_xp = 0
    for item in achievements:
        identity = item.get('id')
        definition = ACHIEVEMENT_DEFINITIONS.get(identity)
        item['rewardXp'] = definition['rewardXp'] if definition else 0
        item['rewardTitle'] = achievement_title(identity)
        item['rewardSticker'] = achievement_sticker(identity)
        item.pop('legacyAwardedXp', None)
        claim = claims.get(identity)
        if claim is None and identity == 'streak-730':
            claim = claims.get('streak-1000')
        if claim is not None:
            # Keep earned achievement display stable through an offline public
            # snapshot or incomplete sync; deleting evidence never grants again.
            item.update(rewardXp=0 if item['rewardTitle'] else claim['awardedXp'], rewardClaimed=True)
            if item['rewardTitle'] and claim['awardedXp']:
                item['legacyAwardedXp'] = claim['awardedXp']
            if definition:
                item.update(unlocked=True, progress=definition['target'], unlockedAt=claim['unlockedAt'])
            continue
        item['rewardClaimed'] = False
        if claim_ids is not None and identity not in claim_ids:
            continue
        progress = item.get('progress')
        if (not definition or item.get('unlocked') is not True
                or not isinstance(progress, (int, float)) or isinstance(progress, bool)
                or not math.isfinite(progress)
                or progress < definition['target'] or item.get('target') != definition['target']):
            continue
        unlocked = parse_time(item.get('unlockedAt'))
        unlocked_at = unlocked.astimezone(dt.timezone.utc).isoformat() if unlocked else None
        amount = definition['rewardXp']
        cursor = connection.execute('INSERT OR IGNORE INTO achievement_xp_claims VALUES(?,?,?,?)',
                                    (identity, unlocked_at, amount, claimed_at))
        if cursor.rowcount:
            new_xp += amount
            claims[identity] = {'unlockedAt': unlocked_at, 'awardedXp': amount, 'claimedAt': claimed_at}
        else:
            row = connection.execute('SELECT unlocked_at,awarded_xp,claimed_at FROM achievement_xp_claims WHERE achievement_id=?', (identity,)).fetchone()
            claims[identity] = {'unlockedAt': row[0], 'awardedXp': row[1], 'claimedAt': row[2]}
        item.update(rewardXp=0 if item['rewardTitle'] else claims[identity]['awardedXp'], rewardClaimed=True)
    return {'xp': sum(value['awardedXp'] for value in claims.values()), 'newXp': new_xp, 'claims': claims}
