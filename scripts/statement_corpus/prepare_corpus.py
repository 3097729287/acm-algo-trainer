import os
"""Reconcile collected original statements with the delivered public seed."""
import base64,collections,datetime,hashlib,io,json,re,sqlite3,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from statement_cleanup import clean_statement
from statement_integrity import annotate_type,statement_type,valid_samples
from statement_resources import archive_resources,inspect_resource,resource_references
from statement_seed import checksum
from statement_asset_store import dehydrate
from statement_quality import has_body,japanese_only
STAMP=datetime.datetime.now(datetime.timezone.utc).isoformat()
RESOURCE={}
for name in ['resource-results.jsonl','resource-alternatives.jsonl']:
    file=ROOT/'evidence'/name
    if file.exists():
        for line in file.read_text('utf8').splitlines():
            row=json.loads(line)
            if row.get('result')=='verified':RESOURCE[row.get('originalUrl') or row['url']]=row
ATTEMPTS=[]
for name in ['attempts.jsonl','resource-attempts.jsonl','alternative-attempts.jsonl']:
    file=ROOT/'evidence'/name
    if file.exists():ATTEMPTS.extend(json.loads(x) for x in file.read_text('utf8').splitlines())
BYURL=collections.defaultdict(list)
for a in ATTEMPTS:BYURL[a['url']].append(a)
import statement_resources as R
_original_inspect=R.inspect_resource
_verified={}
for entry in RESOURCE.values():
    _verified[(entry['sha256'],entry['kind'])]={key:entry[key] for key in ('sha256','bytes','mime','pageCount','frameCount','width','height') if key in entry}
def inspect_resource(data,url,kind):
    key=(hashlib.sha256(data).hexdigest(),kind)
    if key not in _verified:_verified[key]=_original_inspect(data,url,kind)
    result=dict(_verified[key],sourceUrl=url)
    if kind=='image' and result['mime']=='application/pdf':raise ValueError('An image destination returned a PDF')
    if urlsplit(url).path.lower().endswith('.gif') and result['mime']!='image/gif':raise ValueError('A GIF destination did not return original GIF bytes')
    return result
R.inspect_resource=inspect_resource

class Resources:
    def __init__(self,sources):
        self.sources={a['url']:a for a in sources}
    def bytes(self,url,headers=None):
        if url in RESOURCE:
            item=RESOURCE[url];data=(ROOT/'resources'/item['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==item['sha256']
            return data
        if url in self.sources:
            item=self.sources[url];data=(ROOT/'raw'/item['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==item['sha256']
            return data
        raise ValueError('Original resource not verified: '+url)

def canonical_body(value):
    text=value or ''
    text=re.sub(r'(?s)\A#{12,}\s*\n.*?\n#{12,}\s*\n','',text,count=1)
    text=re.sub(r'(?m)^# [^\n]*\n','',text,count=1)
    text=re.sub(r'(?m)^Time limit:[^\n]*\n','',text)
    text=re.split(r'\n={12,}\s*\n官方样例\s*\n={12,}',text,maxsplit=1)[0]
    text=re.sub(r'(?m)^Score\s*:\s*\$*\d+\$*\s*points\s*$','',text)
    # CF's original $$$...$$$ and the old archive's $...$ carry the same TeX.
    # Ignore only delimiter/emphasis spelling; every prose/math token survives.
    text=text.replace('$','').replace('**','')
    return re.sub(r'\s+','',text)

def canonical_prose(value):
    text=value or ''
    text=re.sub(r'(?s)\A#{12,}\s*\n.*?\n#{12,}\s*\n','',text,count=1)
    text=re.sub(r'(?m)^# [^\n]*\n','',text,count=1)
    text=re.sub(r'(?m)^Time limit:[^\n]*\n','',text)
    text=re.split(r'\n={12,}\s*\n官方样例\s*\n={12,}',text,maxsplit=1)[0]
    text=re.sub(r'(?m)^Score\s*:\s*\$*\d+\$*\s*points\s*$','',text)
    text=re.sub(r'!\[[^\]]*\]\([^\n]*?\)','',text)
    text=re.sub(r'(?<!!)\[([^\]]+)\]\([^\s)]*\)',r'\1',text)
    maths=[]
    def protect(m):
        formula=m[2]
        for source,target in [(r'\leq','≤'),(r'\le','≤'),(r'\geq','≥'),(r'\ge','≥'),(r'\lt','<'),(r'\gt','>'),(r'\neq','≠')]:
            formula=re.sub(re.escape(source)+r'(?![A-Za-z])',lambda _:target,formula)
        formula=re.sub(r'\\(?:left|right)\b','',formula)
        formula=re.sub(r'\\(?:texttt|mathrm|text)\{([^{}]*)\}',r'\1',formula)
        formula=re.sub(r'_\{([A-Za-z0-9])\}',r'_\1',formula)
        maths.append(re.sub(r'\s+','',formula));return 'TBMATHTOKEN'+str(len(maths)-1)+'END'
    text=re.sub(r'(?<![\\$])(\${1,3})(?!\$)(.*?)(?<!\\)\1(?!\$)',protect,text,flags=re.S)
    lines=text.splitlines();output=[];table=False;fenced=False
    for i,line in enumerate(lines):
        if re.match(r'^\s*`{3,}',line):fenced=not fenced;continue
        if not fenced:
            if re.match(r'^#{1,6}\s+',line):continue
            if re.fullmatch(r'\s*(?:题目描述|输入描述|输出描述|输入格式|输出格式|说明|备注|提示|样例|示例)\s*[:：]?\s*',line):continue
            if re.fullmatch(r'\s*\|[ :|\-]+\|\s*',line):table=True;continue
            if line.lstrip().startswith('|') and (table or i+1<len(lines) and re.fullmatch(r'\s*\|[ :|\-]+\|\s*',lines[i+1])):
                line=re.sub(r'(?<!\\)\|','',line)
            else:table=False
            line=line.replace('**','')
            line=re.sub(r'(?<![\w\\])\*(?=\S)([^*\n]+?)\*(?!\w)',r'\1',line)
            line=line.replace('`','')
        output.append(line)
    text=re.sub(r'\s+','','\n'.join(output))
    for i,math in enumerate(maths):text=text.replace('TBMATHTOKEN'+str(i)+'END',math)
    return text

def source_supplement(old_body,new_body):
    additions=[]
    for table in re.finditer(r'(?m)^\|[^\n]*\|\n\|[ :|\-]+\|\n(?:\|[^\n]*\|(?:\n|$))+',new_body):
        if table[0].strip() not in old_body:additions.append(table[0].strip())
    for block in re.finditer(r'(?ms)^(`{3,})[^\n]*\n.*?^\1\s*$',new_body):
        if block[0].strip() not in old_body:additions.append(block[0].strip())
    old_images=set(re.findall(r'!\[[^\]]*\]\([^\n]*?\)',old_body))
    for match in re.finditer(r'!\[[^\]]*\]\([^\n]*?\)',new_body):
        if match[0] not in old_images and not any(match[0] in part for part in additions):additions.append(match[0])
    return '\n\n'.join(additions)

def preserve(old,new):
    result={**old,**new}; old_body=old.get('markdown') or '';new_body=new.get('markdown') or ''
    same=canonical_body(old_body)==canonical_body(new_body) or bool(old.get('sourcePdfSha256') and old.get('sourcePdfSha256')==new.get('sourcePdfSha256'))
    samples_equal=True
    if old.get('samples') and new.get('samples'):
        pairs=lambda v:[(s['input'].replace('\r\n','\n').rstrip('\n'),s['output'].replace('\r\n','\n').rstrip('\n')) for s in v]
        samples_equal=pairs(old['samples'])==pairs(new['samples'])
        if same:same=samples_equal
    equivalent=bool(old_body and samples_equal and canonical_prose(old_body)==canonical_prose(new_body))
    if not same and equivalent and old.get('translation'):
        result['currentSourceMarkdown']=new_body
        result['statementSupplement']=source_supplement(old_body,new_body)
        result['formattingEvidence']={'archiveSha256':hashlib.sha256(old_body.encode()).hexdigest(),
            'currentSha256':hashlib.sha256(new_body.encode()).hexdigest(),'comparison':'all-prose-and-math-tokens-v1'}
        result['markdown']=old_body
        same=True
    if same and old_body:result['markdown']=old_body
    # Preserve a previously delivered English original when a site's default
    # endpoint now returns Japanese/site Chinese. Both site snapshots remain.
    old_translation=old.get('translation');incoming=new.get('translation')
    if old_translation:
        # The delivered translation remains authenticated against its exact
        # delivered original. Latest original rendering is a separate snapshot;
        # never manufacture a new translation hash for changed source prose.
        if old_body and old_body!=new_body:
            result['markdown']=old_body
            result['currentSourceMarkdown']=new_body
            result['statementSupplement']=source_supplement(old_body,new_body)
            result['translationSourceSnapshot']={'sourceHash':hashlib.sha256(old_body.encode()).hexdigest(),
                'currentSourceHash':hashlib.sha256(new_body.encode()).hexdigest(),
                'equivalentFormattingVerified':equivalent or same,'samplesUnchanged':samples_equal}
            result['translation']=old_translation
            same=True
        if same or old_body==new_body:
            result['translation']=old_translation
        elif not incoming:
            # Keep the exact old language switch on the unchanged archive body.
            # A genuinely changed source cannot authenticate a stale translation.
            result.pop('translation',None)
        if result.get('translation')!=old_translation:
            archived=list(old.get('archivedTranslations') or [])
            item=dict(old_translation,sourceMarkdown=old_body)
            if item not in archived:archived.append(item)
            result['archivedTranslations']=archived
    images=dict(old.get('images') or {})
    for name,data in (new.get('images') or {}).items():
        if name in images and images[name]!=data and str(images[name]).startswith('data:'):
            result.setdefault('archivedImages',{})[name+'#'+hashlib.sha256(images[name].encode()).hexdigest()[:16]]=images[name]
        images[name]=data
    result['images']=images
    return result

def add_pdf(value,client):
    source=value.get('sourcePdfUrl') or value.get('sourcePdf')
    if not source:return value
    if value.get('statementPdf'):return value
    data=client.bytes(source);entry=inspect_resource(data,source,'attachment')
    displayed=data
    if value.get('sourcePageNumbers'):
        from pypdf import PdfReader,PdfWriter
        reader=PdfReader(io.BytesIO(data));writer=PdfWriter()
        for index in value['sourcePageNumbers']:writer.add_page(reader.pages[index-1])
        output=io.BytesIO();writer.write(output);displayed=output.getvalue()
    view_info=inspect_resource(displayed,source,'attachment')
    value['statementPdf']=dict(view_info,data='data:application/pdf;base64,'+base64.b64encode(displayed).decode(),
        sourceSha256=entry['sha256'],sourcePageNumbers=value.get('sourcePageNumbers'))
    value.setdefault('attachments',{})[source]=dict(entry,data='data:application/pdf;base64,'+base64.b64encode(data).decode(),fileName='statement.pdf')
    return value

def main():
    db=sqlite3.connect(ROOT/'baseline.sqlite3');db.row_factory=sqlite3.Row
    inventory=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'))
    indexed={r['id']:r for r in inventory}
    out=ROOT/'prepared';out.mkdir(exist_ok=True)
    summary=collections.Counter();audit=[];pending=[];patches=[]
    source_rows=[]
    assets={};asset_dir=ROOT/'statement-assets-packed';asset_dir.mkdir(exist_ok=True)
    pack_file=None;pack_size=0;pack_number=0;pack_hash=None;parts=[]
    def close_pack():
        nonlocal pack_file
        if pack_file:
            pack_file.close();parts.append({'file':f'statement-assets/part-{pack_number:04}.bin','bytes':pack_size,'sha256':pack_hash.hexdigest()});pack_file=None
    def save_asset(sha,mime,data):
        nonlocal pack_file,pack_size,pack_number,pack_hash
        if sha not in assets:
            if pack_file is None or pack_size+len(data)>16*1024*1024:
                close_pack();pack_number+=1;pack_size=0;pack_hash=hashlib.sha256();pack_file=(asset_dir/f'part-{pack_number:04}.bin').open('wb')
            assets[sha]={'sha256':sha,'mime':mime,'bytes':len(data),'file':f'statement-assets/part-{pack_number:04}.bin','offset':pack_size}
            pack_file.write(data);pack_hash.update(data);pack_size+=len(data)
    for raw in db.execute('select p.*,s.content from problems p left join statements s on p.id=s.problem_id order by p.id'):
        identity=raw['id'];old=json.loads(raw['content']) if raw['content'] else {};row=indexed[identity]
        path=ROOT/'parsed'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
        packet=json.loads(path.read_text('utf8')) if path.exists() else None
        sources=packet.get('sources',[]) if packet else [];issues=[]
        for source in sources:
            if not source.get('file') or hashlib.sha256((ROOT/'raw'/source['file']).read_bytes()).hexdigest()!=source['sha256']:
                issues.append('source-evidence-mismatch')
        value=clean_statement(preserve(old,packet['statement']) if packet else dict(old)) if old or packet else {}
        if value:
            value['id']=identity;value['url']=raw['url'];value=annotate_type(value)
            client=Resources(sources)
            try:add_pdf(value,client)
            except Exception as e:issues.append('original-pdf-unavailable')
            value=archive_resources(value,client)
            issues.extend('resource:'+x['url'] for x in value['resourceIssues'])
            rendered=value.get('currentSourceMarkdown') or value.get('markdown')
            if not has_body(rendered):issues.append('missing-prose')
            if japanese_only(rendered):issues.append('japanese-only')
            if not valid_samples(value):issues.append('malformed-samples')
            if packet is None and raw['url']:issues.append('current-source-unverified')
            if packet and raw['url'] and 'luogu.com.cn' in raw['url'] and not packet.get('binding'):
                for source in sources:
                    if source['url']!=raw['url']:continue
                    try:origin=json.loads((ROOT/'raw'/source['file']).read_text('utf8'))['data']['problem'].get('content') or {}
                    except Exception:continue
                    if value.get('problemType')=='standard' and any(re.fullmatch(r'\s*[01]\s*',str(origin.get(k) or '')) for k in ('formatI','formatO')):
                        issues.append('source-io-placeholder-requires-review')
            pdf=value.get('statementPdf') or {}
            if pdf:
                data=base64.b64decode(pdf['data'].split(',',1)[1],validate=True)
                inspected=inspect_resource(data,pdf.get('sourceUrl') or raw['url'],'attachment')
                if inspected['pageCount']!=pdf['pageCount']:issues.append('pdf-page-count')
                if not value.get('samples'):value['localJudgeSupported']=False
            # Source zero samples is a legitimate inventory, not missing examples.
            evidence={'schema':1,'status':'incomplete' if issues else 'complete','sourceVerified':bool(packet) or not raw['url'],
                'sampleCount':len(value.get('samples') or []),'checkedAt':STAMP,'pdfPageCountVerified':bool(pdf),
            'markdownSha256':hashlib.sha256((value.get('currentSourceMarkdown') or value.get('markdown') or '').encode()).hexdigest(),
                'sourceDocuments':[{'url':s['url'],'sha256':s['sha256']} for s in sources],'issues':issues}
            value['integrity']=evidence
            if packet and packet.get('binding'):value['sourceBinding']=packet['binding']
            portable=dehydrate(value,save_asset)
            if value!=old:patches.append({'problem_id':identity,'beforeSha256':checksum(old or None),'content':portable})
            target=out/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
            if '--individual-output' in sys.argv:target.write_text(json.dumps(portable,ensure_ascii=False),'utf8')
            summary['stored']+=1;summary['samples']+=len(value.get('samples') or [])
            summary['pdf_statements']+=bool(pdf);summary['special_types']+=statement_type(value)!='standard'
            summary['complete']+=not issues;summary['incomplete']+=bool(issues)
            summary['new_statements']+=not old
            if old.get('translation'):
                summary['old_translations']+=1
                summary['active_translations_preserved']+=value.get('translation')==old.get('translation')
                summary['translations_archived']+=value.get('translation')!=old.get('translation')
        else:issues.append('no-statement')
        entry={'id':identity,'url':raw['url'],'title':row['title'],'status':'unresolved' if issues else 'complete',
            'issues':issues,'samples':len(value.get('samples') or []),'problemType':statement_type(value) if value else None,
            'sourceDocuments':[{'url':s['url'],'sha256':s['sha256']} for s in sources],
            'resourceCount':len(value.get('resourceManifest') or {}),'pdfPageCount':(value.get('statementPdf') or {}).get('pageCount'),
            'markdownSha256':hashlib.sha256((value.get('currentSourceMarkdown') or value.get('markdown') or '').encode()).hexdigest() if value else None}
        audit.append(entry)
        if issues:pending.append(entry)
        summary['total']+=1
        if summary['total']%500==0:print({'processed':summary['total'],'assets':len(assets),'bytesInCurrentPart':pack_size},flush=True)
    (ROOT/'evidence/prepared-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
    (ROOT/'statement_assets.json').write_text(json.dumps([assets[k] for k in sorted(assets)],ensure_ascii=False,indent=2),'utf8')
    close_pack()
    (ROOT/'statement_asset_parts.json').write_text(json.dumps(parts,indent=2),'utf8')
    (ROOT/'evidence/audit-after.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in audit),'utf8')
    (ROOT/'evidence/unresolved.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2),'utf8')
    # Patches are emitted in bounded shards, without changing any educational
    # table or using a live/personal database as a destination.
    folder=ROOT/'statement-patches';folder.mkdir(exist_ok=True)
    part=[];size=0;number=0
    written=[]
    def flush():
        nonlocal number,part,size
        if not part:return
        number+=1;file=folder/f'part-{number:04}.json';file.write_text(json.dumps({'schema':1,'statements':part},ensure_ascii=False,indent=2,sort_keys=True),'utf8');written.append({'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'statements':len(part)})
        part=[];size=0
    for p in patches:
        length=len(json.dumps(p,ensure_ascii=False).encode())
        if size+length>12*1024*1024:flush()
        part.append(p);size+=length
    flush()
    (ROOT/'statement_patch_manifest.json').write_text(json.dumps(written,indent=2),'utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
