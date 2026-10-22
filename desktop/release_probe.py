"""Release checks require an explicitly isolated state directory."""
import json
import os
from pathlib import Path
import threading
import time


def network_check(output):
    """Explicit diagnosis of the bundled service; no account or credential input."""
    from version import VERSION
    from leaderboard import bundled_endpoint, service_opener
    from urllib.error import HTTPError
    from urllib.request import Request
    report = {'ok': False, 'version': VERSION, 'frozen': bool(getattr(__import__('sys'), 'frozen', False))}
    try:
        if not os.environ.get('TB_STATE_DIR'):
            raise RuntimeError('Network checks require an explicitly isolated state directory')
        if os.environ.get('TB_OFFLINE') == '1':
            raise RuntimeError('An offline check cannot contact the bundled service')
        endpoint = bundled_endpoint()
        if not endpoint.startswith('https://'):
            raise RuntimeError('The bundled account service must use HTTPS')
        opener = service_opener(endpoint)
        started = time.monotonic()
        with opener.open(Request(endpoint + '/v1/health', headers={'Accept': 'application/json'}), timeout=8) as response:
            health = json.loads(response.read(4096))
        assert health.get('ok') is True
        report.update(httpsVerified=True, healthSeconds=round(time.monotonic() - started, 3), serverVersion=health['version'])
        # Empty input is always rejected before account creation. This exercises
        # the shipped POST transport without registering a production fixture.
        started = time.monotonic()
        try:
            with opener.open(Request(endpoint + '/v1/accounts/register', data=b'{}',
                             headers={'Content-Type': 'application/json', 'Accept': 'application/json'}), timeout=8):
                raise AssertionError('Empty registration input was unexpectedly accepted')
        except HTTPError as issue:
            assert issue.code == 400
            assert isinstance(json.loads(issue.read(4096)).get('error'), str)
            report.update(registrationValidationStatus=issue.code, postSeconds=round(time.monotonic() - started, 3))
        report.update(ok=True, credentialsSent=False, productionTestRegistrations=0)
    except Exception as issue:
        # Do not serialize response bodies, headers or proxy configuration.
        report.update(error=type(issue).__name__)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1


def run(action, output):
    if action == '--account-network-check':
        return network_check(output)
    from paths import ROOT, STATE, FRONTEND
    from version import VERSION
    server = None
    report = {'ok': False, 'version': VERSION}
    try:
        if not os.environ.get('TB_STATE_DIR'):
            raise RuntimeError('Set TB_STATE_DIR to a disposable directory before running a release probe')
        from backend import create_server
        account_check = action in ('--serve-account-check', '--native-account-check')
        account_endpoint = os.environ.get('TB_TEST_ACCOUNTS_ENDPOINT') if account_check else None
        if account_check:
            from urllib.parse import urlsplit
            endpoint = urlsplit(account_endpoint or '')
            if endpoint.scheme != 'http' or endpoint.hostname != '127.0.0.1' or not endpoint.port:
                raise RuntimeError('Account release checks require a disposable loopback account service')
        server = create_server(require_account=account_check, account_endpoint=account_endpoint,
                               port=int(os.environ.get('TB_PACKAGE_PORT', '0')), dist_dir=FRONTEND,
                               training_file=STATE / 'tb-personal.sqlite3', integration_auto_start=False)
        data = server.store.data()
        workspace = server.training.workspace()
        rows = [row for row in data['rows'] if row.get('solutionAvailable')]
        xterfusion = next(row for row in rows if row['title'] == 'Xterfusion')
        solution = server.store.solution(xterfusion['id'])
        text = solution['markdown']
        assert len(rows) >= 796
        assert all(section in text for section in ('### 题意', '### 思路', '### 参考代码', '```cpp'))
        assert solution['images'] and all(value.startswith('data:image/') for value in solution['images'].values())
        assert {'周赛 163::A', 'ABC 469::A', 'Div.3 1125::A'} <= {row['id'] for row in rows}
        linked_lectures = server.lectures.for_problem(xterfusion['id'])
        assert linked_lectures, 'Existing editorial lost its linked foundation lesson'
        assert len({item['id'] for item in linked_lectures}) == len(linked_lectures)
        assert all(server.lectures.get(item['id'])['markdown'].strip() for item in linked_lectures)
        report['linkedLecturesChecked'] = len(linked_lectures)
        report.update(ok=True, root=str(ROOT), state=str(STATE), frozen=bool(getattr(__import__('sys'), 'frozen', False)),
                      initialTrainingEmpty=workspace['summary']['total']==0, problems=len(data['rows']), solutions=len(rows),
                      lectures=len(server.lectures.snapshot()['lectures']), xterfusionCharacters=len(text),
                      library=server.store.library.check(), profile=server.training.profile()['profile'],
                      baseUrl='http://127.0.0.1:'+str(server.server_port))
        if action == '--package-check':
            from judge import Judge
            import re
            class Fixture:
                def bundle(self, identity):
                    return {'scope':'local','cases':[{'input':'','output':'42\n'}],
                            'limits':{'timeMs':1000,'memoryMb':64},'checker':None,
                            'caseInsensitive':False,'nonunique':False,'coverage':'Release compiler fixture'}
            runner = Judge(Fixture(), STATE / 'release-compiler-check')
            result = runner.execute('release-check','#include <iostream>\nint main(){std::cout<<42<<"\\n";}')
            report.update(compiler=str(runner.compiler), compilerVerdict=result['verdict'])
            assert result['verdict']=='SAMPLE_PASS', result
            python_result=runner.execute('release-python-check','print(42)',language='python3')
            assert python_result['verdict']=='SAMPLE_PASS', python_result
            report.update(pythonRuntime=str(runner.python),pythonVerdict=python_result['verdict'])
            # A user's PC need not have MSYS/GCC on PATH. Exercise all four
            # platforms using bundled public statements/reference code only.
            old_path=os.environ.get('PATH','')
            platform_runs=[]
            try:
                os.environ['PATH']=str(Path(os.environ['SystemRoot'])/'System32')+os.pathsep+os.environ['SystemRoot']
                asset_library=server.training._asset_library()
                engine=Judge(asset_library,STATE/'release-platform-check')
                for platform in ('Codeforces','AtCoder','牛客','洛谷'):
                    for row in rows:
                        if row.get('platform')!=platform or (row.get('difficulty') or 9999)>1200:continue
                        asset=asset_library.problem(row['id'],fetch=False)
                        if not asset.get('statementAvailable') or not asset.get('samples'):continue
                        sources=re.findall(r'```(?:cpp|c\+\+)\s*\n(.*?)```',server.store.solution(row['id'])['markdown'],re.S)
                        sources=[code for code in sources if re.search(r'\bmain\s*\(',code)]
                        if not sources:continue
                        started=time.monotonic()
                        checked=engine.execute(row['id'],sources[-1],mode='run',sample_run=True)
                        assert checked['verdict']=='SAMPLE_PASS',(platform,row['id'],checked)
                        platform_runs.append({'platform':platform,'id':row['id'],'verdict':checked['verdict'],'samples':checked['total'],'seconds':round(time.monotonic()-started,3)})
                        break
                    else:raise AssertionError('No public compiler fixture for '+platform)
                report.update(platformRuns=platform_runs,developerCompilerPathRequired=False)
            finally:os.environ['PATH']=old_path
        else:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            if action in ('--serve-check', '--serve-account-check'):
                Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                while not Path(output).with_suffix('.stop').exists():
                    time.sleep(.2)
            elif action == '--native-account-check':
                import webview
                window = webview.create_window('TB account validation', report['baseUrl'], hidden=True, width=1100, height=850)
                def check_account():
                    def wait_js(script):
                        deadline = time.monotonic() + 35
                        while time.monotonic() < deadline:
                            if window.evaluate_js(script):
                                return
                            time.sleep(.1)
                        raise RuntimeError('Native account UI condition timed out')
                    def fill(name, value):
                        window.evaluate_js("(()=>{const e=document.querySelector(" + json.dumps('input[name="'+name+'"]') +
                            ");Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e," + json.dumps(value) +
                            ");e.dispatchEvent(new Event('input',{bubbles:true}));})()")
                    try:
                        wait_js("document.querySelector('.account-card h1')?.textContent==='登录 TB'")
                        assert not server.accounts.snapshot()['authenticated']
                        report['nativeLoginGate'] = True
                        window.evaluate_js("document.querySelectorAll('.account-tabs button')[1].click()")
                        wait_js("!!document.querySelector('input[name=nickname]')")
                        fill('nickname', '打包验证者'); fill('username', 'native_account_fixture')
                        fill('password', 'native-fixture-password'); fill('passwordConfirmation', 'native-fixture-password')
                        window.evaluate_js("document.querySelector('.account-submit').click()")
                        wait_js("document.querySelector('.account-message')?.textContent.includes('注册成功')")
                        assert not server.accounts.snapshot()['authenticated']
                        report['nativeRegistrationRequiresLogin'] = True
                        fill('password', 'native-fixture-password')
                        window.evaluate_js("document.querySelector('.account-submit').click()")
                        wait_js("!!document.querySelector('.nav-item')")
                        wait_js("!!document.querySelector('.onboarding')")
                        window.evaluate_js("document.querySelector('.modal header button[aria-label=关闭]').click()")
                        report['nativeNewUserGuide'] = True
                        assert server.accounts.snapshot()['authenticated']
                        report['nativeAccountLogin'] = True
                    except Exception as issue:
                        report.update(ok=False, error=str(issue))
                    finally:
                        window.destroy()
                webview.start(check_account, gui='edgechromium', private_mode=False, storage_path=str(STATE / 'native-account-webview'))
            elif action == '--native-check':
                import webview
                from launch import bind_desktop_fullscreen, configure_desktop_downloads
                from window_memory import is_fullscreen
                configure_desktop_downloads()
                assert workspace['summary']['total'] == 0, 'Native UI probe requires fresh disposable state'
                assert server.training.submissions()['total'] == 0, 'Native UI probe refuses existing history'
                tested = next(row for row in rows if row['contest'] == '入门赛 49' and row['problem'] == 'D')
                code = '#include <bits/stdc++.h>\nusing namespace std; int main(){int n;cin>>n;long long one[61]={1},two[61]={0};for(int i=1;i<=n;++i){one[i]=one[i-1]+two[i-1];if(i>=2)two[i]=one[i-2];}cout<<one[n]+two[n]<<"\\n";}\n'
                server.training.save_draft(tested['id'], code)
                window = webview.create_window('TB release validation',report['baseUrl'],hidden=True,width=1480,height=920)
                bind_desktop_fullscreen(server, window)
                def check():
                    def wait_js(script, timeout=30):
                        deadline = time.monotonic() + timeout
                        while time.monotonic() < deadline:
                            if window.evaluate_js(script):
                                return
                            time.sleep(.1)
                        raise RuntimeError('Native UI condition timed out: ' + script)

                    def key(value, ctrl=False):
                        window.evaluate_js('window.dispatchEvent(new KeyboardEvent("keydown",' +
                                           json.dumps({'key': value, 'ctrlKey': ctrl, 'bubbles': True}) + '))')

                    try:
                        wait_js("!!document.querySelector('.nav-item')")
                        report['nativeLoaded'] = True
                        window.evaluate_js("document.querySelector('.nav-item[aria-label=\"算法实验室\"]').click()")
                        wait_js("!!document.querySelector('.lab-course-options')")
                        window.evaluate_js("document.querySelector('.lab-course-options button').click()")
                        wait_js("!!document.querySelector('.algorithm-lab .lab-course-header h1')")
                        assert window.evaluate_js("document.querySelector('.algorithm-lab .lab-course-header h1').textContent") == '背包 DP'
                        report['nativeAlgorithmLab'] = True
                        window.evaluate_js("document.querySelector('.lab-mode-switch').click()")
                        wait_js("!!document.querySelector('.lab-guided')")
                        assert window.evaluate_js("document.querySelector('.lab-guided .lab-position').textContent") == '1 / 5'
                        report['nativeGuidedProblems'] = True
                        window.evaluate_js("document.querySelector('[aria-label=\"设置\"]').click()")
                        wait_js("!!document.querySelector('[role=tab][aria-label=\"交互与导航\"]')")
                        window.evaluate_js("document.querySelector('[role=tab][aria-label=\"交互与导航\"]').click()")
                        wait_js("!!document.querySelector('input[aria-label=\"全屏\"]') && !document.querySelector('input[aria-label=\"全屏\"]').disabled")
                        assert not is_fullscreen(window)
                        window.evaluate_js("document.querySelector('input[aria-label=\"全屏\"]').click()")
                        wait_js("document.querySelector('input[aria-label=\"全屏\"]').checked")
                        assert is_fullscreen(window)
                        from System.Windows.Forms import Screen
                        assert window.native.Bounds == Screen.FromControl(window.native).Bounds
                        window.evaluate_js("document.querySelector('input[aria-label=\"全屏\"]').click()")
                        wait_js("!document.querySelector('input[aria-label=\"全屏\"]').checked")
                        assert not is_fullscreen(window)
                        report['fullscreenToggle'] = True
                        key('F11')
                        wait_js("document.querySelector('input[aria-label=\"全屏\"]').checked")
                        assert is_fullscreen(window)
                        key('F11')
                        wait_js("!document.querySelector('input[aria-label=\"全屏\"]').checked")
                        assert not is_fullscreen(window)
                        report['f11FrontendEvent'] = True
                        key('2', ctrl=True)
                        wait_js("!!document.querySelector('input[aria-label=\"搜索题目\"]')")
                        window.evaluate_js("(() => {const field=document.querySelector('input[aria-label=\"搜索题目\"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(field,'入门赛 49 D');field.dispatchEvent(new Event('input',{bubbles:true}));})()")
                        title = json.dumps(tested['title'], ensure_ascii=False)
                        wait_js("Array.from(document.querySelectorAll('.problem-table tbody tr')).some(row=>row.textContent.includes(" + title + "))")
                        window.evaluate_js("Array.from(document.querySelectorAll('.problem-table tbody tr')).find(row=>row.textContent.includes(" + title + ")).querySelector('.problem-title').click()")
                        wait_js("!!document.querySelector('.wb-run-actions') && document.querySelector('.cm-content')?.textContent.includes('long long one')")
                        labels = window.evaluate_js("Array.from(document.querySelectorAll('.wb-run-actions button')).map(node=>node.textContent.trim())")
                        assert labels == ['运行样例', '提交'], labels
                        report['buttonOrder'] = labels
                        window.evaluate_js("document.querySelectorAll('.wb-run-actions button')[0].click()")
                        wait_js("document.querySelector('.wb-result-summary')?.textContent.includes('样例通过')", timeout=90)
                        submission = next(row for row in server.training.submissions()['submissions'] if row['problemId'] == tested['id'] and row['mode'] == 'run')
                        assert submission['verdict'] == 'SAMPLE_PASS', submission['verdict']
                        assert submission['total'] > 0 and submission['passed'] == submission['total']
                        assert server.training.workspace()['summary']['accepted'] == 0
                        assert server.training.insights(server.store.extensions.snapshot())['growth']['totalXp'] == 0
                        assert all(not task['completed'] and task['scope'] == 'official' and task['version'] == 2 for task in server.training.daily_tasks()['tasks'])
                        report['localSubmission'] = {name: submission[name] for name in ('verdict', 'scope', 'passed', 'total')}
                        report['localAwardsNothing'] = True
                        report['officialSubmissionSent'] = False
                        # Exercise the real desktop Blob download path. Only
                        # the modal destination picker is replaced in this
                        # disposable probe; WebView2 still writes the JSON.
                        import webview.platforms.edgechromium as edge
                        native_forms=edge.WinForms
                        destination=STATE/'native-learning-export.json'
                        class ExportDialog:
                            def ShowDialog(self, _form):
                                assert self.FileName.endswith('.json'),self.FileName
                                self.FileName=str(destination)
                                return native_forms.DialogResult.OK
                        class FormsProxy:
                            def __getattr__(self,name):
                                return ExportDialog if name=='SaveFileDialog' else getattr(native_forms,name)
                        edge.WinForms=FormsProxy()
                        try:
                            window.evaluate_js("Array.from(document.querySelectorAll('.sidebar button')).find(b=>b.textContent.includes('设置')).click()")
                            wait_js("!!document.querySelector('.settings-subpage-tabs')")
                            window.evaluate_js("document.querySelector('.settings-return-button')?.click()")
                            wait_js("!!document.querySelector('.settings-home-grid')")
                            window.evaluate_js("document.querySelector('[role=tab][aria-label=\"数据与帮助\"]').click()")
                            wait_js("!!document.querySelector('.help-action')")
                            window.evaluate_js("document.querySelector('.help-action').click()")
                            deadline=time.monotonic()+20
                            exported=None
                            while time.monotonic()<deadline:
                                try:
                                    exported=json.loads(destination.read_text(encoding='utf-8'))
                                    break
                                except (FileNotFoundError,json.JSONDecodeError):time.sleep(.1)
                            assert exported is not None,'Native JSON download did not finish'
                            assert exported['format']=='tb-learning-export'
                            assert any(row['code']==code for row in exported['tables']['drafts'])
                            assert 'ranking_profile' not in exported['tables']
                            report['nativeJsonExport']=True
                        finally:edge.WinForms=native_forms
                    except Exception as error:
                        import traceback
                        report.update(ok=False,error=str(error),traceback=traceback.format_exc())
                    finally:
                        window.destroy()
                webview.start(check,gui='edgechromium',private_mode=True,storage_path=str(STATE/'release-profile'))
            server.shutdown()
            worker.join(3)
    except Exception as error:
        import traceback
        report.update(ok=False,error=str(error),traceback=traceback.format_exc())
    finally:
        if server:
            server.server_close()
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if report.get('ok') else 1
