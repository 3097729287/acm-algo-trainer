"""Measure the normal frozen loader and signed-in UI in disposable account data.

Fixture setup uses the frozen account API, then normal ToBeLoader.exe launches
restore that real session. CDP only observes the owned WebView2 profile. No
renderer replacement, startup monkeypatch or original-site submission is used.
"""
from contextlib import closing
import argparse
import ctypes
from ctypes import wintypes as w
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)


def stop_windows(pid,executable):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    kernel.CloseHandle.argtypes=[w.HANDLE]
    process=kernel.OpenProcess(0x1000,False,pid)
    if not process:return
    try:
        size=w.DWORD(32768);path=ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(process,0,path,ctypes.byref(size)) or Path(path.value).resolve()!=executable.resolve():
            raise ValueError('Refusing to close a process outside the isolated package')
    finally:kernel.CloseHandle(process)
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user.EnumWindows.argtypes=[callback,w.LPARAM]
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
    @callback
    def visit(handle,_):
        owner=w.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(owner))
        if owner.value==pid:user.PostMessageW(handle,0x0010,0,0)
        return True
    user.EnumWindows(visit,0)


def observe_frame(pid,started,finished,result):
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user.EnumWindows.argtypes=[callback,w.LPARAM]
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    user.IsWindowVisible.argtypes=[w.HWND]
    user.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
    while not finished.is_set() and time.perf_counter()-started<15:
        @callback
        def visit(handle,_):
            owner=w.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(owner))
            if owner.value==pid and user.IsWindowVisible(handle):
                rect=w.RECT();user.GetWindowRect(handle,ctypes.byref(rect))
                if rect.right-rect.left>=1050 and rect.bottom-rect.top>=700:
                    result.update(frameworkVisibleMs=round((time.perf_counter()-started)*1000,2),
                                  frameworkBounds=[rect.left,rect.top,rect.right,rect.bottom])
                    return False
            return True
        user.EnumWindows(visit,0)
        if 'frameworkVisibleMs' in result:return
        time.sleep(.005)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--work-dir',type=Path,required=True)
    args=parser.parse_args();package=args.package.resolve(strict=True);folder=args.work_dir.resolve()
    owned=(ROOT/'.backups/next-150').resolve()
    assert package.is_relative_to(owned)
    assert folder.is_relative_to(owned) or folder.is_relative_to((ROOT/'build').resolve())
    assert not folder.exists(),'Use a fresh isolated fixture; existing evidence is retained'
    assert (package/'ToBe.exe').is_file() and (package/'ToBeLoader.exe').is_file()
    assert shutil.disk_usage(folder.parent).free>=3*1024**3,'Keep existing artifacts; insufficient space for one isolated public-library fixture'
    folder.mkdir(parents=True,exist_ok=False);state=folder/'profile/state';state.mkdir(parents=True)
    env=dict(os.environ,TB_OFFLINE='1',TB_STATE_DIR=str(state),TB_PACKAGE_PORT='0',TB_PACKAGE_NO_SYNC='1',
             TB_LIBRARY_DB=str(state/'tb-library.sqlite3'),TB_ARCHIVE_ROOT=str(state/'imports'),
             TB_BACKUP_DIR=str(state/'backups'),AGENT_CP_CONFIG=str(folder/'profile/config.json'))
    service=subprocess.Popen(['node',str(ROOT/'server/leaderboard/tests/local-server.mjs')],stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,text=True,creationflags=NO_WINDOW)
    preparation=None;process=None;observer=None
    try:
        endpoint=json.loads(service.stdout.readline())['endpoint'];env['TB_TEST_ACCOUNTS_ENDPOINT']=endpoint
        ready=folder/'prepare.json';log=(folder/'prepare.log').open('w',encoding='utf8')
        preparation=subprocess.Popen([str(package/'ToBe.exe'),'--serve-account-check',str(ready)],cwd=package,env=env,
                                     stdout=log,stderr=subprocess.STDOUT,creationflags=NO_WINDOW)
        deadline=time.monotonic()+90
        while not ready.is_file():
            assert preparation.poll() is None,'Frozen account preparation exited; inspect prepare.log'
            assert time.monotonic()<deadline,'Frozen account preparation timeout'
            time.sleep(.05)
        prepared=json.loads(ready.read_text('utf8'));assert prepared['ok'] and prepared['frozen'],prepared
        base=prepared['baseUrl'];host=base.removeprefix('http://');token=None
        def call(path,body=None):
            nonlocal token
            connection=http.client.HTTPConnection(host,timeout=45)
            connection.request('GET' if body is None else 'POST','/api/'+path,
                               body=json.dumps(body).encode() if body is not None else None,
                               headers={'Content-Type':'application/json','X-TB-Token':token or '', 'Origin':base})
            response=connection.getresponse();value=json.loads(response.read());connection.close()
            assert response.status==200,(path,response.status,value.get('error'))
            if isinstance(value,dict) and value.get('token'):token=value['token']
            return value
        call('account');login='frozen_'+uuid.uuid4().hex[:12];password='isolated-startup-only'
        call('account/register',{'loginId':login,'nickname':'启动验收','password':password})
        call('account/login',{'loginId':login,'password':password});call('account')
        rows=call('data?compact=1')['rows'];problem=next(row['id'] for row in rows if row['title']=='A+B Problem')
        call('training/start',{'id':problem});code='// preserved frozen startup draft\nint main(){return 0;}'
        call('draft',{'id':problem,'code':code})
        preferences=call('preferences')['preferences'] or {}
        preferences.update(onboardingCompleted=True,onboardingGuideVersion=2,levelNoticeVersion=1,levelNoticeSeen=100)
        call('preferences',{'preferences':preferences});call('data?compact=1');call('account/sync',{})
        ready.with_suffix('.stop').touch();assert preparation.wait(30)==0;preparation=None;log.close()
        # This is persisted configuration of the isolated legacy workspace. The
        # normal constructor must select the same endpoint as the saved session.
        with closing(sqlite3.connect(state/'tb-personal.sqlite3')) as db:
            db.execute('UPDATE ranking_profile SET endpoint=?',(endpoint,));db.commit()
        results=[]
        for number in (1,2):
            phase=folder/f'launch-{number}';phase.mkdir();result={'mode':'normal frozen user loader','frozen':True}
            with socket.socket() as reservation:
                reservation.bind(('127.0.0.1',0));port=reservation.getsockname()[1]
            browser_profile=folder/'profile/cache/tb-web-profile'
            run_env=dict(env,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f'--remote-debugging-port={port} --remote-debugging-address=127.0.0.1 --enable-automation')
            started=time.perf_counter();process=subprocess.Popen([str(package/'ToBeLoader.exe')],cwd=package,env=run_env,creationflags=NO_WINDOW)
            finished=threading.Event();watcher=threading.Thread(target=observe_frame,args=(process.pid,started,finished,result),daemon=True);watcher.start()
            observer=subprocess.Popen(['node',str(ROOT/'frontend/tests/startup-frozen-observer.mjs'),str(port),str(browser_profile),str(phase/'content.png')],
                                      cwd=ROOT/'frontend',stdout=subprocess.PIPE,stderr=(phase/'observer.log').open('w',encoding='utf8'),text=True,encoding='utf8',creationflags=NO_WINDOW)
            line=observer.stdout.readline();result['contentShownMs']=round((time.perf_counter()-started)*1000,2)
            assert line,'Native observer exited; inspect observer.log'
            observation=json.loads(line);assert observation.get('ok'),observation
            result.update(ok=True,trainingTitles=observation['titles'],profileOwnershipVerified=True)
            assert observer.wait(10)==0;observer.stdout.close();observer=None
            pid=int((browser_profile/'instance.pid').read_text('ascii'));assert pid!=os.getpid()
            # The PID is in this freshly created, private profile and belongs
            # to the child of our still-running native loader.
            stop_windows(pid,package/'ToBe.exe');assert process.wait(30)==0;process=None
            finished.set();watcher.join(1);assert 'frameworkVisibleMs' in result,result
            (phase/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
        found=[];submissions=0
        for path in state.rglob('*.sqlite3'):
            if 'backups' in path.relative_to(state).parts:continue
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
                tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if 'drafts' in tables:found.extend(row[0] for row in db.execute('SELECT code FROM drafts WHERE problem_id=?',(problem,)))
                if 'submissions' in tables:submissions+=db.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]
        assert code in found and submissions==0
        result={'ok':True,'frozen':True,'version':prepared['version'],'launches':results,'draftPreserved':True,
                'originalSubmissions':0,'localInstallationChanged':False,'targetMilliseconds':3000,
                'targetMet':all(row['contentShownMs']<=3000 for row in results)}
        (folder/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
        return 0 if result['targetMet'] else 2
    finally:
        if observer is not None:observer.terminate();observer.wait(10)
        if process is not None:
            try:stop_windows(int((folder/'profile/cache/tb-web-profile/instance.pid').read_text('ascii')),package/'ToBe.exe');process.wait(10)
            except (OSError,ValueError,subprocess.TimeoutExpired):process.terminate();process.wait(10)
        if preparation is not None:
            (folder/'prepare.stop').touch()
            try:preparation.wait(15)
            except subprocess.TimeoutExpired:preparation.terminate();preparation.wait(10)
        service.terminate();service.wait(10);service.stdout.close();service.stderr.close()


if __name__=='__main__':raise SystemExit(main())
