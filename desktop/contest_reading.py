"""Read a registered Nowcoder contest in an invisible managed-browser target.

No form filling, cookie export, registration or submission is performed. Raw
HTML stays in memory; the backend persists only its parsed problem statement.
"""
import time
from urllib.parse import urlsplit

from private_contest_reading import source_url
from statement_access import StatementAccessRequired,nowcoder_access_notice
from platform_login import LOGIN_SCRIPT,valid_identity

READ_SCRIPT='(()=>{const identity='+LOGIN_SCRIPT+';const html=document.documentElement.outerHTML;return {url:location.href,ready:document.readyState,identity,html:html.length<=4000000?html:null};})()'

class ContestReading:
    def __init__(self,bridge,current,bind,*,page_factory=None,timeout=20):
        self.bridge,self.current,self.bind=bridge,current,bind
        self.page_factory=page_factory;self.timeout=timeout

    def _current(self,training):
        try:return self.current() is training
        except Exception:return False

    def __call__(self,url,training):
        if not source_url(url):raise ValueError('只允许读取已经核实的牛客比赛原题')
        if not self._current(training):raise RuntimeError('账号已切换，请重新读取比赛')
        target=self.bridge.browser.new_probe_page(url)
        if target is None:raise StatementAccessRequired('请更新原站浏览器并在原站登录、报名后重试题面')
        page=None
        try:
            if self.page_factory is None:
                from external_browser import DevToolsPage
                page=DevToolsPage(target['webSocketDebuggerUrl'],lambda *_:None)
            else:page=self.page_factory(target['webSocketDebuggerUrl'])
            deadline=time.monotonic()+self.timeout
            while not self.bridge.stopping.is_set() and time.monotonic()<deadline:
                if not self._current(training):raise RuntimeError('账号已切换，请重新读取比赛')
                value=page.evaluate(READ_SCRIPT)
                if not isinstance(value,dict) or value.get('url')=='about:blank':
                    self.bridge.stopping.wait(.25);continue
                actual=urlsplit(value.get('url',''))
                expected=urlsplit(url)
                if actual.scheme!='https' or actual.hostname!='ac.nowcoder.com' or actual.username or actual.password or actual.port not in (None,443):
                    raise StatementAccessRequired('请先在原站登录并报名，再重试题面')
                if actual.path!=expected.path:
                    if actual.path.startswith('/login'):raise StatementAccessRequired('请先在原站登录并报名，再重试题面')
                    raise ValueError('原站返回了另一道题目，已停止读取')
                if value.get('ready')=='loading':
                    self.bridge.stopping.wait(.25);continue
                owner=valid_identity(value.get('identity'),'牛客')
                if not owner:raise StatementAccessRequired('请先在原站登录并报名，再重试题面')
                if not self.bind(training,'牛客',owner):raise StatementAccessRequired('原站牛客账号与当前绑定不一致，请切换后重试题面')
                html=value.get('html')
                if not isinstance(html,str):raise ValueError('原站题面超过读取大小限制')
                if nowcoder_access_notice(html):raise StatementAccessRequired('请先在原站报名，再重试题面')
                if 'subject-describe' in html or 'subject-item-title' in html:
                    if not self._current(training):raise RuntimeError('账号已切换，请重新读取比赛')
                    return html
                self.bridge.stopping.wait(.25)
            raise StatementAccessRequired('原站题面尚未就绪，请完成登录、报名或验证后重试')
        finally:
            if page is not None:page.close()
            try:self.bridge.browser.close_page(target['id'])
            except (OSError,RuntimeError,ValueError):pass
            finally:
                controller=target.get('_controller')
                if controller is not None:
                    try:controller.close()
                    except (OSError,RuntimeError,ValueError):pass
