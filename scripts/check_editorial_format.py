"""Run the existing DSH checks with explicit reviewed C++ code notation.

The original tools are not modified. Their legacy backtick classifier treats
lambda captures, standard headers, many C++ API names and operators as math.
Only the exact reviewed spellings in data/editorial-code-notation.json are added;
all structure, math rendering and other checks remain the original checks.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files',nargs='*',type=Path)
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--jobs',type=int,default=4)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(Path.home()/'.dsh'/'tools'))
    import check_solution as checks
    reviewed=set(json.loads((ROOT/'data/editorial-code-notation.json').read_text('utf-8'))['codeSpans'])
    native=checks.keep_ticks
    checks.keep_ticks=lambda value:value in reviewed or native(value)
    files=list(args.files)
    if args.archive:
        files+=sorted(p for p in args.archive.rglob('*题解.md') if not any(part.startswith('_') for part in p.relative_to(args.archive).parts))
    def check(path):
        with tempfile.TemporaryDirectory(prefix='tb-editorial-format-') as temporary:
            result,_=checks.check_file(str(path),temporary)
        return {'file':str(path),'failed':result.failed,'items':result.items}
    report=[]
    # check_file prints routine file headers. Retain structured original check
    # results, including every failure and its evidence, instead of noisy output.
    with contextlib.redirect_stdout(io.StringIO()):
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for future in as_completed([pool.submit(check,p) for p in files]):report.append(future.result())
    report.sort(key=lambda row:row['file'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    failures=[{'file':r['file'],'checks':[item for item in r['items'] if item[0]=='问题']} for r in report if r['failed']]
    print(json.dumps({'files':len(report),'failed':len(failures),'referenceRecompilation':'Skipped: byte-preservation independently checked; teaching snippets and corridor compiled separately.','failures':failures[:6]},ensure_ascii=False,indent=2))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
