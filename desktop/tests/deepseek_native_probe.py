"""One isolated native window; never import or copy a real browser profile."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / name) for name in ('desktop', 'backend', 'backend/common')]
sys.dont_write_bytecode = True
from embedded_deepseek import DeepSeekPane, TARGET
from native_activity import NativeActivity
import webview

parser = argparse.ArgumentParser()
parser.add_argument('--case', type=Path, required=True)
parser.add_argument('--phase', choices=('seed', 'verify', 'real'), required=True)
parser.add_argument('--origin')
args = parser.parse_args()
case = args.case.resolve(strict=True)
assert case.is_relative_to((ROOT / '.backups').resolve()) and case.drive.upper() == 'E:'
assert not (case / ('result-' + args.phase + '.json')).exists()
assert args.phase == 'real' or args.origin and args.origin.startswith('http://127.0.0.1:')
window = webview.create_window('ToBe isolated DeepSeek ' + args.phase, html='''<!doctype html><style>
html,body{margin:0;height:100%;overflow:hidden;background:#202530;color:white;font:16px sans-serif}
header{height:44px;display:flex;align-items:center;padding:0 12px}main{height:calc(100% - 44px);display:flex}
#left{width:50%;height:100%;background:#283440}textarea{width:50%;box-sizing:border-box;background:#301e40;color:white;resize:none;font:16px monospace}
</style><header>Isolated native pane / code preservation test</header><main><div id="left"></div><textarea id="code">isolated code remains unchanged</textarea></main>''',
    width=1000, height=720, min_size=(640, 480), background_color='#202530')
owner = [('test://local', 'owner-A', 1)]
target = TARGET if args.phase == 'real' else args.origin + ('/seed' if args.phase == 'seed' else '/check')
pane = DeepSeekPane(window, lambda: owner[0], case / ('real-profiles' if args.phase == 'real' else 'local-profiles'),
                    target=target, test_origin=None if args.phase == 'real' else args.origin)
sequence = [0]
activity = NativeActivity(shortcuts=pane.shortcuts)
registration = {'serial': 1, 'bindings': [
    {'route': 'isolated-workbench', 'id': 'workbench-next', 'combo': 'Ctrl+ArrowRight', 'context': 'owned-test'},
    {'route': 'isolated-workbench', 'id': 'toolbar-lock', 'combo': 'Alt+T', 'context': 'owned-test'}]}
report = {'phase': args.phase, 'pid': os.getpid(), 'ok': False, 'ordinaryProgramOrBrowserControlled': False,
          'ordinaryCookiesReadOrCopied': False, 'deepseekLoginAttempted': False, 'chatSent': False,
          'profileRoot': str(case / ('real-profiles' if args.phase == 'real' else 'local-profiles'))}
report['publicMainResponses'] = []
report['publicResourceStatuses'] = {}
report['publicScriptExceptionClasses'] = []
report['publicNetworkFailureCodes'] = []
original_configure = pane._configure
def configured(view):
    original_configure(view)
    if args.phase == 'real':
        core = view.CoreWebView2
        try:
            exception = core.GetDevToolsProtocolEventReceiver('Runtime.exceptionThrown')
            def script_failed(sender, event):
                packet = json.loads(str(event.ParameterObjectAsJson))
                report['publicScriptExceptionClasses'].append(packet.get('exceptionDetails', {}).get('exception', {}).get('className', 'Unknown'))
            exception.DevToolsProtocolEventReceived += script_failed
            failed = core.GetDevToolsProtocolEventReceiver('Network.loadingFailed')
            def network_failed(sender, event):
                import re
                packet = json.loads(str(event.ParameterObjectAsJson));code = packet.get('errorText', '')
                report['publicNetworkFailureCodes'].append(code if re.fullmatch(r'net::ERR_[A-Z_]+', code) else 'OTHER_NETWORK_FAILURE')
            failed.DevToolsProtocolEventReceived += network_failed
            core.CallDevToolsProtocolMethodAsync('Runtime.enable', '{}')
            core.CallDevToolsProtocolMethodAsync('Network.enable', '{}')
        except Exception as error:
            report['diagnosticErrorClass'] = type(error).__name__
    def response(sender, event):
        from urllib.parse import urlsplit
        uri = urlsplit(str(event.Request.Uri))
        if args.phase == 'real':
            key = str(uri.hostname) + ':' + str(event.Response.StatusCode)
            report['publicResourceStatuses'][key] = report['publicResourceStatuses'].get(key, 0) + 1
        if args.phase != 'real' or uri.hostname != 'chat.deepseek.com' or uri.path != '/':
            return
        headers = event.Response.Headers
        def header(name):
            return str(headers.GetHeader(name))[:1000] if headers.Contains(name) else None
        report['publicMainResponses'].append({'status': event.Response.StatusCode,
            'contentType': header('content-type'), 'contentLength': header('content-length'),
            'xFrameOptions': header('x-frame-options'), 'contentSecurityPolicy': header('content-security-policy')})
    view.CoreWebView2.WebResourceResponseReceived += response
pane._configure = configured


def request(visible=True, retry=False):
    geometry = window.evaluate_js('(()=>{const r=document.querySelector("#left").getBoundingClientRect(),x=Math.max(0,r.x),y=Math.max(0,r.y);return {rect:{x,y,width:Math.min(innerWidth,r.right)-x,height:Math.min(innerHeight,r.bottom)-y},viewport:{width:innerWidth,height:innerHeight}}})()')
    report['lastReportedGeometry'] = geometry
    sequence[0] += 1
    return pane.update({'viewId': 'a' * 32, 'sequence': sequence[0], 'ownerKey': pane.snapshot()['ownerKey'],
                        'visible': visible, 'retry': retry, **geometry,
                        **({'shortcuts': registration} if args.phase != 'real' and visible else {})})


def evaluate(script):
    task = pane._ui(lambda: pane.view.CoreWebView2.ExecuteScriptAsync(script))
    assert task.Wait(5000), 'Isolated view script timed out'
    return json.loads(str(task.Result))


def wait_ready():
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        state = request()
        if state['status'] == 'ready':
            return state
        if state['status'] == 'error':
            raise RuntimeError(state['errorCode'])
        time.sleep(.15)
    raise TimeoutError('Native page did not become ready')


def marker():
    return evaluate('({cookie:document.cookie.includes("tb_deepseek_probe=kept"),storage:localStorage.getItem("tb-deepseek-probe")==="kept"})')


def bounds():
    return pane._ui(lambda: {'x': pane.panel.Left, 'y': pane.panel.Top, 'width': pane.panel.Width,
        'height': pane.panel.Height, 'visible': pane.panel.Visible, 'parentIsMainWindow': pane.panel.Parent.Handle == window.native.Handle,
        'hostWidth': window.native.browser.webview.ClientSize.Width,
        'hostHeight': window.native.browser.webview.ClientSize.Height, 'deviceDpi': window.native.DeviceDpi})


def run():
    try:
        assert window.events.loaded.wait(15), 'Isolated main WebView did not load'
        activity.start(*pane._ui(lambda: (window.native.Handle.ToInt64(), window.native.browser.webview.Handle.ToInt64())))
        assert activity.ready.wait(3) and activity.snapshot()['available'], 'Native input hooks did not start'
        wait_ready()
        report['initialBounds'] = bounds()
        assert report['initialBounds']['visible'] and report['initialBounds']['parentIsMainWindow']
        if args.phase != 'real':
            import ctypes
            from ctypes import wintypes as W
            injected = [0]
            observe = activity._observe
            def observed(kind, flags, owned):
                if kind == 'mouse' and flags & 0x03 or kind == 'keyboard' and flags & 0x12:
                    injected[0] += 1
                return observe(kind, flags, owned)
            activity._observe = observed
            pane._ui(lambda: (window.native.Activate(), pane.view.Focus()))
            user = ctypes.WinDLL('user32', use_last_error=True)
            user.GetForegroundWindow.restype = W.HWND
            user.SetForegroundWindow.argtypes = [W.HWND]
            user.SetForegroundWindow(activity.hwnd)
            time.sleep(.2)
            foreground = user.GetForegroundWindow()
            report['isolatedForeground'] = {'present': bool(foreground), 'owned': foreground == activity.hwnd}
            before = activity.snapshot()
            window.evaluate_js('document.dispatchEvent(new KeyboardEvent("keydown",{key:"x",bubbles:true}));document.dispatchEvent(new MouseEvent("mousemove",{bubbles:true}));')
            user.mouse_event.argtypes = [W.DWORD, W.DWORD, W.DWORD, W.DWORD, ctypes.c_size_t]
            # Zero displacement: exercise actual injected LL-hook provenance
            # without clicking, typing or moving the user's pointer.
            if foreground == activity.hwnd:
                user.mouse_event(1, 0, 0, 0, 0)
            # Some drivers coalesce a zero-distance mouse event. F24 is an
            # unregistered, unused test key, sent only to this owned window.
            user.keybd_event.argtypes = [W.BYTE, W.BYTE, W.DWORD, ctypes.c_size_t]
            if foreground == activity.hwnd:
                user.keybd_event(0x87, 0, 0, 0)
                user.keybd_event(0x87, 0, 2, 0)
            deadline = time.monotonic() + 2
            while foreground == activity.hwnd and not injected[0] and time.monotonic() < deadline:
                time.sleep(.02)
            after = activity.snapshot()
            if foreground == activity.hwnd:
                assert injected[0] > 0, 'Windows did not deliver the injected test event'
            assert after['revision'] == before['revision'], 'Synthetic input/focus must not create activity'
            report['nativeActivity'] = {'available': after['available'], 'actualInjectedNativeEventsRejected': injected[0],
                'syntheticDomInputAndProgrammaticFocusRejected': True, 'revisionUnchanged': True,
                'injectedEventCheckSkippedUnlessOwnedForeground': foreground != activity.hwnd,
                'physicalHardwarePositiveClaimed': False, 'snapshotFields': sorted(after)}
            # The native child is a separate HWND branch from the main DOM.
            # Verify the actual Windows ownership/focus boundary, then exercise
            # the command state machine explicitly as a synthetic unit input.
            class GUIThread(ctypes.Structure):
                _fields_ = [('size', W.DWORD), ('flags', W.DWORD), ('active', W.HWND), ('focus', W.HWND),
                            ('capture', W.HWND), ('menu', W.HWND), ('move', W.HWND), ('caret', W.HWND), ('rect', W.RECT)]
            user.GetGUIThreadInfo.argtypes = [W.DWORD, ctypes.POINTER(GUIThread)]
            user.IsChild.argtypes, user.IsChild.restype = [W.HWND, W.HWND], W.BOOL
            user.GetAncestor.argtypes, user.GetAncestor.restype = [W.HWND, W.UINT], W.HWND
            user.GetWindowThreadProcessId.argtypes, user.GetWindowThreadProcessId.restype = [W.HWND, ctypes.POINTER(W.DWORD)], W.DWORD
            info = GUIThread();info.size = ctypes.sizeof(info)
            main, host = pane._ui(lambda: (window.native.Handle.ToInt64(), window.native.browser.webview.Handle.ToInt64()))
            own_thread = user.GetWindowThreadProcessId(main, None)
            assert user.GetGUIThreadInfo(own_thread, ctypes.byref(info))
            assert info.focus and user.GetAncestor(info.focus, 3) == main
            assert info.focus != host and not user.IsChild(host, info.focus)
            assert pane.shortcuts.key(39, 0, child_owned=True, control=True)
            assert pane.shortcuts.key(39, 0, child_owned=True, control=True)
            commands = pane.shortcut_snapshot()
            assert commands['registration'] == registration['serial'] and len(commands['actions']) == 1
            assert commands['actions'][0]['id'] == 'workbench-next'
            pane.shortcuts.key(39, 128, child_owned=True, control=True)
            report['nativeShortcutBoundary'] = {'actualOwnedChildFocusOutsideMainDom': True,
                'sameRegisteredCommandAndRepeatDeduplication': True,
                'commandInputExplicitlySynthetic': True, 'physicalHardwarePositiveClaimed': False}
            if args.phase == 'seed':
                # Crash only this isolated child renderer, through its own
                # CoreWebView2 object. Never discover or terminate other PIDs.
                task = pane._ui(lambda: pane.view.CoreWebView2.CallDevToolsProtocolMethodAsync('Page.crash', '{}'))
                try:
                    task.Wait(3000)
                except Exception:
                    pass  # A disconnected renderer is the intended trigger.
                deadline = time.monotonic() + 5
                while pane.snapshot()['status'] != 'error' and time.monotonic() < deadline:
                    time.sleep(.05)
                assert pane.snapshot()['status'] == 'error' and not pane.snapshot()['visible'], 'A failed renderer must hide'
                request(retry=True)
                wait_ready()
                assert marker() == {'cookie': True, 'storage': True}
                report['failedRendererHiddenAndRecreatedWithSameProfile'] = True
        if args.phase == 'real':
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                request()
                report['publicPage'] = evaluate('({origin:location.origin,title:document.title,ready:document.readyState,bodyCharacters:document.body?.innerText.length||0,deepseekLabel:/deepseek/i.test(document.title+" "+(document.body?.innerText||"")),signInVisible:/sign in|log in|登录|注册/i.test(document.body?.innerText||""),inputVisible:[...document.querySelectorAll("input,textarea,[contenteditable=true]")].some(n=>n.getClientRects().length>0),challengeVisible:/verify you are human|checking your browser|请完成验证/i.test(document.body?.innerText||"")})')
                if report['publicPage']['bodyCharacters'] > 20 and report['publicPage']['deepseekLabel'] and (report['publicPage']['inputVisible'] or report['publicPage']['signInVisible']):
                    break
                time.sleep(.3)
            assert report['publicPage']['origin'] == 'https://chat.deepseek.com'
            assert report['publicPage']['bodyCharacters'] > 20 and report['publicPage']['deepseekLabel'], 'A blank view is not usable rendering'
            assert report['publicPage']['inputVisible'] or report['publicPage']['signInVisible'], 'A real input or sign-in entrance must be visible'
            report['realPageRendered'] = True
            from System.IO import FileStream, FileMode
            from Microsoft.Web.WebView2.Core import CoreWebView2CapturePreviewImageFormat
            screenshot = case / 'deepseek-public-page.png'
            stream = FileStream(str(screenshot), FileMode.CreateNew)
            try:
                capture = pane._ui(lambda: pane.view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, stream))
                assert capture.Wait(8000), 'Owned public page screenshot timed out'
            finally:
                stream.Dispose()
            import hashlib
            report['publicPageScreenshotSha256'] = hashlib.sha256(screenshot.read_bytes()).hexdigest()
        else:
            report['persistedMarkersBeforeOwnerChange'] = marker()
            assert report['persistedMarkersBeforeOwnerChange'] == {'cookie': True, 'storage': True}
            request(False)
            assert not pane.snapshot()['visible']
            assert window.evaluate_js('document.querySelector("#code").value') == 'isolated code remains unchanged'
            request()
            window.resize(1120, 780)
            time.sleep(.3)
            request()
            report['resizedBounds'] = bounds()
            assert report['resizedBounds']['width'] <= report['resizedBounds']['hostWidth'] // 2 + 1
            pane._ui(lambda: setattr(window.native.browser.webview, 'ZoomFactor', 1.25))
            time.sleep(.3)
            request()
            report['zoomedBounds'] = bounds()
            assert report['zoomedBounds']['width'] <= report['zoomedBounds']['hostWidth'] // 2 + 1
            window.minimize()
            time.sleep(.4)
            assert not pane.snapshot()['visible']
            window.restore()
            time.sleep(.3)
            request()
            if args.phase == 'verify':
                stale = pane.snapshot()['ownerKey']
                owner[0] = ('test://local', 'owner-B', 1)
                time.sleep(.3)
                assert not pane.snapshot()['visible']
                wait_ready()
                # The seed URL was used only by the first process. This phase
                # navigates /check, which never writes cookies or localStorage.
                report['otherOwnerMarkers'] = marker()
                assert report['otherOwnerMarkers'] == {'cookie': False, 'storage': False}
                assert pane.snapshot()['ownerKey'] != stale
            report['codeCheck'] = window.evaluate_js('({present:!!document.querySelector("#code"),expected:document.querySelector("#code")?.value==="isolated code remains unchanged",characters:document.querySelector("#code")?.value.length,ready:document.readyState})')
            report['codePreserved'] = bool(report['codeCheck'] and report['codeCheck']['expected'])
            assert report['codePreserved'], 'The isolated host code must remain unchanged'
        report['ok'] = True
    except Exception as error:
        report.update(errorClass=type(error).__name__, errorStatus=getattr(error,'status',None), errorCode=str(error) if type(error) in (AssertionError, TimeoutError) else type(error).__name__, nativeStatus=pane.snapshot(),nativeInputAvailable=activity.snapshot()['available'])
    finally:
        activity.close()
        report['finishedAtUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Never put the opaque owner capability into a public receipt.
        if isinstance(report.get('nativeStatus'), dict):
            report['nativeStatus'].pop('ownerKey', None)
        (case / ('result-' + args.phase + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        pane.close()
        window.destroy()


print(json.dumps({'probeStarted': True, 'pid': os.getpid(), 'phase': args.phase, 'case': str(case)}), flush=True)
webview.start(run, gui='edgechromium', private_mode=False, storage_path=str(case / ('host-' + args.phase)), debug=False)
print(json.dumps({'phase': args.phase, 'ok': report['ok'], 'receipt': str(case / ('result-' + args.phase + '.json'))}), flush=True)
raise SystemExit(0 if report['ok'] else 1)
