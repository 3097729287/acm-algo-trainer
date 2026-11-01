"""Serve the real built UI immediately while the local backend initializes once.

No account, database, password or migration work belongs in this small host.
The normal authenticated handler remains the only authority for all API calls.
"""
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
import json
from pathlib import Path
import threading
from urllib.parse import unquote, urlsplit

class _Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def _json(self,status,raw):
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def _handle(self):
        port=self.server.server_address[1]
        if self.headers.get('Host','').lower() not in {f'127.0.0.1:{port}',f'localhost:{port}'}:
            return self._json(403,b'{"error":"Local requests only"}')
        path=unquote(urlsplit(self.path).path)
        if not path.startswith('/api/'):
            if self.command not in {'GET','HEAD'}:return self._json(405,b'{}')
            file=(self.server.root/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            if not file.is_relative_to(self.server.root) or not file.is_file():return self._json(404,b'{}')
            raw=file.read_bytes();self.send_response(200)
            self.send_header('Content-Type',mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-cache')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            if self.command!='HEAD':self.wfile.write(raw)
            return
        target=self.server.target
        if target is None:
            if path=='/api/account' and self.command=='GET':
                value={'required':True,'authenticated':False,'restoring':bool(self.server.resume_expected and not self.server.failed)}
                if self.server.failed:value['error']='ToBe 启动失败，请关闭后重新打开；本机数据已保留'
                return self._json(200,json.dumps(value,ensure_ascii=False).encode('utf8'))
            return self._json(503,b'{"error":"ToBe is starting"}')
        try:
            length=int(self.headers.get('Content-Length','0'))
            maximum=32*1024*1024 if path in {'/api/training-lists/add','/api/training-lists/save'} else 262144
            if length<0 or length>maximum:return self._json(413,b'{}')
            body=self.rfile.read(length) if length else None
            headers={key:value for key,value in self.headers.items() if key.lower() not in {'host','connection','transfer-encoding'}}
            headers['Host']=f'127.0.0.1:{target.server_address[1]}'
            connection=HTTPConnection('127.0.0.1',target.server_address[1],timeout=65)
            try:
                connection.request(self.command,self.path,body,headers)
                response=connection.getresponse();raw=response.read(40*1024*1024+1)
                if len(raw)>40*1024*1024:raise ValueError('Local response too large')
                self.send_response(response.status)
                for key,value in response.getheaders():
                    if key.lower() not in {'connection','transfer-encoding','content-length','server','date'}:self.send_header(key,value)
                self.send_header('Content-Length',str(len(raw)));self.end_headers()
                if self.command!='HEAD':self.wfile.write(raw)
            finally:connection.close()
        except (OSError,ValueError):self._json(503,b'{"error":"ToBe local service unavailable"}')
    do_GET=do_POST=do_OPTIONS=do_HEAD=_handle

class _Server(ThreadingHTTPServer):
    # WebView hydrates several independent panels at once. Windows refuses a
    # new loopback connection when the default five-slot accept queue is full.
    request_queue_size=64

class EarlyWindow:
    def __init__(self,root,port=0,*,resume_expected=True):
        try:self.server=_Server(('127.0.0.1',port),_Handler)
        except OSError:self.server=_Server(('127.0.0.1',0),_Handler)
        self.server.daemon_threads=True;self.server.root=Path(root).resolve()
        self.server.target=None;self.server.failed=False
        self.server.resume_expected=resume_expected
        self.url=f'http://127.0.0.1:{self.server.server_address[1]}'
        self.thread=threading.Thread(target=self.server.serve_forever,name='tb-window-host',daemon=True);self.thread.start()
    def activate(self,backend):
        backend.frontend_origins=frozenset([*backend.frontend_origins,self.url])
        self.server.target=backend
    def fail(self):self.server.failed=True
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join(2)
