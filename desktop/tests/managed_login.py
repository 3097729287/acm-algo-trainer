"""Headless managed-browser restart with synthetic cookies and no OJ navigation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
for folder in ('backend', 'backend/common', 'desktop'):
    sys.path.insert(0, str(ROOT / folder))
from external_browser import BrowserProcess, DevToolsPage
from browser_login_memory import BrowserLoginMemory
from persistence import load_document

original_popen = subprocess.Popen
def headless(arguments, **options):
    return original_popen(arguments + ['--headless=new', '--disable-background-networking', '--disable-component-update',
                          '--disable-extensions', '--disable-sync', '--host-resolver-rules=MAP * ~NOTFOUND'], **options)

def close_browser(browser, page):
    try: page.call('Browser.close', timeout=2)
    except Exception: pass
    page.close()
    if browser.process:
        browser.process.wait(timeout=15)
    time.sleep(1.2)

with tempfile.TemporaryDirectory(prefix='tb-managed-restart-') as directory, patch('external_browser.subprocess.Popen', side_effect=headless):
    profile = Path(directory) / 'browser'
    first = BrowserProcess(profile)
    first.ensure()
    page = DevToolsPage(first.request('/json/version')['webSocketDebuggerUrl'], lambda *_: None)
    cookie = dict(name='tb-fixture-session', value='synthetic-only', domain='.nowcoder.com', path='/', secure=True, httpOnly=True)
    page.call('Storage.setCookies', {'cookies': [cookie]})
    memory = BrowserLoginMemory(profile.parent)
    deadline = time.monotonic() + 6
    while not load_document(memory.path, None) and time.monotonic() < deadline:
        time.sleep(.15)
    time.sleep(1.2)
    assert 'synthetic-only' not in load_document(memory.path, '')
    close_browser(first, page)
    second = BrowserProcess(profile)
    second.ensure()
    page = DevToolsPage(second.request('/json/version')['webSocketDebuggerUrl'], lambda *_: None)
    assert any(item['name'] == cookie['name'] and item['value'] == cookie['value'] for item in page.call('Storage.getCookies')['cookies'])
    close_browser(second, page)
    print(json.dumps({'ok': True, 'managedBrowserRestart': True, 'encryptedLoginMemory': True, 'realSiteNavigation': False}))
