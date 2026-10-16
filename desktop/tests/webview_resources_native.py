"""Isolated WebView2 policy and process-tree measurement, with local HTTP only.

Run this from Python on Windows. No live account, profile or database is used.
The baseline and optimized child run the exact same page and request workload.
Reports distinguish working set, private committed bytes and CPU seconds.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'desktop'))

HTML = b'''<!doctype html><meta charset="utf-8"><title>TB isolated resource fixture</title>
<body><textarea id="draft"></textarea><main id="rows"></main><script>
window.ticks=0; setInterval(()=>window.ticks++,100);
document.querySelector('#rows').innerHTML=Array.from({length:1200},(_,i)=>'<article><strong>Problem '+i+'</strong><p>Stable local fixture</p></article>').join('');
window.burst=async count=>{
 const start=performance.now(); let next=0;
 await Promise.all(Array.from({length:8},async()=>{
  while(next<count){const id=next++;const response=await fetch('/data?i='+id,{cache:'no-store'});await response.arrayBuffer();}
 }));
 window.burstResult={count,elapsedMs:performance.now()-start};
};
window.saveDraft=async()=>{const text='fixture-code-'.repeat(4000);document.querySelector('#draft').value=text;
 const result=await fetch('/draft',{method:'POST',body:text});window.savedDraft=await result.json();};
</script>'''


def phase(directory, mode):
    import webview
    import webview.platforms.edgechromium as edge
    from webview_resources import bind

    callbacks = {'request':0, 'response':0}
    original_request, original_response = edge.EdgeChrome.on_web_resource_request, edge.EdgeChrome.on_web_resource_response
    def counted_request(self, sender, event):
        callbacks['request'] += 1
        return original_request(self, sender, event)
    def counted_response(self, sender, event):
        callbacks['response'] += 1
        return original_response(self, sender, event)
    edge.EdgeChrome.on_web_resource_request, edge.EdgeChrome.on_web_resource_response = counted_request, counted_response
    state = {'posts':0, 'bytes':0}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args): pass
        def do_GET(self):
            body = HTML if self.path == '/' else b'x' * 65536
            self.send_response(200)
            self.send_header('Content-Type', 'text/html' if self.path == '/' else 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            for i in range(8): self.send_header(f'X-Fixture-{i}', 'local-resource-proof')
            self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            state['posts'] += 1; state['bytes'] = len(body)
            answer = json.dumps({'savedBytes':len(body)}).encode()
            self.send_response(200); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length', str(len(answer))); self.end_headers(); self.wfile.write(answer)

    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    started = time.perf_counter()
    window = webview.create_window('TB isolated resource proof', f'http://127.0.0.1:{server.server_address[1]}', width=1200, height=850, hidden=True)
    subscribers = {'request':0, 'response':0}
    if mode == 'subscribed':
        def request_listener(_request): subscribers['request'] += 1
        def response_listener(_response): subscribers['response'] += 1
        window.events.request_sent += request_listener
        window.events.response_received += response_listener
    policy = bind(window) if mode != 'baseline' else None
    result = {'mode':mode}

    def verify():
        from System import Action
        from System.Diagnostics import Process
        from System.Windows.Forms import FormWindowState
        def ui(action):
            out=[]
            window.native.Invoke(Action(lambda:out.append(action())))
            return out[0]
        def wait(check, timeout=30):
            until=time.monotonic()+timeout
            while time.monotonic()<until:
                value=check()
                if value: return value
                time.sleep(.025)
            raise AssertionError('Native fixture timed out')
        def measure():
            pids=ui(lambda:[int(item.ProcessId) for item in window.native.browser.webview.CoreWebView2.Environment.GetProcessInfos()])
            samples=[]
            for pid in sorted(set([os.getpid(), *pids])):
                try:
                    process=Process.GetProcessById(pid); process.Refresh()
                    samples.append({'pid':pid,'name':str(process.ProcessName),'privateBytes':int(process.PrivateMemorySize64),'workingSetBytes':int(process.WorkingSet64),'cpuSeconds':float(process.TotalProcessorTime.TotalSeconds)})
                    process.Dispose()
                except Exception: pass
            return {'processes':len(samples),'privateBytes':sum(x['privateBytes'] for x in samples),'workingSetBytes':sum(x['workingSetBytes'] for x in samples),'cpuSeconds':sum(x['cpuSeconds'] for x in samples),'details':samples}
        def state_view():
            core=window.native.browser.webview.CoreWebView2
            return {'visible':bool(window.native.browser.webview.Visible),'target':str(core.MemoryUsageTargetLevel),'suspended':bool(core.IsSuspended)}
        try:
            assert window.events.loaded.wait(30)
            wait(lambda:window.evaluate_js('window.ticks') is not None)
            result['startupSeconds']=time.perf_counter()-started
            result['runtimeVersion']=ui(lambda:str(window.native.browser.webview.CoreWebView2.Environment.BrowserVersionString))
            def foreground():
                window.native.Opacity=0
                window.native.ShowInTaskbar=False
                window.native.Show()
                window.native.Activate()
            ui(foreground)
            time.sleep(.3)
            foreground_state=ui(state_view)
            assert foreground_state['target']=='Normal',foreground_state
            result['foregroundState']=foreground_state
            if policy:
                result['removedHooks']=list(policy.removed_hooks)
                assert set(policy.removed_hooks)==(set() if mode=='subscribed' else {'request_sent','response_received'}),result
            before_callbacks=dict(callbacks)
            before=measure()
            window.evaluate_js('window.burstResult=null;void window.burst(400)')
            burst=wait(lambda:window.evaluate_js('window.burstResult'))
            after=measure()
            result['burst']={**burst,'cpuSeconds':after['cpuSeconds']-before['cpuSeconds'],'callbacks':{key:callbacks[key]-before_callbacks[key] for key in callbacks}}
            if mode=='optimized':assert result['burst']['callbacks']=={'request':0,'response':0},result['burst']
            else:assert result['burst']['callbacks']['request']>=400,result['burst']
            if mode=='subscribed':assert subscribers['request']>=400 and subscribers['response']>=400,subscribers
            time.sleep(1)
            result['foregroundMemory']=measure()
            ticks_before=window.evaluate_js('window.ticks')
            ui(lambda:setattr(window.native,'WindowState',FormWindowState.Minimized))
            time.sleep(.2)
            minimized=ui(state_view)
            assert not minimized['suspended'],minimized
            if policy:assert minimized['target']=='Low' and not minimized['visible'],minimized
            result['minimizedState']=minimized
            window.evaluate_js('void window.saveDraft()')
            saved=wait(lambda:window.evaluate_js('window.savedDraft'))
            assert saved['savedBytes']==52000 and state['posts']==1,(saved,state)
            idle_before=measure();idle_started=time.monotonic()
            time.sleep(3)
            idle_after=measure()
            result['minimizedMemory']=idle_after
            result['idleCpuSeconds']=idle_after['cpuSeconds']-idle_before['cpuSeconds']
            result['idleWallSeconds']=time.monotonic()-idle_started
            assert window.evaluate_js('window.ticks')>ticks_before,'timers must remain active'
            def restore():
                window.native.WindowState=FormWindowState.Normal
                window.native.Activate()
            ui(restore);time.sleep(.2)
            restored=ui(state_view)
            assert restored['target']=='Normal' and restored['visible'] and not restored['suspended'],restored
            assert window.evaluate_js("document.querySelector('#draft').value.length")==52000
            if mode=='subscribed':
                def overlay_during_minimize():
                    from System.Windows.Forms import DockStyle, Panel
                    form=window.native;view=form.browser.webview
                    form.WindowState=FormWindowState.Minimized
                    overlay=Panel();overlay.Dock=DockStyle.Fill;form.Controls.Add(overlay);overlay.BringToFront();overlay.Visible=True
                    form.WindowState=FormWindowState.Normal
                    assert not view.Visible and overlay.Visible,'restoring the app must not cover an open original-site overlay'
                    overlay.Dispose();view.Visible=True
                    original_core=policy.core
                    class MissingMemorySdk:
                        @property
                        def MemoryUsageTargetLevel(self):raise AttributeError('SDK fixture does not provide this optional property')
                        @MemoryUsageTargetLevel.setter
                        def MemoryUsageTargetLevel(self,_value):raise AttributeError('SDK fixture does not provide this optional property')
                    try:
                        policy.core=MissingMemorySdk();policy.memory_target=None;policy.memory_supported=None
                        policy._apply()
                        assert policy.memory_supported is False
                    finally:
                        policy.core=original_core;policy.memory_supported=None;policy._apply()
                ui(overlay_during_minimize)
                result.update(originalSiteOverlayPreserved=True,unsupportedSdkFallsBack=True)
            result.update(restoredState=restored,backgroundDraftBytes=52000,timersRunningWhileMinimized=True,subscribers=subscribers,ok=True)
        except Exception as issue:
            result.update(ok=False,error=repr(issue))
        finally:window.destroy()
    try:
        webview.start(verify,gui='edgechromium',private_mode=False,storage_path=str(directory/'profile'))
    finally:
        server.shutdown();server.server_close()
    print(json.dumps(result),flush=True)
    if not result.get('ok'):raise SystemExit(1)


def run(rounds, output):
    reports=[]
    with tempfile.TemporaryDirectory(prefix='tb-webview-resource-proof-',ignore_cleanup_errors=True) as temporary:
        base=Path(temporary)
        sequence=['subscribed'] if rounds==0 else [item for _ in range(rounds) for item in ('baseline','optimized')]
        for index,mode in enumerate(sequence):
            directory=base/f'{index}-{mode}';directory.mkdir()
            run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',str(directory),'--mode',mode],capture_output=True,text=True,encoding='utf-8',timeout=100,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),env=dict(os.environ,TB_OFFLINE='1',TB_STATE_DIR=str(directory/'state')))
            lines=[line for line in run.stdout.splitlines() if line.startswith('{')]
            if not lines or run.returncode:raise AssertionError(run.stdout+'\n'+run.stderr)
            report=json.loads(lines[-1]);reports.append(report)
            print(json.dumps({key:report[key] for key in ('mode','ok','startupSeconds','burst','idleCpuSeconds','originalSiteOverlayPreserved','unsupportedSdkFallsBack') if key in report},ensure_ascii=False),flush=True)
        summary={}
        for mode in ('baseline','optimized'):
            selected=[row for row in reports if row['mode']==mode]
            if selected:
                summary[mode]={'startupSecondsMedian':statistics.median(row['startupSeconds'] for row in selected),'burstMsMedian':statistics.median(row['burst']['elapsedMs'] for row in selected),'burstCpuSecondsMedian':statistics.median(row['burst']['cpuSeconds'] for row in selected),'foregroundPrivateMiBMedian':statistics.median(row['foregroundMemory']['privateBytes']/2**20 for row in selected),'foregroundWorkingSetMiBMedian':statistics.median(row['foregroundMemory']['workingSetBytes']/2**20 for row in selected),'minimizedPrivateMiBMedian':statistics.median(row['minimizedMemory']['privateBytes']/2**20 for row in selected),'minimizedWorkingSetMiBMedian':statistics.median(row['minimizedMemory']['workingSetBytes']/2**20 for row in selected),'idleCpuSecondsMedian':statistics.median(row['idleCpuSeconds'] for row in selected)}
        if output:
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps({'summary':summary,'runs':reports,'measurement':'isolated native fixture, same page and 400 local 64KiB requests; process tree totals; no user data'},indent=2),encoding='utf-8')
        print(json.dumps({'ok':True,'summary':summary},ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--child',type=Path);parser.add_argument('--mode',choices=['baseline','optimized','subscribed']);parser.add_argument('--rounds',type=int,default=1);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.child:phase(args.child,args.mode)
    else:run(args.rounds,args.output)
