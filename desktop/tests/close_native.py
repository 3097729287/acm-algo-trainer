"""Actual WebView2 close cancellation, local save completion and shutdown."""
import json,sys,threading,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1])]
from close_coordinator import CloseCoordinator

def main():
    import webview
    window=webview.create_window('TB local close fixture',html='<script>window.ready=false;window.addEventListener("tb-before-update",event=>event.detail.waitUntil(new Promise(resolve=>setTimeout(()=>resolve(window.ready),120))));</script><p>Isolated close fixture</p>',hidden=True)
    stopping=threading.Event();closed=threading.Event();result={};errors=[]
    coordinator=CloseCoordinator(window,stopping.set)
    window.events.closing+=coordinator.on_closing
    window.events.closed+=closed.set
    def run():
        try:
            assert window.events.loaded.wait(10),'Fixture did not load'
            window.destroy();time.sleep(.4)
            assert not closed.is_set() and not stopping.is_set(),'A failed local save must cancel native close'
            window.evaluate_js('window.ready=true')
            started=time.monotonic();window.destroy()
            assert closed.wait(3),'Native close did not finish after local save'
            result.update(ok=True,localSaveBarrier=True,cancelledUnsavedClose=True,seconds=round(time.monotonic()-started,3))
        except BaseException as issue:
            errors.append(str(issue));coordinator.approved=True;window.destroy()
    webview.start(run,gui='edgechromium',debug=False)
    if errors:raise AssertionError(';'.join(errors))
    assert result.get('ok') and stopping.is_set()
    print(json.dumps(result))

if __name__=='__main__':main()
