"""Merge explicit, disjoint editorial review packages into public content.

Dry run by default. Review status is a separate human decision; neither merging
nor numeric/render checks automatically labels an article as taught.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET

from revise_editorial_reasoning import ROOT, SOURCE, SAVE, backup
from audit_editorial_reasoning import reference_programs


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def dumped(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')


def prepare(paths):
    files={name:SOURCE/(name+'.json') for name in ['solutions','detailed_solutions','meta']}
    before={name:path.read_bytes() for name,path in files.items()}
    rows={name:json.loads(value) for name,value in before.items()}
    indexes={name:{row['problem_id']:row for row in rows[name]} for name in ['solutions','detailed_solutions']}
    changed=[];seen={};batches=[];new_images=0;preserved=0
    for path in paths:
        package=load(path);batches.append(package['batch'])
        for entry in package['problems']:
            identity=entry['problemId']
            if identity in seen:raise ValueError(f'{identity} occurs in both {seen[identity]} and {path.name}')
            seen[identity]=path.name
            if set(entry['variants'])!={'solutions','detailed_solutions'}:raise ValueError('Both variants required: '+identity)
            if not entry.get('reviewNotes') or not entry.get('validation'):raise ValueError('Missing review evidence: '+identity)
            for variant,proposed in entry['variants'].items():
                current=indexes[variant][identity]
                old_text=current['markdown'];new_text=proposed['markdown']
                if digest(old_text) not in [proposed['beforeMarkdownSha256'],digest(new_text)]:
                    raise ValueError('Source changed since review: '+variant+' '+identity)
                if reference_programs(old_text)!=reference_programs(new_text):
                    raise ValueError('Verified reference program changed: '+identity)
                if current['markdown'].count('<!-- reusable-foundations:start -->')!=new_text.count('<!-- reusable-foundations:start -->'):
                    raise ValueError('Foundation blocks changed unexpectedly: '+identity)
                for key,data in current['images'].items():
                    if proposed['images'].get(key)!=data:raise ValueError('Existing image lost/changed: '+identity+' '+key)
                for key,data in proposed['images'].items():
                    if key in current['images']:continue
                    if key.startswith(('/', '\\')) or re.match(r'^[a-zA-Z]:',key):raise ValueError('Absolute image key: '+key)
                    if not data.startswith('data:image/'):raise ValueError('New images must be portable: '+key)
                    raw=base64.b64decode(data.split(',',1)[1],validate=True)
                    if data.startswith('data:image/svg+xml;base64,'):
                        ET.fromstring(raw)
                    if not any(key in v['markdown'] for v in entry['variants'].values()):raise ValueError('Unreferenced new figure: '+identity+' '+key)
                    new_images+=1
                if old_text!=new_text or current['images']!=proposed['images']:
                    current.update(markdown=new_text,images=proposed['images'])
                    changed.append({'problemId':identity,'variant':variant,'beforeSha256':digest(old_text),'afterSha256':digest(new_text)})
                preserved+=1
    if changed:
        rows['meta']['editorialReasoningRevision']='2026-10-22-reviewed-batches-v1'
        existing=set(json.loads(rows['meta'].get('editorialReasoningBatches','["nowcoder141877"]')))
        rows['meta']['editorialReasoningBatches']=json.dumps(sorted(existing|set(batches)),ensure_ascii=False)
        rows['meta']['revision']=str(int(rows['meta'].get('revision','0'))+1)
    return files,before,rows,dict(packages=batches,reviewedPackageProblems=len(seen),changedArticles=changed,
                                  newImageMappings=new_images,preservedProgramArticles=preserved)


def apply(files,before,rows):
    for name,path in files.items():
        if path.read_bytes()!=before[name]:raise ValueError('Concurrent source edit: '+str(path))
        backup(path)
    try:
        for name,path in files.items():
            path.write_bytes(dumped(rows[name]))
        sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
        from library import LibraryDatabase
        staged=LibraryDatabase.from_source(SOURCE,SAVE/'merged-public.sqlite3')
        counts=staged.check()
        target=ROOT/'data/library.sqlite3'
        # These files contain public educational content only. No personal DB
        # or installed application is opened during this operation.
        with sqlite3.connect(staged.path.as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(target) as dest:
            source.backup(dest)
        return counts
    except BaseException:
        for name,path in files.items():path.write_bytes(before[name])
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages',nargs='+',type=Path)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    paths=[p.resolve() for p in args.packages]
    assert all(p.is_relative_to(ROOT/'data/editorial-revisions') for p in paths)
    files,before,rows,report=prepare(paths)
    report['dryRun']=not args.write
    if args.write:
        report['counts']=apply(files,before,rows)
        SAVE.mkdir(parents=True,exist_ok=True)
        (SAVE/'merge-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({**report,'changedArticles':len(report['changedArticles'])},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
