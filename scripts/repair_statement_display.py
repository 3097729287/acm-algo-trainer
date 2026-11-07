"""Apply reviewed public display repairs, preserving original source snapshots.

The supplied report must come from statement-corpus.mjs over both languages.
Only unreadable originals with a successfully rendered existing Chinese source
are promoted. Two exact source-format defects have explicit, checked repairs.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_seed import checksum,load_statements
from statement_cleanup import clean_statement


def run(review,output):
    if output.exists():raise ValueError('Repair already exported; rebase against its preceding seed before rerunning')
    spec=importlib.util.spec_from_file_location('corpus',ROOT/'scripts/translate_public_library.py')
    corpus=importlib.util.module_from_spec(spec);spec.loader.exec_module(corpus)
    issues=json.loads(review.read_text('utf8'))['issues'];bad={r['id'] for r in issues}
    rows={r['problem_id']:r['content'] for r in load_statements(ROOT/'data/library')}
    changes=[];audit=[]
    for identity in sorted(bad):
        if '\t' in identity:continue
        old=rows[identity];value=deepcopy(old);original=old.get('markdown') or '';reason=None
        translation=old.get('translation') or {}
        if identity=='nowcoder-global::24870':
            # This statement has monetary amounts, and no TeX formula. Keep
            # currency dollars literal in both the source and bound translation.
            value['markdown']=re.sub(r'(?<!\\)\$(?=\d)',r'\\$',original)
            target=re.sub(r'(?<!\\)\$(?=\d)',r'\\$',translation['markdown'])
            value['translation']=corpus.bind(value,clean_statement(value)['markdown'],'markdown','en',target,translation.get('provider','原有中文译文'))
            reason='Escape literal currency dollars; retain all original amounts and prose'
        elif identity=='nowcoder-global::15666':
            before=r'\begin{array} \\F';after=r'\begin{array}{ll} F'
            if original.count(before)!=1:raise ValueError('Piecewise source changed')
            value['markdown']=original.replace(before,after)
            reason='Restore missing array column specification in the unchanged piecewise recurrence'
        elif translation.get('markdown') and identity+'\tzh' not in bad:
            value['markdown']=translation['markdown'];value.pop('translation',None)
            value.setdefault('archivedTranslations',[]).append(dict(translation,sourceMarkdown=original))
            value.pop('currentSourceMarkdown',None);value['statementLanguage']='zh'
            value['statementSource']=translation.get('provider','原有完整中文题面')
            reason='Use successfully rendered existing Chinese source; retain malformed original snapshot'
        else:
            raise ValueError('No reviewed readable replacement: '+identity)
        value.setdefault('sourceSnapshots',[]).append({'markdown':original,'url':old.get('url'),'reason':reason})
        integrity=value.setdefault('integrity',{})
        integrity['markdownSha256']=corpus.sha(value['markdown'])
        if integrity.get('corpusAuditVerifiedSha256'):integrity['corpusAuditVerifiedSha256']=corpus.sha(value['markdown'])
        integrity['displayRepair']=reason
        changes.append({'problem_id':identity,'beforeSha256':checksum(old),'content':value})
        audit.append({'id':identity,'url':old.get('url'),'reason':reason,'beforeSha256':corpus.sha(original),'afterSha256':corpus.sha(value['markdown'])})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'schema':1,'statements':changes},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (ROOT/'docs/statement-repairs-20261107/display-repairs.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'displayRepairs':len(changes)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.review,args.output)
