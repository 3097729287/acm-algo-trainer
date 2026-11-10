"""Close isolated real WebView2 fixtures after their own browser process exits.

No installed ToBe process, browser profile, account or provider is accessed.
Browser.crash is issued only through this fixture's own CoreWebView2.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'desktop'))
from close_coordinator import CloseCoordinator
from webview_resources import MainViewResources


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('x','button','pending'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    directory=args.output.resolve().parent
    directory.mkdir(parents=True,exist_ok=True)
    db=directory/(args.mode+'-synthetic.sqlite3')
    if db.exists():raise RuntimeError('Use a fresh fixture output directory')
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE fixture_draft(value TEXT NOT NULL)')
        connection.execute('INSERT INTO fixture_draft VALUES (?)',('committed synthetic draft',))
    original=hashlib.sha256(db.read_bytes()).hexdigest()
    result={'mode':args.mode,'ownProcessId':os.getpid(),'events':[],
            'realAccountOrBrowserUsed':False,'externalProcessSignalled':False}
    errors=[]
    failed=threading.Event();closed=threading.Event();stopped=threading.Event()
    save_signal=threading.Event()
    started=time.monotonic()
    import webview
    window=webview.create_window('TB isolated crashed browser close fixture',
        html='''<p>Private local crash close fixture</p><script>
        window.addEventListener('tb-before-update',event=>event.detail.waitUntil(new Promise(()=>{})));
        window.addEventListener('tb-desktop-closing',()=>window.pywebview.api.fixture_saved());
        </script>''',hidden=True)
    def fixture_saved():save_signal.set()
    window.expose(fixture_saved)
    policy=MainViewResources(window)
    coordinator=CloseCoordinator(window,stopped.set,frontend_alive=policy.frontend_alive)
    policy.on_frontend_failed=coordinator.frontend_failed
    original_failed=policy._process_failed
    def process_failed(sender,event):
        kind=str(event.ProcessFailedKind)
        result['events'].append(kind)
        original_failed(sender,event)
        if kind=='BrowserProcessExited':failed.set()
    policy._process_failed=process_failed
    window.events.before_show+=policy.attach
    window.events.closing+=coordinator.on_closing
    window.events.closed+=closed.set

    def ui(action):
        from System import Action
        outcome=[];issues=[]
        def run():
            try:outcome.append(action())
            except BaseException as issue:issues.append(issue)
        window.native.Invoke(Action(run))
        if issues:raise issues[0]
        return outcome[0] if outcome else None

    def own_quit():
        # Failure cleanup only: WM_QUIT ends only this fixture's message loop.
        from ctypes import wintypes
        user32=ctypes.WinDLL('user32',use_last_error=True)
        user32.GetWindowThreadProcessId.argtypes=(wintypes.HWND,ctypes.POINTER(wintypes.DWORD))
        user32.GetWindowThreadProcessId.restype=wintypes.DWORD
        owner=wintypes.DWORD()
        thread_id=user32.GetWindowThreadProcessId(int(window.native.Handle.ToInt64()),ctypes.byref(owner))
        assert owner.value==os.getpid(),'Refusing to signal a foreign fixture window'
        assert user32.PostThreadMessageW(thread_id,0x12,0,0),'Could not end fixture UI loop'

    def run():
        try:
            assert window.events.loaded.wait(10),'Isolated frontend did not load'
            assert policy.core is not None,'Isolated CoreWebView2 did not initialize'
            result['ownBrowserProcessId']=ui(lambda:int(policy.core.BrowserProcessId))
            if args.mode=='pending':
                window.destroy()
                time.sleep(.2)
                assert coordinator.requesting and not closed.is_set(),'Pending local save did not cancel the first close'
            ui(lambda:policy.core.CallDevToolsProtocolMethodAsync('Browser.crash','{}'))
            assert failed.wait(5),'Private browser did not report BrowserProcessExited'
            assert not policy.frontend_alive(),'Exited frontend still advertised itself as alive'
            before_close=time.monotonic()
            if args.mode=='x':
                window.destroy()
            elif args.mode=='button':
                def click():
                    buttons=[control for control in policy.failure_panel.Controls if str(control.Text)=='关闭 ToBe']
                    assert len(buttons)==1,'Native crash panel has no independent close button'
                    # PerformClick is deliberately suppressed by WinForms for
                    # invisible controls. Raise its native click event while
                    # keeping this fixture hidden from the user's desktop.
                    from System import Array,EventArgs,Object
                    from System.Reflection import BindingFlags
                    method=buttons[0].GetType().GetMethod('OnClick',BindingFlags.NonPublic|BindingFlags.Instance)
                    method.Invoke(buttons[0],Array[Object]([EventArgs.Empty]))
                ui(click)
            assert closed.wait(3),'Native window did not close after browser exit'
            assert stopped.wait(1),'Native cleanup was not invoked'
            assert not save_signal.is_set(),'Crash close falsely reported a completed editor save'
            result.update(nativeClosed=True,cleanupCalled=True,saveFalselyConfirmed=False,
                          closeSeconds=round(time.monotonic()-before_close,3))
        except BaseException as issue:
            errors.append(str(issue))
            own_quit()

    try:
        webview.start(run,gui='edgechromium',private_mode=False,
                      storage_path=str(directory/(args.mode+'-private-profile')),debug=False)
        result['webviewStartReturned']=True
    finally:
        result['finallyExecuted']=True
        result['committedSyntheticSqlitePreserved']=hashlib.sha256(db.read_bytes()).hexdigest()==original
        with sqlite3.connect(db) as connection:
            assert connection.execute('SELECT value FROM fixture_draft').fetchone()[0]=='committed synthetic draft'
        result.update(errors=errors,seconds=round(time.monotonic()-started,3))
        result['ok']=not errors and result.get('nativeClosed',False) and result['committedSyntheticSqlitePreserved']
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    if errors:raise AssertionError('; '.join(errors))


if __name__=='__main__':main()
