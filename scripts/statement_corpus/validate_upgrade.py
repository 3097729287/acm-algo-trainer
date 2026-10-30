import os
"""Actual previous public seed -> current seed, with synthetic private facts."""
import hashlib,json,sqlite3,sys
from pathlib import Path
from contextlib import closing
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from library import LibraryDatabase
from statement_seed import checksum
from store import Store
from test_library import record
path=ROOT/'upgrade-validation-verified/live.sqlite3';path.parent.mkdir(exist_ok=True)
assert not path.exists(),'Use a fresh isolated output'
live=LibraryDatabase(path);live.merge_seed(ROOT/'baseline.sqlite3',fingerprint='previous-delivered-public-seed')
retired=json.loads((REPO/'docs/statement-integrity-20261030/retired.json').read_text('utf8'));retired_ids={r['id'] for r in retired}
identity=next(iter(retired_ids));custom={'id':identity,'url':live.find(identity)['url'],'markdown':'Synthetic user-edited original.','samples':[{'input':'1','output':'2'}],
    'translation':{'kind':'site','markdown':'仅供隔离验证的私人备注。'}}
live.save_statement(identity,custom);custom_hash=checksum(live.statement(identity))
raw,encoded,solution,statement=record('private-import::A');live.import_records([(raw,encoded,solution,statement)],{}, {})
with closing(sqlite3.connect(path)) as writer:
    writer.execute('pragma journal_mode=WAL');writer.execute('create table private_facts(kind text primary key,content text)')
    facts=[(key,'synthetic '+key) for key in ('training','draft','code','submission','experience','account','private-list','import')]
    writer.executemany('insert into private_facts values (?,?)',facts);writer.commit()
    with live.connection() as source,closing(sqlite3.connect(path.parent/'online-wal.sqlite3')) as destination:source.backup(destination)
    with closing(sqlite3.connect(path.parent/'online-wal.sqlite3')) as saved:assert sorted(saved.execute('select * from private_facts'))==sorted(facts)
live.merge_seed(REPO/'data/library.sqlite3',fingerprint='statement-integrity-delivery')
assert checksum(live.statement(identity))==custom_hash
assert live.find('private-import::A')
with live.connection() as db:assert sorted(tuple(r) for r in db.execute('select * from private_facts'))==sorted(facts)
assert live.find(url='https://qoj.ac/problem/14684')['id']=='luogu-training-P14450'
assert live.find(url='https://qoj.ac/problem/14688')['id']=='luogu-training-P14454'
# Validate public filtering using the current seed directly. The private edit
# above deliberately remains private, even while the public row is retired.
store=Store(data_file=ROOT/'upgrade-validation/no-import.md',data_root=ROOT/'upgrade-validation/imports',
    history_file=ROOT/'upgrade-validation/history.jsonl',library_file=path)
rows=[r for r in store.training_data()['rows'] if not r.get('catalogHidden')];visible={r['id'] for r in rows};assert not visible & retired_ids
assert not any(entry.get('problemId') in retired_ids for t in store.public_training_lists() for entry in t.get('problems',[]))
new=[r for r in rows if r.get('source')=='xcpc-qoj' and r.get('contestId')=='2562'];assert len(new)==11
assert all(r['platform']=='QOJ' and r['series']=='XCPC' and r['catalogReplayReady'] is False for r in new)
result={'preservedSyntheticPrivateFacts':len(facts),'privateStatementAndChinesePreserved':True,'privateImportPreserved':True,
    'onlineBackupIncludesCommittedWal':True,'verifiedSourceAliases':2,'publicRetirementsFiltered':len(retired_ids),
    'newQojFilteredRows':len(new),'newEventReplayDisabled':True,'visiblePublicRows':len(rows),'realPersonalDatabasesRead':0}
(ROOT/'evidence/upgrade-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps(result,ensure_ascii=False),flush=True)
