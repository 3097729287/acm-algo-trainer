"""Real hidden WebView2; every network request intercepted, no OJ account used."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
for directory in ('desktop', 'backend', 'backend/common'):
    sys.path.insert(0, str(ROOT / directory))
os.environ['TB_OFFLINE'] = '1'
import webview
from browser_bridge import BrowserBridge
from browser_sessions import BrowserSessions
from browser_preparation import BrowserPreparation
from silent_submit import SilentSubmitter


def run():
    result, posts, saved, cookies, timings, opened = {}, [], [], [], [], []
    mode = {'login': True, 'context': True, 'invalid': False, 'acToken': None, 'acReject': False}
    accepted_atcoder = [0]
    with tempfile.TemporaryDirectory(prefix='tb-silent-proof-', ignore_cleanup_errors=True) as directory:
        main = webview.create_window('TB invisible fixture', html='<p>Fixture</p>', hidden=True)
        from webview_resources import bind as bind_resources
        bind_resources(main)
        store = BrowserSessions(Path(directory) / 'login.dpapi')
        def sync():
            for request in store.requests():
                domain=request['domains'][0]
                cookie={'value':'test-only-session','domain':'.'+domain,'path':'/','httpOnly':True,'sameSite':'lax','expirationDate':time.time()+600}
                store.accept({**request,'loginState':'logged_in','cookies':[
                    {**cookie,'name':'fixture_login','secure':False},
                    {**cookie,'name':'fixture_partition','secure':True,'partitionKey':{'topLevelSite':'https://'+domain,'hasCrossSiteAncestor':False}}],
                    'userAgent':'TB Fixture'})
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=store, opener=opened.append, on_receipt=lambda sid,s: saved.append(s['verdict']) or True)
        def fixture(view):
            from Microsoft.Web.WebView2.Core import CoreWebView2WebResourceContext
            from System.IO import MemoryStream, StreamReader
            from System.Text import Encoding
            core=view.CoreWebView2
            assert str(core.Profile.ProfileName) in ('tb-cf','tb-atcoder','tb-nowcoder','tb-luogu')
            core.AddWebResourceRequestedFilter('*',CoreWebView2WebResourceContext.All)
            def serve(_, event):
                # Fail closed even if a fixture assertion or header read fails.
                event.Response=core.Environment.CreateWebResourceResponse(MemoryStream(Encoding.UTF8.GetBytes('{}')),599,'Fixture blocked','Content-Type: application/json')
                request=event.Request; url=urlsplit(str(request.Uri)); method=str(request.Method)
                headers='Content-Type: text/html; charset=utf-8'
                body=''
                if request.Content is not None: body=str(StreamReader(request.Content,Encoding.UTF8).ReadToEnd())
                if method=='POST':
                    posts.append((url.hostname,url.path,body))
                    cookies.append(str(request.Headers.GetHeader('Cookie')) if request.Headers.Contains('Cookie') else '')
                def payload(value):
                    nonlocal headers
                    headers='Content-Type: application/json'
                    return json.dumps(value)
                if url.hostname=='www.luogu.com.cn':
                    context={'user':{'uid':12345} if mode['login'] else None,'data':{'problem':{'pid':'B4536','acceptLanguages':[12,34]},'contest':None}}
                    if url.path=='/_lfe/config': content=payload({'route':{'api.problem.submit':'/fe/api/problem/submit/{pid}'},'CodeLanguage':{'12':{'id':12,'name':'C++17','canO2':True}}})
                    elif method=='POST':
                        assert json.loads(body)=={'code':'int main(){}','lang':12,'enableO2':1}
                        assert str(request.Headers.GetHeader('X-CSRF-TOKEN'))=='fixture-csrf'
                        content=payload({'rid':4002})
                    elif url.path.startswith('/record/'):
                        content=payload({'data':{'record':{'id':4002,'problem':{'pid':'B4536'},'user':{'uid':12345},'status':12}}})
                    elif request.Headers.Contains('x-lentille-request'):
                        content=payload({} if mode['invalid'] else context)
                    else:
                        content='<meta name="csrf-token" content="fixture-csrf">'
                        if mode['context']: content+='<script id="lentille-context" type="application/json">'+json.dumps(context)+'</script>'
                        content+='<p>Lazy editor is not mounted</p>'
                elif url.hostname=='ac.nowcoder.com':
                    if method=='POST': content=payload({'code':0,'submissionId':3002})
                    elif url.path=='/nccommon/status': content=payload({'code':0,'id':3002,'status':5,'isSelfTest':False})
                    else: content='''<select name="language"><option value="2">C++（clang++18）</option></select><div class="CodeMirror"></div><script>window.pageInfo={contestId:'127263',questionId:'11604979',isNewJudgeEditor:false,codeJudgeType:'0',tagId:'4',subTagId:'1',doneQuestionId:'127263'};window.globalInfo={ownerId:12345};</script>'''
                else:
                    cf=url.hostname=='codeforces.com'
                    if not cf and method=='POST' and not mode['acReject']:
                        accepted_atcoder[0]+=1
                    submitted=any(p[0]==url.hostname for p in posts) if cf else bool(accepted_atcoder[0])
                    rejected=not cf and method=='POST' and mode['acReject']
                    if not rejected and (url.path.endswith('/my') or url.path.endswith('/submissions/me') or method=='POST'):
                        remote=2001+accepted_atcoder[0]
                        row=('<a href="/contest/123/submission/1002">1002</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a><span class="submissionVerdictWrapper">Accepted</span>' if cf else f'<a href="/contests/abc100/submissions/{remote}">{remote}</a><a href="/contests/abc100/tasks/abc100_a">A</a><span class="label">AC</span>') if submitted else ''
                        content='<table class="status-frame-datatable"><tr><th>Submission</th><th>Verdict</th></tr><tr><td>'+row+'</td></tr></table>'
                        if not cf and not submitted:
                            content='<title>My Submissions - AtCoder Beginner Contest 100</title><nav class="navbar"><a href="/users/fixture">fixture</a></nav><div class="panel-body">No Submissions</div>'
                        elif not cf:
                            content='<nav class="navbar"><a href="/users/fixture">fixture</a></nav>'+content.replace('<span class="label">', '<a href="/users/fixture">fixture</a><span class="label">')
                    else:
                        task='A' if cf else 'abc100_a'
                        account='<header id="header"><a href="/profile/fixture">fixture</a></header>' if cf else '<nav class="navbar"><a href="/users/fixture">fixture</a></nav>'
                        content=account+f'<form method="post"><select name="taskScreenName"><option value="{task}">{task}</option></select><select name="languageId"><option value="2">GNU C++17</option></select><textarea name="sourceCode"></textarea><button type="submit">Submit</button></form>'
                        if not cf and mode['acToken'] is not None:
                            token='fixture-site-token' if mode['acToken'] else ''
                            content=content.replace('</form>',f'<div class="cf-challenge"><input type="hidden" name="cf-turnstile-response" value="{token}"></div></form>')
                        if rejected:
                            content+='<div class="alert alert-danger">Invalid submission verification</div>'
                event.Response=core.Environment.CreateWebResourceResponse(MemoryStream(Encoding.UTF8.GetBytes(content)),200,'OK',headers)
            core.WebResourceRequested+=serve
        runner=SilentSubmitter(main,bridge,store,wake=sync,native_setup=fixture)
        bridge.runner=runner
        preparation=BrowserPreparation(bridge,ROOT/'build/browser-extension',profiles=lambda:[(Path('fixture-browser'),'Default')])
        main.events.closing+=bridge.on_closing
        def wait(sid, status, timeout=30):
            until=time.monotonic()+timeout
            while time.monotonic()<until:
                value=bridge.status(sid)
                if value['status']==status:return value
                if value['status']=='error':raise AssertionError(value)
                time.sleep(.1)
            raise AssertionError(bridge.status(sid))
        def verify():
            try:
                urls=['https://codeforces.com/contest/123/problem/A','https://atcoder.jp/contests/abc100/tasks/abc100_a','https://ac.nowcoder.com/acm/contest/127263/B','https://www.luogu.com.cn/problem/B4536']
                for url in urls:
                    started=time.monotonic()
                    # A stale empty snapshot used to prevent waking the closed
                    # browser at all. Exercise the actual submit gate + runner.
                    preparation.check_submission(url)
                    request=store.requests()[-1]
                    store.accept({**request,'cookies':[],'loginState':'logged_out'})
                    preparation.check_submission(url)
                    sid=bridge.submit(url,'int main(){}','fixture')['sessionId']
                    assert wait(sid,'finished')['verdict']=='AC'
                    timings.append({'platform':bridge.sessions[sid]['platform'],'seconds':round(time.monotonic()-started,3)})
                    assert not runner._ui(lambda:main.native.Visible)
                assert len(posts)==4 and saved==['AC']*4 and not opened
                assert all('fixture_login=test-only-session' in c for c in cookies)
                assert all('fixture_partition=test-only-session' in c for c in cookies)
                # A native form with an existing original-site token can submit.
                # Missing-token handoff is checked last: that job belongs to the
                # browser thereafter, and must not restart the hidden transport.
                before=len(posts)
                mode['acToken']=True
                sid=bridge.submit(urls[1],'int main(){}','AtCoder verified native form')['sessionId']
                assert wait(sid,'finished')['verdict']=='AC'
                assert len(posts)==before+1 and 'cf-turnstile-response=fixture-site-token' in posts[-1][2]
                mode['acReject']=True
                sid=bridge.submit(urls[1],'int main(){}','AtCoder server rejection')['sessionId']
                rejected=wait(sid,'error')
                assert 'Invalid submission verification' in rejected['message'] and len(posts)==before+2
                assert len(opened)==0 and not bridge.sessions[sid].get('manual')
                mode['acReject']=False
                mode['acToken']=None
                extra_atcoder=2
                # Persisted encrypted session, no browser process or connector.
                runner.store=BrowserSessions(Path(directory)/'login.dpapi');runner.wake=lambda:False
                mode['context']=False
                sid=bridge.submit(urls[-1],'int main(){}','lazy Luogu context')['sessionId']
                assert wait(sid,'finished')['verdict']=='AC'
                assert len(posts)==5+extra_atcoder
                mode['login']=False
                sid=bridge.submit(urls[-1],'int main(){}','expired login')['sessionId']
                wait(sid,'needs_login')
                assert len(posts)==5+extra_atcoder
                mode['login']=True
                time.sleep(.4)
                bridge.submit(urls[-1],'int main(){}','explicit retry')
                assert wait(sid,'finished')['verdict']=='AC'
                assert len(posts)==6+extra_atcoder and len(opened)==0
                mode['invalid']=True
                sid=bridge.submit(urls[-1],'int main(){}','invalid context')['sessionId']
                wait(sid,'error',timeout=25)
                assert len(posts)==6+extra_atcoder and not bridge.sessions[sid]['attempted']
                assert not bridge.sessions[sid].get('manual')
                assert len(opened)==0
                mode['acToken']=False
                # Different code creates an independent native job; the earlier
                # rejected job must remain with the browser until superseded.
                sid=bridge.submit(urls[1],'int main(){return 0;}','AtCoder verification required')['sessionId']
                wait(sid,'awaiting_submit',timeout=40)
                assert len(posts)==6+extra_atcoder and not bridge.sessions[sid]['attempted']
                assert bridge.sessions[sid]['manual'] and bridge.sessions[sid]['transport']=='browser'
                assert len(opened)==1 and all(url.startswith(bridge.base_url+'/browser-connect.html#') for url in opened)
                assert not runner._ui(lambda:main.native.Visible)
                result.update(ok=True,allFourHidden=True,allFourStaleCacheRefreshedBeforeSubmit=True,firstPartyPartitionReplayed=True,atcoderFirstContestSubmission=True,atcoderVerificationNoPost=True,atcoderVerifiedNativeForm=True,atcoderRejectionDisplayed=True,reusedBrowserLogin=True,encryptedSessionWorksWithBrowserClosed=True,luoguMissingEditor=True,luoguContextFetch=True,loginRetry=True,invalidContextNoPost=True,manualBrowserHandoffs=len(opened),posts=len(posts),fixtureTimings=timings,realAccountSubmission=False)
            except Exception as error:
                result.update(ok=False,error=repr(error),states=[bridge.status(sid) for sid in bridge.sessions],posts=len(posts))
            finally: main.destroy()
        webview.start(verify,gui='edgechromium',private_mode=False,storage_path=str(Path(directory)/'profile'))
    print(json.dumps(result,ensure_ascii=False),flush=True)
    assert result.get('ok'),result

if __name__=='__main__':run()
