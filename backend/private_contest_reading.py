"""Account-owned contest statements read through an existing original-site login.

Only public roster metadata reaches the shared catalogue. Normalized statements
remain in the requesting account's existing portable-fact table and SQLite cache.
"""
import copy
import hashlib
import json
import re
import threading

from contest_policy import content_ready
from persistence import load_document,save_document
from statement_access import nowcoder_access_notice,StatementAccessRequired

def source_url(value):
    return isinstance(value,str) and bool(re.fullmatch(r'https://ac\.nowcoder\.com/acm/contest/[1-9]\d*/[A-Z][0-9]?',value))

def private_row(fact):
    if not isinstance(fact,dict):return None
    row,statement=fact.get('row'),fact.get('statement')
    if not isinstance(row,dict) or not isinstance(statement,dict) or statement.get('accountReading') is not True:return None
    if not source_url(row.get('url')) or statement.get('url')!=row['url'] or statement.get('id')!=row.get('id') or not content_ready(statement):return None
    return dict(row,catalogContentReady=True,catalogReplayReady=True,statementAvailable=True,catalogHidden=False)

def private_rows(training,identity=None):
    with training.lock:
        query="SELECT value FROM account_problem_facts WHERE CASE WHEN json_valid(value) THEN json_extract(value,'$.statement.accountReading') ELSE 0 END=1"
        values=[]
        if identity is not None:query+=' AND problem_id=?';values.append(identity)
        return [row for item in training.connection.execute(query,values) if (row:=private_row(json.loads(item[0]))) is not None]

def remember(training,rows,statements):
    """Caller holds its account-operation barrier; no browser secrets are accepted."""
    from account_sync import AccountStateSync
    from training import iso
    with training.lock:
        if training.closed:raise RuntimeError('账号工作区已关闭，请重新读取比赛')
        updates=[]
        for row in rows:
            identity=row['id'];statement=statements.get(identity)
            if not statement or not content_ready(statement):continue
            if not source_url(row.get('url')) or statement.get('id')!=identity or statement.get('url')!=row['url']:raise ValueError('原站题面与题单身份不一致')
            raw=training.store.row(identity)
            encoded=training.store.encode_row(raw)
            old=training.portable_problem(identity) or {}
            fact={**old,'row':dict(encoded,id=identity),'raw':copy.deepcopy(raw),'statement':dict(statement,accountReading=True)}
            fact=AccountStateSync._portable_json(fact)
            value=json.dumps(fact,ensure_ascii=False)
            if training.portable_problem(identity)!=fact:updates.append((identity,value,iso(training._now())))
        if updates:
            with training._write() as db:db.executemany('INSERT INTO account_problem_facts VALUES(?,?,?) ON CONFLICT(problem_id) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',updates)
            assets=training.assets
            if assets is not None:
                assets._cached.cache_clear();assets.bundle.cache_clear()

class AccountContestImport:
    def __init__(self,public,training,event,reader,current,saver):
        self.public,self.training,self.event=public,training,event
        self.reader,self.current,self.saver=reader,current,saver
        self.access_required=False;self.access_message=''
        self.lock=threading.RLock();self.closed=False
        self.state_dir=training.db_path.parent/'contest-reading'/hashlib.sha256(event['id'].encode()).hexdigest()
        self.path=self.state_dir/'roster.json'
        self.state=load_document(self.path,{'rows':{}})
        self.stop=self
        self.client=AccountPageClient(self)
        # Reuse previously available public or account-owned statements offline.
        for identity,row in self.state.get('rows',{}).items():
            fact=training.portable_problem(identity)
            if private_row(fact):save_document(self._statement_path(identity),fact['statement'])

    def is_set(self):
        return self.closed or self.public.stop.is_set() or not self.current(self.training)

    def _statement_path(self,identity):return self.state_dir/'statements'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')

    def _save(self):
        if self.is_set():raise RuntimeError('账号已切换，请在当前账号重新读取比赛')
        statements={}
        for identity in self.state['rows']:
            value=load_document(self._statement_path(identity),{})
            if not content_ready(value):
                fact=self.training.portable_problem(identity)
                if private_row(fact):value=fact['statement']
                else:value=load_document(self.public.state_dir/'statements'/(hashlib.sha256(identity.encode()).hexdigest()+'.json'),{})
                if content_ready(value):save_document(self._statement_path(identity),value)
            statements[identity]=value
        with self.public.lock:
            for identity,row in self.state['rows'].items():
                public_statement=load_document(self.public.state_dir/'statements'/(hashlib.sha256(identity.encode()).hexdigest()+'.json'),{})
                public_row={**self.public.state['rows'].get(identity,{}),**copy.deepcopy(row),'catalogContentReady':content_ready(public_statement)}
                if not public_row['catalogContentReady']:public_row['statementNotice']='原站题面尚未公开或需要在原站报名'
                self.public.state['rows'][identity]=public_row
            self.public._save()
        self.saver(self.training,list(self.state['rows'].values()),statements)
        save_document(self.path,self.state)

class AccountPageClient:
    def __init__(self,context):self.context=context
    def __getattr__(self,name):return getattr(self.context.public.client,name)
    def text(self,url,headers=None):
        context=self.context
        page=context.public.client.fresh_text(url,headers=headers)
        if not source_url(url) or not nowcoder_access_notice(page):return page
        if url not in {row['url'] for row in context.state['rows'].values()} or context.is_set():raise ValueError('当前账号没有这道比赛题目的读取请求')
        try:
            if not callable(context.reader):raise StatementAccessRequired('请先在原站登录并报名，再重试题面')
            result=context.reader(url,context.training)
            if context.is_set():raise RuntimeError('账号已切换，请重新读取比赛')
            return result
        except StatementAccessRequired as error:
            context.access_required=True;context.access_message=str(error)
            raise
    fresh_text=text
