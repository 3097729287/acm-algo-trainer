"""Interactive startup/reattachment on an offline blank page, no real login."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
os.environ['TB_OFFLINE'] = '1'
sys.path[:0] = [str(ROOT / folder) for folder in ('backend', 'backend/common', 'desktop')]
from external_browser import BrowserProcess, DevToolsPage

original = subprocess.Popen
def offline_browser(arguments, **options):
    assert not any(flag in arguments for flag in ('--headless', '--enable-automation', '--remote-debugging-port=0'))
    return original(arguments + ['--disable-background-networking', '--disable-component-update',
        '--disable-extensions', '--disable-sync', '--host-resolver-rules=MAP * ~NOTFOUND'], **options)

with tempfile.TemporaryDirectory(prefix='tb-interactive-browser-') as directory, patch('external_browser.subprocess.Popen', side_effect=offline_browser):
    browser = BrowserProcess(Path(directory) / 'profile')
    page = None
    try:
        browser.ensure(background=True)
        tab = browser.new_page()
        page = DevToolsPage(tab['webSocketDebuggerUrl'], lambda *_:None)
        assert page.evaluate('navigator.webdriver') is False
        assert page.evaluate('location.href') == 'about:blank'
        reattached = BrowserProcess(Path(directory) / 'profile')
        reattached.ensure(background=True)
        assert reattached.port == browser.port
        print(json.dumps({'ok':True,'interactiveBrowser':True,'profileReattachment':True,
                          'offlineBlankOnly':True,'realSiteLogin':False}),flush=True)
    finally:
        if page:
            try: page.call('Browser.close', timeout=2)
            except Exception: pass
            page.close()
        if browser.process:
            try: browser.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                browser.process.terminate()
                browser.process.wait(timeout=10)
