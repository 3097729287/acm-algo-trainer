"""Prove the exact code-only normalization of historically reviewed Markdown.

Old review hashes and extracted lesson snapshots remain untouched. The pinned
formatter independently compares Markdown prose/structure and lexical tokens.
Any later rewrite remains unaccepted by this mechanical lineage.
"""
import argparse,base64,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/library'
def load(path):return json.loads(path.read_text('utf8'))
def sha(text):return hashlib.sha256(text.encode('utf8')).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--formatters',type=Path,required=True)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    commit=subprocess.check_output(['git','rev-parse',args.source_commit],cwd=ROOT,text=True).strip()
    current={name:{row['problem_id']:row for row in load(SOURCE/(name+'.json'))} for name in ['solutions','detailed_solutions']}
    wanted={}
    def add(table,identity,digest):
        row=current[table].get(identity)
        if row and sha(row['markdown'])!=digest:wanted[(table,identity,digest)]=row['markdown']
    for item in load(ROOT/'backend/resources/metadata-review-1423.json')['estimated']:
        if item.get('sourceKind') not in ['published-editorial','published-reference','self-reviewed-statement']:
            add('solutions',item['id'],item['editorialSha256'])
    for item in load(ROOT/'backend/resources/metadata-review-1430.json')['foundationEditorials']:
        for table in current:add(table,item['id'],item['articles'][table]['markdownSha256'])
    for rule in load(ROOT/'backend/resources/knowledge_topic_review.json')['problems'].values():
        for item in rule.get('sources',[]):
            for table in current:
                prefix='data/library/'+table+'.json#'
                if item.get('reference','').startswith(prefix):add(table,item['reference'][len(prefix):],item['sha256'])
    reasoning={item['problemId']:item for item in load(ROOT/'data/editorial-reasoning-review.json')['problems']}
    for row in load(SOURCE/'lectures.json'):
        lesson=row['content']
        if lesson.get('conceptSource')=='reviewed-editorial-extraction':
            identity=lesson['sourceProblemIds'][0]
            if lesson['sourceMarkdown'] not in current['detailed_solutions'][identity]['markdown']:
                add('detailed_solutions',identity,reasoning[identity]['variants']['detailed_solutions']['markdownSha256'])
    before={table:{row['problem_id']:row for row in json.loads(subprocess.check_output(['git','show',commit+':data/library/'+table+'.json'],cwd=ROOT))} for table in current}
    docs={}
    for (table,identity,digest),markdown in wanted.items():
        original=before[table][identity]['markdown']
        assert sha(original)==digest,(table,identity,'Historical snapshot does not match its review')
        docs[digest]=original
    args.work.mkdir(parents=True,exist_ok=True)
    input_file=args.work/'input.json';output_file=args.work/'formatted.json'
    assert not input_file.exists() and not output_file.exists()
    input_file.write_text(json.dumps([{'id':digest,'markdown':value} for digest,value in docs.items()],ensure_ascii=False),encoding='utf8')
    subprocess.run(['node',str(ROOT/'frontend/scripts/standardize-editorial-code.mjs'),str(input_file.resolve()),str(output_file.resolve()),str(args.formatters.resolve())],cwd=ROOT,check=True)
    formatted=load(output_file);report=formatted['report']
    assert not report['failures'] and not report['issues'] and report['proseAndStructurePreserved']
    after={row['id']:sha(row['markdown']) for row in formatted['documents']}
    revisions=[];needs_review=[];presentation_additions=0
    for (table,identity,digest),markdown in wanted.items():
        entry={'table':table,'problemId':identity,'beforeSha256':digest,'formattedSha256':after[digest]}
        if sha(markdown)!=after[digest]:
            pattern=r'\n<!-- tb-motion:([a-z0-9-]+):start -->\n\n!\[([^\]\n]+)\]\((assets/editorial-motion/[a-z0-9.-]+\.svg)\)\n\n<!-- tb-motion:\1:end -->\n'
            additions=list(re.finditer(pattern,markdown))
            unchanged=re.sub(pattern,'',markdown)
            previous=before[table][identity]['images'];images=current[table][identity]['images']
            if additions and sha(unchanged)==after[digest] and all(images.get(key)==value for key,value in previous.items()):
                reviewed_images=[]
                for addition in additions:
                    key=addition[3];value=images[key]
                    assert value.startswith('data:image/svg+xml;base64,')
                    data=base64.b64decode(value.split(',',1)[1],validate=True);ET.fromstring(data)
                    reviewed_images.append({'key':key,'sha256':hashlib.sha256(data).hexdigest()})
                entry.update(presentationSha256=sha(markdown),presentationOnly=True,codeAndExistingProseUnchanged=True,addedImages=reviewed_images)
                presentation_additions+=1
            else:needs_review.append({'table':table,'problemId':identity,'beforeSha256':digest,'formattedSha256':after[digest],'currentSha256':sha(markdown)})
        revisions.append(entry)
    proof={'schema':1,'sourceCommit':commit,'proseAndStructurePreserved':True,'formatterFailures':report['failures'],'formatterIssues':report['issues'],'formatterManifestSha256':hashlib.sha256((ROOT/'backend/resources/code-formatters.json').read_bytes()).hexdigest(),'documents':len(docs),'revisions':revisions,'additionalRewritesRequiringReview':needs_review}
    target=ROOT/'data/editorial-evidence-format-20261108.json' if args.write else args.work/'proof.json'
    assert not target.exists()
    target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'provedDocuments':len(docs),'references':len(revisions),'presentationOnlyAdditions':presentation_additions,'additionalRewrites':needs_review},ensure_ascii=False))

if __name__=='__main__':main()
