"""Apply six page-reviewed translations and exact native sample corrections."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_seed import checksum,load_statements
from translation import TRANSLATION_FORMAT,bundled_translation


def main():
    folder=ROOT/'content-updates/20261108-taiwan'
    reviewed=json.loads((folder/'review.json').read_text('utf8'))
    current={r['problem_id']:r['content'] for r in load_statements(ROOT/'data/library')}
    result=[]
    for proof in reviewed:
        letter=proof['letter'];identity='remote:codeforces:105544::'+letter
        slug='105544-'+letter
        english=(folder/(slug+'.en.md')).read_text('utf8')
        chinese=(folder/(slug+'.zh.md')).read_text('utf8')
        sample_record=json.loads((folder/(slug+'.samples.json')).read_text('utf8'))
        assert sample_record['sourcePdfSha256']==proof['pdfSha256']
        assert proof['pagesReviewed']==list(range(1,proof['pageCount']+1))
        assert sample_record['page'] in proof['pagesReviewed']
        for i,sample in enumerate(sample_record['samples'],1):
            for language,text in [('en',english),('zh',chinese)]:
                assert '```text\n'+sample['input']+'\n```' in text,(identity,language,i,'input')
                assert '```text\n'+sample['output']+'\n```' in text,(identity,language,i,'output')
        target=ROOT/('data/library/statement-patches/zzzzzzzzzzz-20261108-taiwan-'+letter+'.json')
        if target.exists():
            stored=json.loads(target.read_text('utf8'))['statements'][0]['content']
            assert current[identity]==stored
            assert stored['sourceText']==english and stored['translation']['markdown']==chinese
            assert stored['samples']==sample_record['samples']
            assert bundled_translation(stored)
            continue
        before=current[identity];value=copy.deepcopy(before)
        assert before['statementPdf']['sha256']==proof['pdfSha256']
        assert before['statementPdf']['pageCount']==proof['pageCount']
        assert not before.get('translation')
        value.setdefault('sourceTextArchive',[]).append({'text':before.get('sourceText',''),'kind':'unreviewed-pdf-extraction','sha256':hashlib.sha256(before.get('sourceText','').encode()).hexdigest()})
        value.setdefault('sampleExtractionHistory',[]).append({'samples':before['samples'],'extraction':before.get('sampleExtraction')})
        value['sourceText']=english
        value['samples']=sample_record['samples']
        value['sampleExtraction']={k:v for k,v in sample_record.items() if k!='samples'}
        value['sourceTextReview']={**proof,'method':'page-by-page-original-pdf-review','sourceTextSha256':hashlib.sha256(english.encode()).hexdigest()}
        value['translationAvailable']=True
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


if __name__=='__main__':main()
