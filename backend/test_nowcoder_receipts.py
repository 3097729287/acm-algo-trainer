"""Production observer with intercepted requests; no real account submissions."""
import json
from pathlib import Path
import subprocess
import unittest
from test_official_v4 import NODE

SCRIPT = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const observer=fs.readFileSync(process.argv[1],'utf8');
const messages=[],location=new URL('https://ac.nowcoder.com/acm/contest/127263/B');
const ctx={sessionId:'fixture',platform:'牛客',originalUrl:location.href,code:'int main(){}'};
let responses=[];
const window={pageInfo:{contestId:'127263',questionId:'11604979'},globalInfo:{ownerId:12345},fetch:async(url)=>{
 const value=responses.shift();return {ok:true,url:new URL(url,location).href,json:async()=>value,clone(){return {json:async()=>value}}};
}};
const box={window,location,URL,URLSearchParams,Promise,AbortSignal,chrome:{webview:{postMessage(value){messages.push(JSON.parse(value))}}},normal:text=>({'答案错误':'WA','运行超时':'TLE','AC':'AC'}[text]||null)};
vm.runInNewContext(observer+';window.state=installNowcoderReceipts('+JSON.stringify(ctx)+');',box);
window.state.armed=true;
async function request(url,body,response){responses.push(response);await window.fetch(url,{method:body?'POST':'GET',...(body?{body:JSON.stringify(body)}:{})});await new Promise(r=>setImmediate(r));}
const body={questionId:'11604979',content:ctx.code,submitType:1,userId:12345,appId:1,tagId:1};
(async()=>{
 // Old result, another task/code/account and self-test never become acceptance.
 await request('/status?submissionId=12',null,{code:0,data:{status:5}});
 for(const changed of [{questionId:'other'},{content:'other code'},{submitType:2},{userId:999},{selfInputData:'1'}]){
  await request('/api/service/judge/submit',{...body,...changed},{code:0,data:{id:12}});
 }
 assert.equal(messages.length,0);
 await request('/api/service/judge/submit',body,{code:0,data:{id:21}});
 assert.equal(messages.at(-1).status,'judging');
 const query='/api/service/judge/submit-status?id=21&submitType=1&userId=12345&appId=1&tagId=1';
 for(const url of [query.replace('id=21','id=20'),query.replace('submitType=1','submitType=2'),query.replace('userId=12345','userId=999')])await request(url,null,{code:0,data:{status:5}});
 await request(query,null,{code:0,data:{status:1,desc:'AC'}});
 assert.equal(messages.length,1);
 await request(query,null,{code:0,data:{status:4,desc:'答案错误',memo:'答案正确 AC'}});
 assert.equal(messages.at(-1).verdict,'WA');
 await request(query,null,{code:0,data:{status:5}});
 assert.equal(messages.at(-1).verdict,'AC');assert.equal(messages.at(-1).submissionId,'21');
 window.state.pending=null;
 await request('/submit_cd',{questionId:'11604979',content:ctx.code},{code:0,data:22});
 await request('/status?submissionId=22',null,{code:0,data:{status:5}});
 assert.equal(messages.at(-1).submissionId,'22');
 // Current production terminal uses the cross-origin Victorinox judge API.
 window.state.pending=null;
 const production='https://victorinox.nowcoder.com';
 await request(production+'/api/service/judge/submit',{...body,appId:6,tagId:4,token:'page-only-token'},{code:0,data:31});
 assert.equal(messages.at(-1).submissionId,'31');
 const count=messages.length;
 await request('/api/service/judge/submit-status?id=31&submitType=1&userId=12345&appId=6&tagId=4',null,{code:0,data:{status:5}});
 await request('https://victorinox.nowcoder.com.evil.test/api/service/judge/submit-status?id=31',null,{code:0,data:{status:5}});
 assert.equal(messages.length,count,'receipt must come from the submitted-to production origin');
 // Desktop polling uses the confirmed ID and metadata, with no second POST.
 responses.push({code:0,data:{status:5}});await window.state.poll();
 assert.equal(messages.at(-1).verdict,'AC');assert.equal(messages.at(-1).submissionId,'31');
 assert.ok(!JSON.stringify(messages).includes('page-only-token'));
 // Early status may race ahead of the submit response, on that same origin.
 window.state.pending=null;
 await request(production+'/api/service/judge/submit-status?id=32&submitType=1&userId=12345&appId=6&tagId=4',null,{code:0,data:{status:5}});
 await request(production+'/api/service/judge/submit',{...body,appId:6,tagId:4},{code:0,data:32});
 assert.equal(messages.at(-1).verdict,'AC');assert.equal(messages.at(-1).submissionId,'32');
 await request(production+'/api/service/judge/submit',body,{code:1125,msg:'验证码错误'});
 assert.equal(messages.at(-1).status,'needs_verification');assert.equal(messages.at(-1).attempted,false);
 console.log(JSON.stringify({ok:true,legacy:true,modern:true,crossOriginProduction:true,hostPolling:true,rejectedOldOtherTaskCodeOwnerAndSelfTest:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
'''


class NowcoderReceiptTests(unittest.TestCase):
    def test_global_target_keeps_original_identity_without_a_contest(self):
        from official_bridge import submission_target
        url='https://ac.nowcoder.com/acm/problem/16570'
        target=submission_target(url)
        self.assertEqual((target['url'],target['originalUrl'],target['problem'],target['platform']),(url,url,'16570','牛客'))
        self.assertNotIn('contestId',target)
        for invalid in ('http://ac.nowcoder.com/acm/problem/16570','https://ac.nowcoder.com/acm/problem/0',
                        'https://ac.nowcoder.com/acm/problem/016570','https://ac.nowcoder.com/acm/problem/16570/submit',
                        url+'?contestId=123',url+'#submit','https://ac.nowcoder.com.evil.test/acm/problem/16570',
                        'https://user@ac.nowcoder.com/acm/problem/16570','https://ac.nowcoder.com:8443/acm/problem/16570'):
            with self.subTest(url=invalid),self.assertRaises(ValueError):submission_target(invalid)

    def test_passive_global_receipt_keeps_configured_owner_and_exact_url_guards(self):
        import datetime as dt
        from types import SimpleNamespace
        from official_sync import OfficialSync
        from training import ServiceError
        snapshot=lambda:{'settings':{'accounts':{'nowcoder':'12345'}}}
        server=SimpleNamespace(store=SimpleNamespace(extensions=SimpleNamespace(client=None,snapshot=snapshot)))
        sync=OfficialSync(server,fetch=lambda _:None)
        accepted=[]
        def capture(rows):accepted.extend(rows);return len(rows)
        sync.import_receipts=capture
        row=dict(submissionId='101',url='https://ac.nowcoder.com/acm/problem/16570',verdict='AC',acceptedAt=dt.datetime.now(dt.timezone.utc).isoformat())
        self.assertEqual(sync.from_browser(dict(platform='牛客',owner='12345',records=[row]))['imported'],1)
        self.assertEqual(accepted[-1]['url'],row['url'])
        with self.assertRaises(ServiceError):sync.from_browser(dict(platform='牛客',owner='999',records=[row]))
        for url in ('https://ac.nowcoder.com.evil.test/acm/problem/16570','https://ac.nowcoder.com/acm/problem/0','https://ac.nowcoder.com/acm/problem/16570/submit-list'):
            self.assertEqual(sync.from_browser(dict(platform='牛客',owner='12345',records=[dict(row,url=url)]))['imported'],0)

    def test_original_request_and_status_correlation(self):
        result = subprocess.run([NODE, '-e', SCRIPT, str(Path(__file__).parents[1]/'desktop/official_nowcoder.js')],
                                capture_output=True, text=True, encoding='utf-8', timeout=15, check=True)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_global_native_request_is_bound_to_real_question_and_signed_in_owner(self):
        result = subprocess.run([NODE, '-e', GLOBAL_SCRIPT, str(Path(__file__).parents[1]/'desktop/official_nowcoder.js')],
                                capture_output=True, text=True, encoding='utf-8', timeout=15, check=True)
        proof=json.loads(result.stdout)
        self.assertTrue(proof['ok'])
        self.assertGreaterEqual(proof['rejectedRequests'], 20)


GLOBAL_SCRIPT = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[1],'utf8'), code='int main(){}';
function fixture({ctxChanges={},infoChanges={},owner=12345,loggedIn=true,path='/acm/problem/16570'}={}){
 const messages=[],requests=[],responses=[],location=new URL('https://ac.nowcoder.com'+path);
 const ctx={sessionId:'global-fixture',platform:'牛客',originalUrl:'https://ac.nowcoder.com/acm/problem/16570',code,baseline:['99'],...ctxChanges};
 const window={isLogin:loggedIn,pageInfo:{problemId:'16570',questionId:'170283',doneQuestionId:'16570',tagId:'4',subTagId:'0',codeJudgeType:'0',...infoChanges},globalInfo:owner?{ownerId:owner}:{},fetch:async(url,options)=>{
  requests.push({url:String(url),method:options?.method||'GET',body:options?.body});
  const item=responses.shift()||{};return{ok:true,url:item.url||new URL(url,location).href,json:async()=>item.value,clone(){return{json:async()=>item.value}}};
 }};
 const box={window,location,URL,URLSearchParams,Promise,AbortSignal,chrome:{webview:{postMessage(value){messages.push(JSON.parse(value))}}},normal:text=>({'答案错误':'WA','运行超时':'TLE','AC':'AC'}[text]||null)};
 vm.runInNewContext(source+';window.state=installNowcoderReceipts('+JSON.stringify(ctx)+');',box);
 window.state.armed=true;
 return{window,ctx,messages,requests,location,responses,async request(url,body,value,responseUrl){responses.push({value,url:responseUrl});await window.fetch(url,{method:body?'POST':'GET',...(body?{body:new URLSearchParams(body).toString()}:{})});await new Promise(r=>setImmediate(r));}};
}
const legacy={questionId:'170283',doneQuestionId:'16570',tagId:'4',subTagId:'0',language:'2',languageName:'C++(g++ 13)',content:code};
const modern={questionId:'170283',tagId:'4',appId:6,userId:12345,language:2,content:code,submitType:1,token:'fixture-short-lived'};
const status=id=>'/nccommon/status?submissionId='+id+'&tagId=4&subTagId=0';
(async()=>{
 let rejected=0;
 const invalid=[
  {body:{questionId:'170284'}},{body:{doneQuestionId:'16571'}},{body:{problemId:'16571'}},{body:{tagId:'5'}},{body:{subTagId:'1'}},
  {body:{content:'other code'}},{body:{selfType:8}},{body:{selfInputData:'1'}},{body:{input:'1'}},{body:{isSelfTest:true}},{body:{language:undefined}},
  {options:{owner:null}},{options:{loggedIn:false}},{options:{path:'/acm/problem/16571'}},{options:{infoChanges:{problemId:'16571'}}},
  {options:{infoChanges:{doneQuestionId:'16571'}}},{options:{infoChanges:{contestId:'16570'}}},{options:{infoChanges:{teamId:54321}}},
  {options:{infoChanges:{questionId:'170284'}}},{options:{infoChanges:{codeJudgeType:1}}},
  {target:'https://ac.nowcoder.com.evil.test/nccommon/submit_cd'},
  {responseUrl:'https://victorinox.nowcoder.com/nccommon/submit_cd'},
  {responseUrl:'https://ac.nowcoder.com/other-result'},
 ];
 for(const test of invalid){const f=fixture(test.options);await f.request(test.target||'/nccommon/submit_cd',{...legacy,...test.body},{code:0,data:{submissionId:101}},test.responseUrl);assert.equal(f.messages.length,0,JSON.stringify(test));rejected++;}
 const unarmed=fixture();unarmed.window.state.armed=false;await unarmed.request('/nccommon/submit_cd',legacy,{code:0,data:101});assert.equal(unarmed.messages.length,0);rejected++;
 const old=fixture();await old.request('/nccommon/submit_cd',legacy,{code:0,data:98});assert.equal(old.messages.length,0);rejected++;
 const f=fixture();assert.equal(f.window.state.pageMatches(),true);assert.equal(f.window.state.hasLegacyApi(),false,'global uses native control, not synthesized legacy API');
 await f.request('/nccommon/submit_cd',legacy,{code:0,data:{submissionId:101}});
 assert.equal(f.messages.at(-1).status,'judging');assert.equal(f.messages.at(-1).submissionId,'101');
 for(const target of [status(100),status(101).replace('tagId=4','tagId=5'),status(101).replace('subTagId=0','subTagId=1'),'https://victorinox.nowcoder.com'+status(101)])await f.request(target,null,{code:0,data:{status:5}});
 for(const data of [{status:1,desc:'AC'},{status:5,questionId:170284},{status:5,problemId:16571},{status:5,ownerId:999},{status:5,userId:999},{status:5,isSelfTest:'1'},{status:'5'}])await f.request(status(101),null,{code:0,data});
 assert.equal(f.messages.length,1,'stale/wrong owner/task/nonterminal/selftest statuses rejected');
 f.window.globalInfo.ownerId=999;await f.request(status(101),null,{code:0,data:{status:5}});assert.equal(f.messages.length,1);
 f.window.globalInfo.ownerId=12345;f.window.pageInfo.problemId='16571';await f.request(status(101),null,{code:0,data:{status:5}});assert.equal(f.messages.length,1);
 f.window.pageInfo.problemId='16570';await f.request(status(101),null,{code:0,data:{status:4,desc:'答案错误',memo:'答案正确 AC'}});assert.equal(f.messages.at(-1).verdict,'WA');
 await f.request(status(101),null,{code:0,data:{status:5}});assert.equal(f.messages.at(-1).verdict,'AC');assert.equal(f.messages.at(-1).url,f.ctx.originalUrl);assert.equal(f.messages.at(-1).owner,'12345');
 assert.equal(f.requests.filter(r=>r.method==='POST').length,1);
 // The verified modern production endpoint remains native-click driven too.
 const m=fixture();const production='https://victorinox.nowcoder.com';
 await m.request(production+'/api/service/judge/submit',{...modern,userId:999},{code:0,data:102});assert.equal(m.messages.length,0);
 await m.request(production+'/api/service/judge/submit',{...modern,appId:5},{code:0,data:102});assert.equal(m.messages.length,0);
 await m.request(production+'/api/service/judge/submit',modern,{code:0,data:102});assert.equal(m.messages.at(-1).status,'judging');
 m.responses.push({value:{code:0,data:{status:5}}});await m.window.state.poll();assert.equal(m.messages.at(-1).verdict,'AC');
 assert.ok(!JSON.stringify(m.messages).includes('fixture-short-lived'));
 const passive=fixture({ctxChanges:{sessionId:'unbound',code:''}});passive.window.state.armed=false;
 await passive.request('/nccommon/submit_cd',legacy,{code:0,data:103});await passive.request(status(103),null,{code:0,data:{status:5}});assert.equal(passive.messages.at(-1).verdict,'AC');
 for(const [error,expected] of [[999,'needs_login'],[1125,'needs_verification']]){const p=fixture();await p.request('/nccommon/submit_cd',legacy,{code:error,msg:'fixture rejected'});assert.equal(p.messages.at(-1).status,expected);assert.equal(p.messages.at(-1).attempted,false);}
 console.log(JSON.stringify({ok:true,rejectedRequests:rejected,nativeGlobalLegacy:true,nativeGlobalModern:true,passiveGlobal:true,noRealOJ:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
'''


if __name__ == '__main__':
    unittest.main()
