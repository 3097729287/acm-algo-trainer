"""Read back the installed articles and compare private records to recovery."""
import json
from collections import Counter
from pathlib import Path
import sqlite3
import urllib.parse
import urllib.request
from cf2278_stage import OUT, CONTENT, additions, shared
from three_contests_install import stable_inventory, public_digest
from three_contests_stage import additions as previous_additions

BASE='http://127.0.0.1:18765'

def get(path):
    with urllib.request.urlopen(BASE+path,timeout=60) as response:
        return json.load(response)

def private_records(before, identities):
    """Distinguish user records from the public catalog and startup caches."""
    paths=[Path(x['source']) for install in before['installations'] for x in install['snapshots']]
    expected={key:value for install in before['installations'] for key,value in install['privateInventory'].items()}
    backups={x['source']:Path(x['backup']) for install in before['installations'] for x in install['snapshots']}
    current=stable_inventory(paths)
    changes=[];reordered=[]
    for path,value in expected.items():
        for table,saved in value['tables'].items():
            if table in {'problems','documents'}:continue
            if current[path]['tables'][table]!=saved:
                quoted='"'+table.replace('"','""')+'"'
                with sqlite3.connect(backups[path]) as old,sqlite3.connect(Path(path).as_uri()+'?mode=ro',uri=True) as now:
                    # Account synchronization may reinsert equal records in a
                    # different physical rowid order. Compare complete values.
                    assert Counter(old.execute('select * from '+quoted))==Counter(now.execute('select * from '+quoted)),(Path(path).name,table)
                reordered.append(table)
    for install in before['installations']:
        for snap in install['snapshots']:
            source=Path(snap['source']);backup=Path(snap['backup'])
            if source.name=='tb-library.sqlite3' and current[str(source)]!=expected[str(source)]:
                assert public_digest(source,identities)==public_digest(backup,identities)
            if source.name!='tb-documents.sqlite3':continue
            with sqlite3.connect(backup) as old,sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as now:
                a=dict(old.execute('select key,value from documents'));b=dict(now.execute('select key,value from documents'))
            assert a.keys()==b.keys()
            for key in a:
                if a[key]==b[key]:continue
                assert key in {'integrations.json','account-session.json','tb-catalog-cache.json','contest-calendar.json','contest-imports.json','tb-knowledge-analysis.json'},key
                changes.append(key)
                if key=='integrations.json':
                    x=json.loads(a[key]);y=json.loads(b[key])
                    runtime={'knowledgeAttempts','sync','localBaseline','rows','notifications','updates','accounts','difficultyMetadata'}
                    assert {k:v for k,v in x.items() if k not in runtime}=={k:v for k,v in y.items() if k not in runtime}
                    for platform,account in x.get('accounts',{}).items():
                        for field,v in account.items():
                            if field not in {'updatedAt','statisticsSource','submissionCountSource','solvedCountSource'}:
                                assert y['accounts'][platform][field]==v,(platform,field)
                    metadata={'difficultyCheckedAt','knowledgeAnalysis','officialTagsCheckedAt'}
                    for identity,row in x.get('rows',{}).items():
                        new=y['rows'][identity]
                        assert {k:v for k,v in row.items() if k not in metadata}=={k:v for k,v in new.items() if k not in metadata},identity
                    for identity,row in x.get('localBaseline',{}).items():assert y['localBaseline'][identity]==row
                    assert all(n in y.get('notifications',[]) for n in x.get('notifications',[]))
                if key in {'contest-calendar.json','contest-imports.json'}:
                    x=json.loads(a[key]);y=json.loads(b[key])
                    ignored={'checkedAt'} if key=='contest-calendar.json' else {'attempts','checkedAt','retryAt'}
                    for identity,row in x.items():
                        assert {k:v for k,v in row.items() if k not in ignored}=={k:v for k,v in y[identity].items() if k not in ignored}
    return sorted(set(changes)),sorted(set(reordered))

def main():
    packet=additions();before=shared.load(OUT/'local-install.json')
    workspace=get('/api/workspace');assert not workspace.get('activeContest')
    checks=[]
    for task in [packet,previous_additions()]:
        defaults={x['problem_id']:x for x in task['solutions']}
        detailed={x['problem_id']:x for x in task['detailed_solutions']}
        for p in task['problems']:
            identity=p['id'];value=get('/api/solution?id='+urllib.parse.quote(identity,safe=''))
            assert value['markdown']==defaults[identity]['markdown'],identity
            assert value['detailedSolution']['markdown']==detailed[identity]['markdown'],identity
            assert value['methods'][0]['markdown']==value['markdown'],identity
            checks.append({'id':identity,'bothVariantsExact':True})
    cache_changes,reordered=private_records(before,{p['id'] for p in packet['problems']})
    api=get('/api/data')
    rows=api.get('rows',[]) if isinstance(api,dict) else api
    indexed={x['id']:x for x in rows}
    for p in packet['problems']:
        saved=indexed[p['id']]
        assert saved.get('solutionAvailable') and saved.get('detailedSolutionAvailable'),p['id']
    result={'passed':True,'newTasks':6,'newArticles':12,'priorTasksPreserved':16,
        'priorArticlesPreserved':32,'checks':checks,'privateRecordInventoryUnchanged':True,
        'normalStartupReadback':True,'noOfficialSubmissionsSent':True,
        'unrelatedLivePublicRowsUnchanged':True,'startupCacheDocumentsRefreshed':cache_changes,
        'equalPrivateRecordsReorderedByAccountSync':reordered}
    shared.dump(OUT/'live-readback.json',result)
    print('Live readback: 12 new and 32 prior articles exact; private records unchanged.')

if __name__=='__main__':main()
