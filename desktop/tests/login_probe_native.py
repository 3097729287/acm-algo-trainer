"""Check invisible login probes in a disposable real managed browser.

Only a loopback page is opened. No account, original OJ or existing profile is
used. The result proves the installed Chromium supports a windowless target.
"""
from contextlib import closing
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json,os
from pathlib import Path
import sys,tempfile,threading,time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'desktop'),str(ROOT/'backend'),str(ROOT/'backend/common')]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'<title>Disposable login probe fixture</title><h1 id="ready">Loopback only</h1>'
        self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*_):pass

def main():
    with tempfile.TemporaryDirectory(prefix='tb-hidden-probe-') as directory:
        os.environ['TB_OFFLINE']='1';os.environ['TB_STATE_DIR']=str(Path(directory)/'state')
        from external_browser import BrowserProcess,DevToolsPage
        browser=BrowserProcess(Path(directory)/'browser')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        target=None;control=None
        try:
            target=browser.new_probe_page(f'http://127.0.0.1:{server.server_port}/')
            assert target is not None,'Installed Chromium does not support invisible login probes'
            control=target['_controller']
            with closing(DevToolsPage(target['webSocketDebuggerUrl'],lambda *_:None)) as page:
                deadline=time.monotonic()+5
                while page.evaluate('document.querySelector("#ready")?.textContent')!='Loopback only':
                    if time.monotonic()>deadline:raise AssertionError('Hidden page did not load')
                    time.sleep(.05)
                try:
                    window=control.call('Browser.getWindowForTarget',{'targetId':target['id']})
                except RuntimeError:
                    window={}
                assert not window.get('windowId'),'Login probe owns a visible browser window'
            browser.close_page(target['id'])
            print(json.dumps({'ok':True,'windowlessProbe':True,'existingProfilesUsed':False,'originalSiteRequests':False}))
        finally:
            if control:
                try:control.call('Browser.close')
                except Exception:pass
                control.close()
            if browser.process:
                try:browser.process.wait(timeout=10)
                except Exception:pass
            server.shutdown();server.server_close()

if __name__=='__main__':main()
