"""An account-owned slower introduction, selected once by a new beginner.

Historical accounts keep their original curve and every earned XP row. This
policy is journalled independently of the old assessment schema, so mixed
clients can retain it without altering that schema or its once-only grant.
"""
import copy
import json
from progression import parse_time
from tb_rank import LEVEL_COSTS

KEY='starter-level-curve-v1'
BEGINNER_COSTS=(200,400,600,800)+LEVEL_COSTS[4:]

def validate(value,owner=None):
    if (not isinstance(value,dict) or set(value)!={'version','owner','selectedAt'}
        or type(value.get('version')) is not int or value['version']!=1
        or not isinstance(value.get('owner'),str) or not value['owner']
        or owner is not None and value['owner']!=owner or not parse_time(value.get('selectedAt'))):return None
    return copy.deepcopy(value)

def read(training):
    row=training.connection.execute('SELECT value FROM account_preferences WHERE key=?',(KEY,)).fetchone()
    try:return validate(json.loads(row[0]),training._ranking_profile()['user_id']) if row else None
    except (ValueError,TypeError):return None

def choose(training,connection,initial_growth):
    # Existing Lv.2+ users and already chosen legacy beginners never migrate.
    if initial_growth.get('level')!=1:return
    from training import iso
    stamp=iso(training._now())
    value={'version':1,'owner':training._ranking_profile()['user_id'],'selectedAt':stamp}
    connection.execute('INSERT OR IGNORE INTO account_preferences VALUES(?,?,?)',(KEY,json.dumps(value,sort_keys=True),stamp))

def costs(training):
    if read(training):
        from experience_challenge import read as assessment
        # A concurrent legitimate veteran assignment still follows the tested
        # legacy 500-XP top-up; the assessment schema/grant never changes.
        if assessment(training).get('choice')!='experienced':return BEGINNER_COSTS
    return LEVEL_COSTS

def merge(left,right):
    valid=[value for raw in (left,right) if (value:=validate(raw))]
    if not valid or len({value['owner'] for value in valid})!=1:return None
    return min(valid,key=lambda value:value['selectedAt'])

def preserve_rows(training,rows):
    local=read(training)
    if not local:return rows,False
    incoming=next((row for row in rows if row.get('key')==KEY),None)
    try:remote=validate(json.loads(incoming['value']),local['owner']) if incoming else None
    except (ValueError,TypeError):remote=None
    value=merge(local,remote)
    if remote==value:return rows,False
    current=dict(training.connection.execute('SELECT * FROM account_preferences WHERE key=?',(KEY,)).fetchone())
    current['value']=json.dumps(value,sort_keys=True)
    return [row for row in rows if row.get('key')!=KEY]+[current],True
