"""Compare default-template edits against independent legacy/native journals."""
from contextlib import closing
from pathlib import Path
import argparse,hashlib,json,os,sqlite3,sys,tempfile,uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
os.environ['TB_OFFLINE']='1'
import initial_code
from native_parity import LegacyState
from native_run_parity import Native
from training import ServiceError


def normalized(value):
    if isinstance(value,dict):return {key:normalized(item) for key,item in value.items() if key not in {'revision','updatedAt','createdAt'}}
    if isinstance(value,list):return [normalized(item) for item in value]
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();checks=[]
    with tempfile.TemporaryDirectory(prefix='ToBe-native-defaults-') as directory:
        state=Path(directory);native=Native(args.native,state/'native','unused','unused')
        with closing(sqlite3.connect(state/'native/personal.sqlite3')) as source,closing(sqlite3.connect(state/'legacy.sqlite3')) as target:source.backup(target)
        legacy=LegacyState(state/'legacy.sqlite3')
        try:
            assert native.call('initial-code')==initial_code.catalog(legacy);checks.append('default-revisions-and-complete-initial-catalogue')
            for language,code in [('cpp17','// 中文\nint main() {}'),('python3','')]:
                body={'id':'default','title':'默认','language':language,'code':code,'revision':''}
                actual=native.call('initial-code/save',body);expected=initial_code.save(legacy,body)
                assert normalized(actual)==normalized(expected)
                assert actual['template']['revision'] and expected['template']['revision']
                assert actual['template']['id']=='default' and actual['template']['customized'] is True
                assert native.call('initial-code')['revisions']=={'cpp17':'','python3':''}
                checks.append('edit-'+language+'-without-changing-language-selection')
            for change,status in [({'revision':'stale'},409),({'title':'renamed'},400),({'delete':True},400),({'code':'\0'},400),({'code':'界'*21846},400)]:
                a=native.call('initial-code');b=initial_code.catalog(legacy)
                actual_body={'id':'default','title':'默认','language':'cpp17','code':'changed','revision':a['templates'][0]['revision'],**change}
                expected_body={**actual_body,'revision':b['templates'][0]['revision']}
                if 'revision' in change:expected_body['revision']=change['revision']
                native.process.stdin.write(json.dumps({'version':1,'id':uuid.uuid4().hex,'method':'POST','path':'initial-code/save','query':{},'body':actual_body,'token':native.token,'owner':native.owner},ensure_ascii=False)+'\n');native.process.stdin.flush()
                response=native.responses.get(timeout=15);assert not response['ok'] and response['error']['status']==status
                try:initial_code.save(legacy,expected_body)
                except ServiceError as error:assert error.status==status
                else:raise AssertionError('Legacy accepted invalid default mutation')
                assert native.call('initial-code')==a and initial_code.catalog(legacy)==b
                checks.append('rejected-'+next(iter(change))+'-'+str(status))
            expected=normalized(initial_code.catalog(legacy));native.close();native=Native(args.native,state/'native','unused','unused')
            assert normalized(native.call('initial-code'))==expected;checks.append('defaults-persist-through-process-restart')
        finally:legacy.connection.close();native.close()
    report={'ok':True,'checks':checks,'nativeSha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),'independentJournals':True,'livePrivateStateOpened':False,'pythonRuntimeFallback':False}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report))


if __name__=='__main__':main()
