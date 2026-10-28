"""Reusable public code and account-owned templates in the existing SQLite journal."""
import json
import re
import uuid
from functools import lru_cache
from paths import resource
from training import ServiceError, iso

PREFIX = 'custom-template:'
MAX_CODE_BYTES = 64 * 1024

@lru_cache(maxsize=1)
def builtins():
    return json.loads(resource('code-templates.json').read_text(encoding='utf8'))['templates']

def _owned(training):
    values=[]
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'custom-template:%'"):
        value=json.loads(row[0])
        if not value.get('deleted'):values.append(value)
    return sorted(values,key=lambda item:(item['title'].casefold(),item['id']))

def catalog(training):
    with training.lock:
        passed={row[0] for row in training.connection.execute("SELECT DISTINCT problem_id FROM submissions WHERE scope='template' AND verdict='AC' AND mode='submit' AND finished_at IS NOT NULL")}
        return {'templates':[{**item,'practicePassed':[identity in passed for identity in item.get('practiceIds',[])]} for item in builtins()]+_owned(training)}

def save(training,body):
    if not isinstance(body,dict) or set(body)-{'id','title','category','language','code','notes','summary','revision','delete'}:
        raise ServiceError(400,'模板格式无效')
    identity=body.get('id')
    if identity is not None and (not isinstance(identity,str) or not re.fullmatch(r'custom-template:[a-f0-9]{32}',identity)):
        raise ServiceError(400,'内置模板请另存为自己的模板')
    if type(body.get('delete',False)) is not bool:
        raise ServiceError(400,'模板操作无效')
    with training.lock:
        record=training.connection.execute('SELECT value FROM account_preferences WHERE key=?',(identity,)).fetchone() if identity else None
        previous=json.loads(record[0]) if record else None
        if identity and (previous is None or previous.get('deleted')):
            raise ServiceError(404,'没有找到这个模板')
        if previous and body.get('revision')!=previous.get('revision'):
            raise ServiceError(409,'模板已在其它位置修改，请重新读取后保存')
        now=iso(training._now())
        if body.get('delete'):
            if previous is None:raise ServiceError(404,'没有找到这个模板')
            value={**previous,'deleted':True,'updatedAt':now,'revision':uuid.uuid4().hex}
        else:
            fields={key:body.get(key,'') for key in ['title','category','language','code','notes','summary']}
            limits={'title':120,'category':40,'language':16,'code':MAX_CODE_BYTES,'notes':16*1024,'summary':400}
            if any(not isinstance(value,str) or len(value.encode('utf8'))>limits[key] or '\x00' in value for key,value in fields.items()):
                raise ServiceError(400,'模板内容过长或格式无效')
            fields['title']=fields['title'].strip()
            fields['category']=fields['category'].strip() or '我的模板'
            if not fields['title'] or not fields['code'].strip() or fields['language'] not in {'cpp17','python3'}:
                raise ServiceError(400,'请填写模板名称、语言和代码')
            if previous is None and len(_owned(training))>=128:
                raise ServiceError(400,'自建模板已达 128 个，请先整理已有模板')
            value={**fields,'id':identity or PREFIX+uuid.uuid4().hex,'builtin':False,'tags':[],
                   'createdAt':previous['createdAt'] if previous else now,'updatedAt':now,'revision':uuid.uuid4().hex}
        # One document per template: independent edits and deletion tombstones
        # travel with the existing private account snapshot, never public library.
        with training._write() as db:
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (value['id'],json.dumps(value,ensure_ascii=False,sort_keys=True),now))
        return {'template':value,'templates':[*builtins(),*_owned(training)]}
