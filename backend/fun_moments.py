"""Playful one-off moments from real records and confirmed account actions.

These do not assert algorithm mastery. Completion and reward ownership use the
existing durable achievement ledgers; hidden entries are concealed until earned.
"""
import datetime as dt
import json
from collections import defaultdict

from progression import SHANGHAI,parse_time

from fun_moment_definitions import MOMENTS


def _events(training):
    events=[]
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'activity-actions:%'"):
        try:document=json.loads(row[0])
        except (ValueError,TypeError):continue
        if isinstance(document,dict):events.extend(item for item in document.values() if isinstance(item,dict))
    return events


def from_facts(training,records):
    dates={}
    def unlock(identity,stamp):
        parsed=parse_time(stamp)
        if parsed and parsed<=now and (identity not in dates or parsed<parse_time(dates[identity])):dates[identity]=stamp
    now=training._now()
    official=sorted((record for record in records if record.get('scope')=='official' and record.get('mode')=='submit'
                     and isinstance(record.get('problem_id'),str) and record['problem_id']
                     and (submitted:=parse_time(record.get('submitted_at'))) and (finished:=parse_time(record.get('finished_at')))
                     and submitted<=finished<=now),key=lambda r:r['submitted_at'])
    # The language journal is local account evidence. No source programs are
    # exported, and absent Python metadata never invents a Python acceptance.
    languages={row[0].split(':',1)[1]:row[1] for row in training.connection.execute("SELECT key,value FROM account_preferences WHERE key LIKE 'submission-language:%'")}
    previous={};accepted_languages=defaultdict(set)
    contests={row['id']:row['deadline'] for row in training.connection.execute('SELECT id,deadline FROM contests')}
    for record in official:
        identity=record.get('problem_id');stamp=parse_time(record['submitted_at']);old=previous.get(identity)
        if record.get('verdict')=='AC':
            if old and old.get('verdict') in {'CE','WA','TLE','MLE','RE','OLE'}:
                elapsed=stamp-parse_time(old['submitted_at'])
                if dt.timedelta(0)<=elapsed<=dt.timedelta(hours=1):unlock('moment-rebound',record['submitted_at'])
                first,second=old.get('code'),record.get('code')
                if old.get('verdict')=='CE' and isinstance(first,str) and 'main' in first and isinstance(second,str) and len(second)==len(first)+1:
                    at=0
                    while at<len(first) and first[at]==second[at]:at+=1
                    if second[at:at+1]==';' and first[at:]==second[at+1:]:unlock('moment-semicolon',record['submitted_at'])
            language=languages.get(str(record.get('id')),'cpp17')
            if language in {'cpp17','python3'}:accepted_languages[identity].add(language)
            if len(accepted_languages[identity])==2:unlock('moment-polyglot',record['submitted_at'])
            local=stamp.astimezone(SHANGHAI)
            if local.strftime('%H%M')==local.strftime('%H%M')[::-1]:unlock('moment-palindrome',record['submitted_at'])
            if local.weekday()==0:unlock('moment-monday',record['submitted_at'])
            if old and old.get('verdict') in {'CE','WA','TLE','MLE','RE','OLE'} and dt.timedelta(0)<=stamp-parse_time(old['submitted_at'])<=dt.timedelta(hours=1):
                first,second=old.get('code'),record.get('code')
                if isinstance(first,str) and isinstance(second,str) and first and len(first)==len(second) and sum(a!=b for a,b in zip(first,second))==1:unlock('moment-one-character',record['submitted_at'])
            if local.hour==local.minute==local.second:unlock('moment-clock',record['submitted_at'])
            deadline=parse_time(contests.get(record.get('contest_id')))
            if deadline and dt.timedelta(0)<=deadline-stamp<=dt.timedelta(seconds=5):unlock('moment-photo-finish',record['submitted_at'])
        previous[identity]=record
    found=training.connection.execute("SELECT MIN(finished_at) FROM submissions WHERE mode='run' AND verdict='RUN_OK' AND finished_at IS NOT NULL AND trim(output,char(9)||char(10)||char(13)||' ')='42'").fetchone()[0]
    if found:unlock('moment-42',found)
    events=_events(training)
    kind_to_moment={'sticker-gallery':'moment-gallery','sticker-rainbow':'moment-rainbow',
                    'sticker-upside-down':'moment-upside-down','sticker-returned':'moment-returned',
                    'duel-tie':'moment-duel-tie','duel-rebound-win':'moment-duel-rebound'}
    wiki_categories={}
    for event in events:
        kind=event.get('kind')
        if kind in kind_to_moment:unlock(kind_to_moment[kind],event.get('at'))
        if kind=='wiki-category' and event.get('key') and parse_time(event.get('at')):
            wiki_categories.setdefault(event['key'],event['at'])
    for row in training.connection.execute("SELECT key,value FROM account_preferences WHERE key LIKE 'wiki-discovered:%'"):
        try:visit=json.loads(row[1])
        except (ValueError,TypeError):continue
        if isinstance(visit,dict) and parse_time(visit.get('at')):wiki_categories.setdefault(row[0],visit['at'])
    visits=sorted(wiki_categories.values())
    if len(visits)>=3:unlock('moment-wiki-trip',visits[2])
    teases=[parse_time(event.get('at')) for event in events if event.get('kind')=='leader-tease' and parse_time(event.get('at'))]
    for row in training.connection.execute('SELECT awards FROM ranking_reward_totals'):
        try:awards=json.loads(row[0])
        except (ValueError,TypeError):continue
        for award in awards if isinstance(awards,list) else []:
            if award.get('rank')!=1 or award.get('period') not in {'daily','day'}:continue
            day=award.get('startDate') or award.get('start') or award.get('date')
            raw=award.get('settledAt') or award.get('awardedAt') or award.get('createdAt') or award.get('at')
            settled=parse_time(raw)
            if settled and any(t<settled and t.astimezone(SHANGHAI).date().isoformat()==str(day)[:10] for t in teases):unlock('moment-prophet',raw)
    amounts={}
    row=training.connection.execute("SELECT value FROM account_preferences WHERE key='gameplay-moments-v1'").fetchone()
    try:facts=json.loads(row[0]) if row else {}
    except (ValueError,TypeError):facts={}
    if not isinstance(facts,dict):facts={}
    if facts.get('owner')==training._ranking_profile().get('user_id'):
        amounts={'moment-collection-12':facts.get('uniqueStickers',0),'moment-collection-24':facts.get('uniqueStickers',0),'moment-first-gift':facts.get('sent',0),'moment-gift-five':facts.get('recipients',0),'moment-gift-circle':facts.get('recipients',0),
                 'moment-receive-gift':facts.get('received',0),'moment-box-first':facts.get('opened',0),'moment-box-ten':facts.get('opened',0),
                 'moment-box-lucky':int(bool(facts.get('lucky'))),'moment-box-rainbow':int(bool(facts.get('rainbow')))}
        for identity,amount in amounts.items():
            if amount>=MOMENTS[identity].get('target',1):unlock(identity,facts.get('observedAt'))
    return [dict(id=identity,name=definition['name'],description=definition['description'],target=definition.get('target',1),
                 progress=min(definition.get('target',1),amounts.get(identity,int(identity in dates))),unlocked=identity in dates,unlockedAt=dates.get(identity),
                 hidden=definition['hidden'],category='fun',rewardXp=definition['xp']) for identity,definition in MOMENTS.items()]


def confirmed_wiki_visit(training,article):
    if not isinstance(article,dict) or not article.get('category') or not article.get('id'):return
    stamp=training._now().astimezone(dt.timezone.utc).isoformat()
    with training.lock,training._write() as db:
        db.execute('INSERT OR IGNORE INTO account_preferences VALUES(?,?,?)',
                   ('wiki-discovered:'+article['category'],json.dumps({'articleId':article['id'],'at':stamp}),stamp))


def confirmed_gameplay(training,view,kind=None):
    """Called only after the owner-checked shared-service receipt succeeds."""
    owner=training._ranking_profile()['user_id']
    if view.get('owner')!=owner:return
    now=training._now();stamp=now.astimezone(dt.timezone.utc).isoformat();proof=[]
    units=view.get('units')
    if isinstance(units,list):
        boxes=view.get('boxes') or {}
        opened=[box for box in boxes.values() if isinstance(box,dict) and box.get('openedAt')]
        stats=view.get('giftStats') or {}
        known_stickers={item.get('id') for item in view.get('catalogue',[]) if isinstance(item,dict)}
        observed={'owner':owner,'uniqueStickers':len({u.get('stickerId') for u in units if isinstance(u,dict) and u.get('stickerId') in known_stickers}),'sent':stats.get('sent',0),'recipients':stats.get('recipients',0),'received':stats.get('received',0),'opened':len(opened),
                  'lucky':any(any(drop.get('rarity')=='legendary' for drop in box.get('drops',[])) for box in opened),
                  'rainbow':any({drop.get('rarity') for drop in box.get('drops',[])}>={'common','rare','epic','legendary'} for box in opened)}
        with training.lock:
            row=training.connection.execute("SELECT value FROM account_preferences WHERE key='gameplay-moments-v1'").fetchone()
            try:previous=json.loads(row[0]) if row else {}
            except (ValueError,TypeError):previous={}
            if not isinstance(previous,dict):previous={}
            for key in ('sent','recipients','received','opened','lucky','rainbow','uniqueStickers'):
                observed[key]=max(observed[key],previous.get(key,0) if previous.get('owner')==owner else 0)
            if any(observed[key]!=previous.get(key) for key in observed):
                observed['observedAt']=stamp
                with training._write() as db:db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',('gameplay-moments-v1',json.dumps(observed),stamp))
        catalogue={item['id']:item.get('rarity') for item in view.get('catalogue',[]) if isinstance(item,dict) and item.get('id')}
        distinct={unit['id']:unit for unit in units if isinstance(unit,dict) and unit.get('id')}
        placed=[unit for unit in distinct.values() if isinstance(unit.get('placement'),dict)]
        if len(placed)>=5:proof.append(('sticker-gallery','five-placed'))
        if {catalogue.get(unit.get('stickerId')) for unit in distinct.values()}>={'common','rare','epic','legendary'}:proof.append(('sticker-rainbow','four-rarities'))
        if any(abs(abs(unit['placement'].get('angle',0))-180)<.01 for unit in placed):proof.append(('sticker-upside-down','half-turn'))
        if kind=='recycle':proof.append(('sticker-returned','confirmed-recycle'))
    room=view.get('match') or {}
    if room.get('status')=='finished':
        players=room.get('players') or [];self_player=next((p for p in players if p.get('owner')==owner),None)
        if len(players)==2 and players[0].get('acceptedAt') and players[0].get('acceptedAt')==players[1].get('acceptedAt'):proof.append(('duel-tie',room['id']))
        if self_player and room.get('winner')==owner and self_player.get('acceptedAt') and self_player.get('attempts',0)>1:proof.append(('duel-rebound-win',room['id']))
    if proof:
        # Save completion once, rather than creating activity on every poll or
        # every later day that the same inventory/match is displayed.
        with training.lock,training._write() as db:
            if training._ranking_profile()['user_id']!=owner:return
            for event,key in proof:
                identity={'sticker-gallery':'moment-gallery','sticker-rainbow':'moment-rainbow',
                          'sticker-upside-down':'moment-upside-down','sticker-returned':'moment-returned',
                          'duel-tie':'moment-duel-tie','duel-rebound-win':'moment-duel-rebound'}[event]
                db.execute('INSERT OR IGNORE INTO account_preferences VALUES(?,?,?)',
                           ('achievement-unlock:'+identity,json.dumps({'unlockedAt':stamp,'observedAt':stamp,'evidenceId':key}),stamp))
