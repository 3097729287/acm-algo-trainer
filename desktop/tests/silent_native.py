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
from silent_submit import SilentSubmitter


def run():
    result, posts, saved, cookies, timings = {}, [], [], [], []
    mode = {'login': True, 'context': True, 'invalid': False}
    with tempfile.TemporaryDirectory(prefix='tb-silent-proof-', ignore_cleanup_errors=True) as directory:
        main = webview.create_window('TB invisible fixture', html='<p>Fixture</p>', hidden=True)
        store = BrowserSessions(Path(directory) / 'login.dpapi')
        def sync():
            for request in store.requests():
                domain=request['domains'][0]
                store.accept({**request,'cookies':[{'name':'fixture_login','value':'test-only-session','domain':'.'+domain,'path':'/','secure':True,'httpOnly':True,'sameSite':'lax','expirationDate':time.time()+600}], 'userAgent':'TB Fixture'})
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=store, opener=lambda _: (_ for _ in ()).throw(AssertionError('Browser opened')), on_receipt=lambda sid,s: saved.append(s['verdict']) or True)
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
                    submitted=any(p[0]==url.hostname for p in posts)
                    if url.path.endswith('/my') or url.path.endswith('/submissions/me') or method=='POST':
                        row=('<a href="/contest/123/submission/1002">1002</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a><span class="submissionVerdictWrapper">Accepted</span>' if cf else '<a href="/contests/abc100/submissions/2002">2002</a><a href="/contests/abc100/tasks/abc100_a">A</a><span class="label">AC</span>') if submitted else ''
                        content='<table class="status-frame-datatable"><tr><th>Submission</th><th>Verdict</th></tr><tr><td>'+row+'</td></tr></table>'
                        if not cf and not submitted:
                            content='<title>My Submissions - AtCoder Beginner Contest 100</title><nav class="navbar"><a href="/users/fixture">fixture</a></nav><div class="panel-body">No Submissions</div>'
                        elif not cf:
                            content=content.replace('<span class="label">', '<a href="/users/fixture">fixture</a><span class="label">')
                    else:
                        task='A' if cf else 'abc100_a'
                        account='<header id="header"><a href="/profile/fixture">fixture</a></header>' if cf else '<nav class="navbar"><a href="/users/fixture">fixture</a></nav>'
                        content=account+f'<form method="post"><select name="taskScreenName"><option value="{task}">{task}</option></select><select name="languageId"><option value="2">GNU C++17</option></select><textarea name="sourceCode"></textarea><button type="submit">Submit</button></form>'
                event.Response=core.Environment.CreateWebResourceResponse(MemoryStream(Encoding.UTF8.GetBytes(content)),200,'OK',headers)
            core.WebResourceRequested+=serve
        runner=SilentSubmitter(main,bridge,store,wake=sync,native_setup=fixture)
        bridge.runner=runner
        main.events.closing+=bridge.on_closing
        def wait(sid, status):
            until=time.monotonic()+30
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
                    sid=bridge.submit(url,'int main(){}','fixture')['sessionId']
                    assert wait(sid,'finished')['verdict']=='AC'
                    timings.append({'platform':bridge.sessions[sid]['platform'],'seconds':round(time.monotonic()-started,3)})
                    assert not runner._ui(lambda:main.native.Visible)
                assert len(posts)==4 and saved==['AC']*4
                assert all('fixture_login=test-only-session' in c for c in cookies)
                # Persisted encrypted session, no browser process or connector.
                runner.store=BrowserSessions(Path(directory)/'login.dpapi');runner.wake=lambda:False
                mode['context']=False
                sid=bridge.submit(urls[-1],'int main(){}','lazy Luogu context')['sessionId']
                assert wait(sid,'finished')['verdict']=='AC'
                assert len(posts)==5
                mode['login']=False
                sid=bridge.submit(urls[-1],'int main(){}','expired login')['sessionId']
                wait(sid,'needs_login')
                assert len(posts)==5
                mode['login']=True
                time.sleep(.4)
                bridge.submit(urls[-1],'int main(){}','explicit retry')
                assert wait(sid,'finished')['verdict']=='AC'
                assert len(posts)==6
                mode['invalid']=True
                sid=bridge.submit(urls[-1],'int main(){}','invalid context')['sessionId']
                until=time.monotonic()+25
                while bridge.status(sid)['status']!='error' and time.monotonic()<until:time.sleep(.1)
                assert bridge.status(sid)['status']=='error' and len(posts)==6
                result.update(ok=True,allFourHidden=True,atcoderFirstContestSubmission=True,reusedBrowserLogin=True,encryptedSessionWorksWithBrowserClosed=True,luoguMissingEditor=True,luoguContextFetch=True,loginRetry=True,invalidContextNoPost=True,posts=len(posts),fixtureTimings=timings,realAccountSubmission=False)
            except Exception as error:
                result.update(ok=False,error=repr(error),states=[bridge.status(sid) for sid in bridge.sessions],posts=len(posts))
            finally: main.destroy()
        webview.start(verify,gui='edgechromium',private_mode=False,storage_path=str(Path(directory)/'profile'))
    print(json.dumps(result,ensure_ascii=False),flush=True)
    assert result.get('ok'),result

if __name__=='__main__':run()
