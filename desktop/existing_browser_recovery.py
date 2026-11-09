"""Harvest historical job evidence from an already running ToBe profile only.

This module never launches a browser, reads a cookie, changes a page or queries
an original-site result. A connected current browser must separately prove owner.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener,ProxyHandler,HTTPRedirectHandler

from browser_endpoint import candidates
from external_browser import DevToolsPage,browsers
from official_recovery import legacy_nowcoder_proof


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*_args,**_kwargs):return None


def existing_job_proof(root,record):
    if not record.get('url','').startswith('https://ac.nowcoder.com/acm/problem/'):
        return None
    opener=build_opener(ProxyHandler({}),_NoRedirect())
    for name,executable in browsers().items():
        profile=Path(root)/('interactive-'+name);active=profile/'DevToolsActivePort'
        if not executable or not active.is_file():continue
        try:
            lines=active.read_text(encoding='utf-8').splitlines();port=int(lines[0])
            if len(lines)!=2 or not 1<=port<=65535:continue
            def read(path):
                with opener.open('http://127.0.0.1:'+str(port)+path,timeout=3) as response:return json.loads(response.read(2000000))
            version=read('/json/version');endpoint=urlsplit(version['webSocketDebuggerUrl'])
            if endpoint.scheme!='ws' or endpoint.hostname not in ('127.0.0.1','localhost') or endpoint.port!=port or endpoint.path!=lines[1]:continue
            inspector=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
            try:pid=next((p['id'] for p in inspector.call('SystemInfo.getProcessInfo')['processInfo'] if p.get('type')=='browser'),None)
            finally:inspector.close()
            if not any(candidate_pid==pid and candidate_port==port for candidate_pid,candidate_port in candidates(profile,executable)):continue
            for target in read('/json/list'):
                if target.get('type')!='page' or target.get('url')!=record['url']:continue
                page=DevToolsPage(target['webSocketDebuggerUrl'],lambda *_:None)
                try:proof=legacy_nowcoder_proof(page,record,require_current_owner=False)
                finally:page.close()
                if proof:return proof
        except (OSError,ValueError,KeyError,TypeError,RuntimeError):continue
    return None
