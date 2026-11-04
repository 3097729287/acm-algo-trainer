"""One explicit replay start controls one account-bound original-site VP form."""
import datetime as dt
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from platform_login import LOGIN_SCRIPT,valid_identity
from training import ServiceError,iso,UTC

class VirtualContest:
    def __init__(self,bridge,current,bind,*,page_factory=None,timeout=25):
        self.bridge,self.current,self.bind=bridge,current,bind
        self.page_factory,self.timeout=page_factory,timeout
        root=Path(sys.executable).parent/'resources' if getattr(sys,'frozen',False) else Path(__file__).parent
        self.script=(root/'virtual_contest.js').read_text('utf-8')

    def _current(self,training):
        return self.current() is training and not self.bridge.stopping.is_set()

    def __call__(self,spec,training):
        if not self._current(training):raise ServiceError(409,'账号已切换，请重新开始比赛')
        original=urlsplit(spec['registrationUrl'])
        allowed={'Codeforces':'codeforces.com','QOJ':'qoj.ac','牛客':'ac.nowcoder.com'}
        if original.scheme!='https' or original.hostname!=allowed.get(spec['platform']) or original.username or original.password or original.port not in (None,443):raise ServiceError(400,'原站 VP 地址无效')
        target=self.bridge.browser.new_probe_page(spec['registrationUrl'])
        if target is None:raise ServiceError(503,'请更新原站浏览器后重试 VP')
        page=None;attempted=set();start_ms=None;original_owner=None
        try:
            if self.page_factory:page=self.page_factory(target['webSocketDebuggerUrl'])
            else:
                from external_browser import DevToolsPage
                page=DevToolsPage(target['webSocketDebuggerUrl'],lambda *_:None)
            deadline=time.monotonic()+self.timeout
            while time.monotonic()<deadline:
                if not self._current(training):raise ServiceError(409,'账号已切换，本地比赛尚未开始')
                observed=page.evaluate(LOGIN_SCRIPT)
                handle=valid_identity(observed,spec['platform'])
                if handle:
                    if original_owner and original_owner.casefold()!=handle.casefold():raise ServiceError(409,'原站账号已切换，本地比赛尚未开始')
                    # QOJ has a private local browser identity, not a public
                    # rating binding. Pin that identity for this entire start.
                    if spec['platform']!='QOJ' and not self.bind(training,spec['platform'],handle):raise ServiceError(409,'原站账号与当前绑定不一致')
                    original_owner=handle
                context={'spec':spec,'action':'inspect','startMs':start_ms,'attempted':sorted(attempted)}
                value=page.evaluate(self.script+'\ntbVirtualContest('+json.dumps(context)+')') or {}
                state=value.get('state')
                if state=='duration-mismatch':raise ServiceError(409,'本地比赛时长与原站 VP 不一致，请使用原比赛时长')
                if state in ('login','verification'):
                    self.bridge.browser.new_page(spec['registrationUrl'])
                    raise ServiceError(409,'请在原站完成登录或验证，再开始重现赛')
                if state=='unsupported':
                    if spec['required']:raise ServiceError(409,'原站 VP 入口暂不可用，本地比赛尚未开始')
                    return {'supported':False}
                if state=='confirmed':
                    if not handle:raise ServiceError(409,'原站 VP 账号尚未确认')
                    began=value.get('startedMs')
                    if type(began) not in (int,float):raise ServiceError(409,'原站 VP 计时尚未确认')
                    stamp=dt.datetime.fromtimestamp(began/1000,UTC)
                    return {**{key:spec[key] for key in ('platform','contestId','url')},'confirmed':True,'startedAt':iso(stamp),'deadline':iso(stamp+dt.timedelta(minutes=spec['duration']))}
                intent=value.get('intentKey','start')
                if state=='ready' and intent not in attempted:
                    if not handle:raise ServiceError(409,'请先登录原站并确认绑定账号')
                    # CF registers on minute boundaries. Both clocks use the
                    # same confirmed future start instead of starting locally
                    # while the registration page is still loading.
                    start_ms=((int(time.time()*1000)+15000+59999)//60000)*60000
                    attempted.add(intent)
                    page.evaluate(self.script+'\ntbVirtualContest('+json.dumps({**context,'action':'start','startMs':start_ms})+')')
                self.bridge.stopping.wait(.2)
            raise ServiceError(409,'原站 VP 尚未确认，本地比赛尚未开始；请检查原站后重试')
        finally:
            if page is not None:page.close()
            try:self.bridge.browser.close_page(target['id'])
            except (OSError,RuntimeError,ValueError):pass
            controller=target.get('_controller')
            if controller is not None:controller.close()
