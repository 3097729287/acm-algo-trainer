import os
"""Assemble only this isolated checkout; the installed program is read-only."""
import collections,hashlib,json,re,shutil,sqlite3,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from library import LibraryDatabase
from statement_integrity import native_submission_supported
from statement_seed import checksum
SOURCE=REPO/'data/library'
backup=REPO/'.backups/statement-integrity/public-source';backup.mkdir(parents=True,exist_ok=True)
for file in SOURCE.glob('*.json'):
    if not (backup/file.name).exists():shutil.copy2(file,backup/file.name)
baseline=LibraryDatabase(ROOT/'baseline.sqlite3',readonly=True)
baseline.export_source(SOURCE)
patches=json.loads((ROOT/'statement_patch_manifest.json').read_text('utf8'))
folder=SOURCE/'statement-patches';folder.mkdir(exist_ok=True)
for item in patches:
    assert re.fullmatch(r'part-\d{4}\.json',item['file'])
    source=ROOT/'statement-patches'/item['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
    shutil.copy2(source,folder/item['file'])
asset_folder=SOURCE/'statement-assets';asset_folder.mkdir(exist_ok=True)
parts=json.loads((ROOT/'statement_asset_parts.json').read_text('utf8'))
for part in parts:
    name=part['file'].split('/')[-1];assert re.fullmatch(r'part-\d{4}\.bin',name)
    source=ROOT/'statement-assets-packed'/name
    assert source.stat().st_size==part['bytes'] and hashlib.sha256(source.read_bytes()).hexdigest()==part['sha256']
    shutil.copy2(source,asset_folder/name)
for name in ['statement_assets.json','statement_asset_parts.json']:shutil.copy2(ROOT/name,SOURCE/name)
audits=[json.loads(x) for x in (ROOT/'evidence/audit-after.jsonl').read_text('utf8').splitlines()]
by_id={a['id']:a for a in audits};problems=json.loads((SOURCE/'problems.json').read_text('utf8'));retired=[]
for problem in problems:
    a=by_id[problem['id']];encoded=problem['encoded'];kind=a.get('problemType') or encoded.get('problemType','standard')
    supported=native_submission_supported(problem.get('url'))
    ready=a['status']=='complete'
    encoded.update(problemType=kind,catalogStatementReady=ready,catalogReplayReady=ready and supported and kind not in {'communication','output-only','attachment'})
    if not ready:
        encoded['statementPriorVisibility']={k:encoded[k] for k in ('catalogHidden','catalogNotice','catalogVisibilityPolicy') if k in encoded}
        encoded.update(statementRetired=True,statementRetirementPolicy='public-statement-audit-v1',
            statementRetirementReason='公开题面与样例尚未就绪，暂不加入题库；个人训练与历史记录保留',catalogHidden=True)
        retired.append(dict(a,reasonCodes=a['issues'],temporary=True,historyRetained=True))
(SOURCE/'problems.json').write_text(json.dumps(problems,ensure_ascii=False,indent=2,sort_keys=True),'utf8',newline='\n')
docs=REPO/'docs/statement-integrity-20261030';docs.mkdir(exist_ok=True)
for name in ['inventory-summary.json','prepared-summary.json','audit-after.jsonl','inventory.json']:
    shutil.copy2(ROOT/'evidence'/name,docs/name)
(docs/'retired.json').write_text(json.dumps(retired,ensure_ascii=False,indent=2),'utf8')
# Public evidence includes source URL/status/hash, not response HTML, cookies,
# login sessions, private records, or machine paths.
for name in ['attempts.jsonl','resource-results.jsonl','resource-alternatives.jsonl','alternative-attempts.jsonl']:
    path=ROOT/'evidence'/name
    if path.exists():shutil.copy2(path,docs/name)
print(json.dumps({'publicProblems':len(problems),'temporaryRetirements':len(retired),'statementShards':len(patches),'assetParts':len(parts)},ensure_ascii=False),flush=True)
