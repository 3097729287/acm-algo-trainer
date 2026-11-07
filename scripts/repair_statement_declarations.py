"""Repair only array/string declarations proven reversed against their original.

The exact original and all immutable spans stay unchanged. No title matching,
translation provider, personal database, or guessed mathematical roles are used.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_cleanup import clean_statement,clean_statement_markdown
from statement_seed import checksum,load_statements
from translation import bundled_translation

from translation_roles import repair


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'data/library')
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--patch-name',default='zzzz-20261107-declarations.json')
    parser.add_argument('--check-only',action='store_true',help='Write only the audit, without exporting a source patch')
    args=parser.parse_args();patches=[];audit=[]
    for row in load_statements(args.source):
        old=row['content'];value=clean_statement(dict(old,translation=None));translation=old.get('translation') or {}
        if translation.get('kind')!='bundled' or not translation.get('markdown'):continue
        corrected,changes=repair(value.get('markdown') or '',clean_statement_markdown(translation['markdown']))
        if not changes:continue
        incoming=dict(old,translation=dict(translation,markdown=corrected))
        if not bundled_translation(clean_statement(incoming)):raise ValueError('Immutable-span validation failed: '+row['problem_id'])
        patches.append({'problem_id':row['problem_id'],'beforeSha256':checksum(old),'content':incoming})
        audit.append({'id':row['problem_id'],'url':value.get('url'),'sourceHash':translation.get('sourceHash'),'changes':changes})
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if patches and not args.check_only:
        folder=args.source/'statement-patches';folder.mkdir(exist_ok=True)
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.json',args.patch_name):raise ValueError('Invalid patch filename')
        destination=folder/args.patch_name
        if destination.exists():raise ValueError('Use a fresh authoring checkout')
        destination.write_text(json.dumps({'schema':1,'statements':patches},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'correctedStatements':len(patches),'correctedDeclarations':sum(len(row['changes']) for row in audit)}))

if __name__=='__main__':main()
