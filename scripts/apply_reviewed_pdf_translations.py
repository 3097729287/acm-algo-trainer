"""Apply page-reviewed PDF transcriptions with exact source and resource binding."""
import base64,copy,datetime,hashlib,json,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_seed import checksum,load_statements
from statement_resources import inspect_resource
from translation import TRANSLATION_FORMAT,bundled_translation

def main():
 folder=ROOT/'content-updates/20261108-pdf-translations';current={row['problem_id']:row['content'] for row in load_statements(ROOT/'data/library')}
 stage=ROOT/'.backups/complete-20261108/pdfs';audit=[]
 for chinese in sorted(folder.glob('*.zh.md')):
  slug=chinese.name[:-6];contest,letter=slug.split('-');identity=f'remote:codeforces:{contest}::{letter}'
  english=(folder/(slug+'.en.md')).read_text('utf8');translated=chinese.read_text('utf8')
  target=ROOT/f'data/library/statement-patches/zzzzzzzzz-20261108-pdf-{slug}.json'
  if target.exists():
   stored=json.loads(target.read_text('utf8'))['statements'][0];assert current[identity]==stored['content']
   assert stored['content']['sourceText']==english and stored['content']['translation']['markdown']==translated,'Reviewed files changed; author a guarded follow-up patch: '+identity
   continue
  before=current[identity];value=copy.deepcopy(before)
  pdf=stage/f'remote-codeforces-{contest}--{letter}'/'original.pdf';digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
  assert digest==value['statementPdf']['sha256'];assert value.get('samples')
  old_text=value.get('sourceText','');value.setdefault('sourceTextArchive',[]).append({'sha256':hashlib.sha256(old_text.encode()).hexdigest(),'text':old_text,'kind':'unreviewed-pdf-extraction'})
  value['sourceText']=english
  proof={'schema':1,'method':'page-by-page-original-pdf-review','pdfSha256':digest,'pages':value['statementPdf']['pageCount'],'sourceTextSha256':hashlib.sha256(english.encode()).hexdigest(),'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'samplesRetainedSeparately':True}
  value['sourceTextReview']=proof
  expected_samples=before['samples']
  sample_file=folder/(slug+'.samples.json')
  if sample_file.exists():
   correction=json.loads(sample_file.read_text('utf8'))
   assert 1<=correction['sourcePage']<=proof['pages'] and correction['reason']
   expected_samples=correction['samples'];assert len(expected_samples)==len(before['samples'])
   value.setdefault('sampleExtractionHistory',[]).append({'samples':before['samples'],'extraction':before.get('sampleExtraction')})
   value['samples']=expected_samples
   value['sampleExtraction']={'method':'page-reviewed-original-pdf','sourcePdfSha256':digest,'page':correction['sourcePage'],'reason':correction['reason']}
   proof['sampleInputsCorrected']=True
  history={key:value[key] for key in ['translationReview','translationNotice','translationAvailable'] if key in value}
  value.setdefault('translationReviewHistory',[]).append(history)
  value.pop('translationNotice',None);value['translationAvailable']=True
  value['translation']={'kind':'bundled','provider':'逐页核对原始 PDF 的预置中文译文','format':TRANSLATION_FORMAT,'sourceHash':hashlib.sha256(value['markdown'].encode()).hexdigest(),'sourceLanguage':'en','targetLanguage':'zh-CN','inputKind':'pdf-text','sourceTextHash':hashlib.sha256(english.encode()).hexdigest(),'sourcePdfSha256':digest,'markdown':translated}
  for name in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',translated):
   image=folder/name;assert image.is_file();data=image.read_bytes();entry=inspect_resource(data,value.get('sourcePdfUrl') or value['url'],'image')
   entry.update(derivedFromPdfSha256=digest,kind='reviewed-original-diagram')
   value.setdefault('images',{})[name]='data:'+entry['mime']+';base64,'+base64.b64encode(data).decode('ascii')
   value.setdefault('resourceManifest',{})[name]=entry
  assert bundled_translation(value) is not None,'Protected text validation failed: '+identity
  value['translationReview']={**proof,'status':'complete','immutableSpansValidated':True}
  assert value['samples']==expected_samples and value['statementPdf']==before['statementPdf'] and value['markdown']==before['markdown']
  packet={'schema':1,'statements':[{'problem_id':identity,'beforeSha256':checksum(before),'content':value}]}
  target.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  audit.append({'id':identity,'pdfSha256':digest,'pagesReviewed':proof['pages'],'samples':len(value['samples']),'formulaProtection':True})
 report=folder/'review.json';previous=json.loads(report.read_text('utf8')) if report.exists() else []
 report.write_text(json.dumps(previous+audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'newTranslations':len(audit),'totalReviewed':len(previous)+len(audit),'problems':[row['id'] for row in audit]}),flush=True)

if __name__=='__main__':main()
