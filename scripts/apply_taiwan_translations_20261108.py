"""Apply page-reviewed PDF translations with exact samples and original diagrams."""
import copy
import argparse
import base64
import datetime
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_seed import checksum,load_statements
from statement_resources import inspect_resource
from translation import TRANSLATION_FORMAT,bundled_translation


def reviewed_figures(folder, proof, original, english, chinese):
    figures=proof.get('figures',[])
    names=[entry['file'] for entry in figures]
    assert len(names)==len(set(names))
    for text in (english,chinese):
        assert set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text))==set(names)
    images={};manifest={}
    for figure in figures:
        name=figure['file']
        assert Path(name).name==name and figure['page'] in proof['pagesReviewed']
        raw=(folder/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==figure['sha256']
        entry=inspect_resource(raw,original['statementPdf']['sourceUrl'],'image')
        entry.update(derivedFromPdfSha256=proof['pdfSha256'],kind='reviewed-original-diagram',
                     sourcePage=figure['page'],clipRect=figure['clipRect'])
        images[name]='data:'+entry['mime']+';base64,'+base64.b64encode(raw).decode('ascii')
        manifest[name]=entry
    return images,manifest


def main(folder=None,contest='105544',review_file='review.json',packet_prefix='zzzzzzzzzzz-20261108-taiwan'):
    folder=folder or ROOT/'content-updates/20261108-taiwan'
    assert re.fullmatch(r'\d{1,10}',contest) and re.fullmatch(r'z+-[A-Za-z0-9-]+',packet_prefix)
    assert re.fullmatch(r'[A-Za-z0-9-]+\.json',review_file)
    reviewed=json.loads((folder/review_file).read_text('utf8'))
    current={r['problem_id']:r['content'] for r in load_statements(ROOT/'data/library')}
    result=[]
    for proof in reviewed:
        letter=proof['letter'];assert re.fullmatch(r'[A-Z][0-9]?',letter)
        identity=proof.get('problemId') or 'remote:codeforces:'+contest+'::'+letter
        assert identity in current
        if proof.get('problemId'):
            assert current[identity]['url']=='https://codeforces.com/gym/'+contest+'/problem/'+letter
        slug=contest+'-'+letter
        english=(folder/(slug+'.en.md')).read_text('utf8')
        chinese=(folder/(slug+'.zh.md')).read_text('utf8')
        sample_file=folder/(slug+'.samples.json')
        if not sample_file.exists():sample_file=folder/(letter+'.samples.json')
        sample_record=json.loads(sample_file.read_text('utf8'))
        assert sample_record['sourcePdfSha256']==proof['pdfSha256']
        assert proof['pagesReviewed']==list(range(1,proof['pageCount']+1))
        assert (sample_record.get('page') in proof['pagesReviewed'] if 'page' in sample_record else all(page in proof.get('sourcePageNumbers',[]) for page in sample_record['pages']))
        for i,sample in enumerate(sample_record['samples'],1):
            for language,text in [('en',english),('zh',chinese)]:
                assert '```text\n'+sample['input']+'\n```' in text,(identity,language,i,'input')
                assert '```text\n'+sample['output']+'\n```' in text,(identity,language,i,'output')
        images,manifest=reviewed_figures(folder,proof,current[identity],english,chinese)
        target=ROOT/('data/library/statement-patches/'+packet_prefix+'-'+letter+'.json')
        if target.exists():
            stored=json.loads(target.read_text('utf8'))['statements'][0]['content']
            assert current[identity]==stored
            assert stored['sourceText']==english and stored['translation']['markdown']==chinese
            assert stored['samples']==sample_record['samples']
            assert all(stored.get('images',{}).get(name)==value for name,value in images.items())
            assert all(stored.get('resourceManifest',{}).get(name)==value for name,value in manifest.items())
            assert bundled_translation(stored)
            continue
        before=current[identity];value=copy.deepcopy(before)
        assert before['statementPdf']['sha256']==proof['pdfSha256']
        assert before['statementPdf']['pageCount']==proof['pageCount']
        if 'sourcePageNumbers' in proof:
            assert before['statementPdf']['sourcePageNumbers']==proof['sourcePageNumbers']
        assert not before.get('translation')
        value.setdefault('sourceTextArchive',[]).append({'text':before.get('sourceText',''),'kind':'unreviewed-pdf-extraction','sha256':hashlib.sha256(before.get('sourceText','').encode()).hexdigest()})
        value.setdefault('sampleExtractionHistory',[]).append({'samples':before['samples'],'extraction':before.get('sampleExtraction')})
        value['sourceText']=english
        value['samples']=sample_record['samples']
        value['sampleExtraction']={k:v for k,v in sample_record.items() if k!='samples'}
        value['sourceTextReview']={**proof,'method':'page-by-page-original-pdf-review','sourceTextSha256':hashlib.sha256(english.encode()).hexdigest()}
        value['translationAvailable']=True
        if images:
            value.setdefault('images',{}).update(images)
            value.setdefault('resourceManifest',{}).update(manifest)
        value['translation']={'kind':'bundled','provider':'逐页核对原始 PDF 的预置中文译文','format':TRANSLATION_FORMAT,
            'sourceHash':hashlib.sha256(value['markdown'].encode()).hexdigest(),'sourceLanguage':'en','targetLanguage':'zh-CN',
            'inputKind':'pdf-text','sourceTextHash':hashlib.sha256(english.encode()).hexdigest(),
            'sourcePdfSha256':proof['pdfSha256'],'markdown':chinese}
        assert bundled_translation(value),identity+' failed complete immutable-span validation'
        value['translationReview']={**value['sourceTextReview'],'status':'complete','immutableSpansValidated':True}
        assert value['markdown']==before['markdown'] and value['statementPdf']==before['statementPdf']
        packet={'schema':1,'statements':[{'problem_id':identity,'beforeSha256':checksum(before),'content':value}]}
        target.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        result.append(identity)
    print(json.dumps({'newTranslations':len(result),'reviewedTotal':len(reviewed),'problems':result},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',type=Path);parser.add_argument('--contest',default='105544')
    parser.add_argument('--review-file',default='review.json');parser.add_argument('--packet-prefix',default='zzzzzzzzzzz-20261108-taiwan')
    args=parser.parse_args();main(args.folder.resolve(strict=True) if args.folder else None,args.contest,args.review_file,args.packet_prefix)
