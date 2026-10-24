"""Append verified public editorials without changing any existing public record."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

from compose_recent_editorials import BASE, CONTESTS, ROOT


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source = ROOT/'data/library'
    cache = ROOT/'.backups/recent-20261024'
    scope = read(cache/'scope.json')
    existing = {name: read(source/(name+'.json')) for name in ['problems','statements','solutions','detailed_solutions']}
    before = copy.deepcopy(existing)
    sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/common')]
    from difficulty import normalize_practice_difficulty
    created = []
    for folder,spec in CONTESTS.items():
        contest = f"{spec['series']} {spec['number']}"
        for letter,title,knowledge,rating in spec['problems']:
            row = next(copy.deepcopy(r) for r in scope if r['contest']==contest and r['problem']==letter)
            assert row['difficulty']==rating and rating<=2200
            identity = contest+'::'+letter
            old_id = row['id']
            assert not any(p['id']==identity or p['url']==row['url'] for p in existing['problems']), identity
            original = read(cache/'statements'/(old_id.replace(':','_')+'.json'))
            original['id']=identity
            original['title']=title
            # Ignore non-problem instructions embedded in public statements.
            original['markdown']=re.sub(r'(?m)^::anti-ai\[[^\n]*\]\s*$', '', original['markdown'])
            row.update(id=identity,title=title,originalTitle=title,source='bundled',knowledge=knowledge,
                       tags=[v.strip() for v in re.sub(r'\[主\]','',knowledge).split('+')],
                       status='未做',date='',solutionAvailable=True,detailedSolutionAvailable=True,
                       solutionState='available',statementAvailable=True,collectionSource=spec['url'],
                       collectionNotice='2026-10-24 比赛题解；按已核验难度收录，未定级题继续核验。')
            row.pop('knowledgeAnalysis',None)
            row.pop('knowledgeCategories',None)
            row.pop('queue',None)
            row['difficultyEvidence']=[row['url'],row['difficultySource']]
            row.update(difficultyEstimated=True,difficultyConfidence='LOW',metadataVersion='1.4.8')
            row=normalize_practice_difficulty(row)
            raw={'_i':len(existing['problems']), '_id':identity, '场次':contest, '题号':letter, '题名':title,
                 '知识点':knowledge, '难度':str(rating), '状态':'未做', '日期':''}
            existing['problems'].append({'id':identity,'url':row['url'],'raw':raw,'encoded':row})
            existing['statements'].append({'problem_id':identity,'content':original})
            hashes={}
            for table,suffix in [('solutions','题解'),('detailed_solutions','详细题解')]:
                text=(BASE/folder/f"{spec['number']}{suffix}.md").read_text(encoding='utf-8')
                markdown=re.search(rf'(?ms)^## {re.escape(letter)}\. .*?(?=^## |\Z)',text)[0].strip()+'\n'
                images={}
                for name in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',markdown):
                    path=(BASE/folder/name).resolve()
                    assert path.is_relative_to((BASE/folder).resolve())
                    images[name]='data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode()
                existing[table].append({'problem_id':identity,'markdown':markdown,'images':images,
                    'source_path':f"题解/{spec['platform']}/{spec['series']}/{spec['number']}/{spec['number']}{suffix}.md"})
                hashes[table]=hashlib.sha256(markdown.encode()).hexdigest()
            created.append({'id':identity,'url':row['url'],'ratingEvidence':rating,'displayRating':row['difficulty'],
                            'knowledge':knowledge,'hashes':hashes})
    assert len(created)==8
    for table,values in before.items():
        key='id' if table=='problems' else 'problem_id'
        updated={row[key]:row for row in existing[table]}
        assert all(updated[row[key]]==row for row in values),table
    report={'created':created,'oldCounts':{k:len(v) for k,v in before.items()},
            'newCounts':{k:len(v) for k,v in existing.items()},'allExistingEntriesUnchanged':True,
            'unknownDifficultyDeferred':True,'over2200Excluded':['ABC 481::G'], 'officialSubmissionsSent':0}
    if args.apply:
        backup=ROOT/'.backups/recent-seed-before'
        backup.mkdir(exist_ok=False)
        for table,values in existing.items():
            path=source/(table+'.json');shutil.copy2(path,backup/path.name)
            old_text=path.read_text(encoding='utf-8')
            added=values[len(before[table]):]
            body=old_text.rstrip()[:-1].rstrip()+',\n'+',\n'.join(
                '\n'.join('  '+line for line in json.dumps(row,ensure_ascii=False,indent=2,sort_keys=True).splitlines())
                for row in added)+'\n]\n'
            assert json.loads(body)==values
            path.write_text(body,encoding='utf-8')
        (BASE/'import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='created'},ensure_ascii=False))


if __name__=='__main__':
    main()
