"""Stage and optionally install ONLY revised content for already shipped tasks.

The running application and personal databases are never opened. Use the
product's existing seed merge on next startup. Unrelated unpublished problems,
code changes and standalone courses are excluded from the installed seed.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase


def load(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,value):p.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def copy_database(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as original,sqlite3.connect(target) as copied:original.backup(copied)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();installation=args.installation.resolve()
    assert installation.is_relative_to(ROOT.parents[1]/'版本'/'最新版'),installation
    save=ROOT/'.backups'/('editorial-content-install-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    save.mkdir(parents=True)
    before=installation/'data/library.sqlite3'
    assert before.is_file()
    with sqlite3.connect(before.as_uri()+'?mode=ro',uri=True) as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert not tables.intersection({'submissions','training','drafts','documents'}),'Not a public seed'
    copy_database(before,save/'original.sqlite3')
    public=LibraryDatabase(save/'original.sqlite3',readonly=True)
    stage=public.export_source(save/'source')
    old_ids={r['id'] for r in load(stage/'problems.json')}
    old_defaults={r['problem_id'] for r in load(stage/'solutions.json')}
    old_details={r['problem_id'] for r in load(stage/'detailed_solutions.json')}
    for name,identities in [('solutions',old_defaults),('detailed_solutions',old_details)]:
        revised={r['problem_id']:r for r in load(ROOT/'data/library'/(name+'.json'))}
        assert identities.issubset(revised),'A shipped editorial is missing from the revised source'
        dump(stage/(name+'.json'),[revised[i] for i in sorted(identities)])
    old_lectures={r['id']:r for r in load(stage/'lectures.json')}
    new_lectures=[]
    for row in load(ROOT/'data/library/lectures.json'):
        if row['content'].get('conceptSource')!='independent-foundation':continue
        row['content']['sourceProblemIds']=[p for p in row['content']['sourceProblemIds'] if p in old_ids]
        new_lectures.append(row)
    lecture_ids=set(old_lectures)|{r['id'] for r in new_lectures}
    dump(stage/'lectures.json',list(old_lectures.values())+new_lectures)
    relationships=load(stage/'links.json');seen={(r['problem_id'],r['lecture_id']) for r in relationships}
    for row in load(ROOT/'data/library/links.json'):
        key=(row['problem_id'],row['lecture_id'])
        if row['problem_id'] in old_defaults and row['lecture_id'] in lecture_ids and key not in seen:
            relationships.append(row);seen.add(key)
    dump(stage/'links.json',relationships)
    meta=load(stage/'meta.json');meta['teachingRevision']='2026-10-22-foundations-v1'
    meta['revision']=str(int(meta.get('revision','0'))+1)
    audit=json.loads(meta.get('lectureAudit','{}'));audit.update(lectureCount=len(lecture_ids),normalizedLectureCount=len(lecture_ids),independentFoundationCount=len(new_lectures),teachingRevision=meta['teachingRevision'])
    meta['lectureAudit']=json.dumps(audit,ensure_ascii=False);dump(stage/'meta.json',meta)
    built=LibraryDatabase.from_source(stage,save/'revised.sqlite3')
    counts=built.check()
    assert counts['problems']==len(old_ids) and counts['solutions']==len(old_defaults)
    assert counts['detailed_solutions']==len(old_details)
    # Exercise the actual upgrade path with an existing local editorial edit.
    upgraded=LibraryDatabase(save/'upgrade-check.sqlite3')
    upgraded.merge_seed(save/'original.sqlite3')
    identity=next(i for i in old_defaults if i!='remote:nowcoder:141877::C')
    note='Personal editorial edit remains untouched.'
    with upgraded.connection() as db:db.execute('UPDATE solutions SET markdown=?,digest=? WHERE problem_id=?',(note,hashlib.sha256(note.encode()).hexdigest(),identity))
    upgraded.merge_seed(built.path)
    assert upgraded.solution(identity)['markdown']==note
    article=upgraded.solution('remote:nowcoder:141877::C','detailed')
    assert 'assets/foundations/interval-coverage.svg' in article['markdown']
    assert 'lower_bound' in article['markdown'] and 'lambda' in article['markdown']
    assert any(i=='lecture:foundation-lambda' for i,kind in upgraded.references('remote:nowcoder:141877::C'))
    report={'installation':str(installation),'counts':counts,'excludedUnshippedProblems':len(load(ROOT/'data/library/problems.json'))-len(old_ids),
            'upgradePreservedLocalEditorial':True,'personalDatabasesOpened':False,'applied':args.apply}
    if args.apply:
        # The entire changed artifact is the public seed, not a user library.
        copy_database(built.path,before)
        text_source=installation/'data/library'
        if text_source.is_dir():
            for name in ['solutions','detailed_solutions','lectures','links','meta']:
                target=text_source/(name+'.json')
                if target.exists():
                    backup=save/'installed-source'/target.name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup)
                shutil.copy2(stage/(name+'.json'),target)
        assert LibraryDatabase(before,readonly=True).check()==counts
    (save/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
