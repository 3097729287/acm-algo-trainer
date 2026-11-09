"""Protocol-4, job-scoped tabs in an already running user browser.

The production connector has no cookie store, native runner or browser opener.
Original-site requests stay in their own page and use its existing session.
"""
from contextvars import copy_context
import datetime as dt
import re
import secrets
import threading
import time
import uuid
from urllib.parse import urlsplit

from browser_bridge import BrowserBridge,TERMINAL,VERDICTS
from official_bridge import LOGIN_HOSTS,submission_target
from official_recovery import nowcoder_binding
from platform_login import valid_identity
from training import ServiceError


class ConnectedBrowserBridge(BrowserBridge):
    transport='browser'

    def __init__(self,base_url,guard=None,on_receipt=None,on_pending=None,on_status=None,current_owner=None,expected_owner=None,on_identity=None,legacy_proof=None,clock=None):
        super().__init__(base_url,guard,on_receipt,on_pending,opener=self._no_open,clock=clock)
        self.stopping=threading.Event();self.on_status=on_status
        self.current_owner=current_owner;self.expected_owner=expected_owner;self.on_identity=on_identity;self.legacy_proof=legacy_proof
        self.owners={};self.brands={};self.contexts={}

    def _current(self,owner):
        return not self.stopping.is_set() and (not self.current_owner or self.current_owner() is owner)

    @staticmethod
    def _no_open(_url):
        raise ServiceError(409,'请先在常用浏览器启用 ToBe 浏览器连接；不会另开独立登录')

    def register_browser(self,body):
        client=body.get('clientId')
        try:uuid.UUID(client)
        except (ValueError,TypeError,AttributeError):raise ServiceError(400,'浏览器连接标识无效')
        if len(client)!=36 or body.get('protocol')!=4:
            raise ServiceError(426,'请加载新版纯标签页浏览器连接；旧版登录同步已停用')
        with self.lock:
            self.clients.setdefault(client,secrets.token_urlsafe(32));self.client_protocols[client]=4
            self.client_versions[client]=str(body.get('extensionVersion',''))[:32]
            self.brands[client]='edge' if body.get('browser')=='edge' else 'chrome'
            return {'key':self.clients[client],'mode':'tabs','protocol':4,'cookieSync':False}

    def sync_browser(self,*_args,**_kwargs):
        raise ServiceError(410,'浏览器会话导出已停用；请使用纯标签页连接')

    def _client(self,platform,expected=None):
        live=[key for key in self.clients if self.client_protocols.get(key)==4 and self.client_windows.get(key)
              and self.clock()-self.client_seen.get(key,-100)<=6]
        matching=[key for key in live if expected and self.owners.get(key,{}).get(platform,'').casefold()==expected.casefold()]
        if len(matching)==1:return matching[0]
        return live[0] if len(live)==1 else None

    def browser_queue(self,body,capability):
        client=body.get('clientId')
        owner=self.current_owner() if self.current_owner else None
        with self.lock:
            expected=self.clients.get(client)
            if not expected or not secrets.compare_digest(expected,str(capability)):
                raise ServiceError(403,'浏览器连接已失效')
            if 'cookies' in body or 'syncPlatforms' in body:
                raise ServiceError(410,'不接受浏览器会话导出')
            self.client_seen[client]=self.clock();self.client_windows[client]=body.get('hasWindow') is True
            hints=body.get('identities',{})
            if not isinstance(hints,dict) or set(hints)-LOGIN_HOSTS.keys():raise ServiceError(400,'浏览器账号提示无效')
            self.owners[client]={platform:handle for platform,value in hints.items() if (handle:=valid_identity(value,platform))}
            self.client_login_states[client]={platform:value.get('state','unknown') for platform,value in hints.items() if isinstance(value,dict)}
            jobs=[]
            for session in self.sessions.values():
                self._expire(session)
                if session.get('released'):continue
                if self.current_owner and session.get('_owner') is not owner:continue
                if session.get('readOnlyRestore'):
                    if not session.get('prepared'):continue
                    if not session.get('preferredClient'):session['preferredClient']=self._client(session['platform'],session.get('expectedOwner'))
                    if session.get('preferredClient')==client and session['status']=='needs_browser':session['status']='judging'
                if session.get('preferredClient')==client and session['status']=='needs_browser' and self.client_windows[client]:session['status']='loading'
                if session.get('preferredClient')!=client or session['status'] in TERMINAL and not (session['status']=='finished' and not session.get('windowClosed')):continue
                if not self.client_windows[client]:continue
                jobs.append({'sessionId':session['sessionId'],'key':session['capability']})
            return {'mode':'tabs','protocol':4,'jobs':jobs}

    def _expire(self,session):
        if session['status'] in TERMINAL:return
        now=self.clock()
        if now-session['createdAt']>900:
            session.update(status='unconfirmed' if session.get('attempted') else 'error',intent=False,
                           message='原站查询已暂停，编号和代码已保留；可重连查询，不会重复提交。')
        elif session.get('preferredClient') and now-self.client_seen.get(session['preferredClient'],-100)>8:
            session.update(status='unconfirmed' if session.get('attempted') else 'needs_browser',
                           message='常用浏览器连接已中断；请恢复原连接，不会改用独立浏览器重交。')

    def _open(self,url,code,title,intent,language='cpp17'):
        target=submission_target(url)
        if not isinstance(code,str) or not code.strip() or len(code.encode())>65536 or language not in ('cpp17','python3'):
            raise ServiceError(400,'请先输入不超过 64 KiB 的代码并选择支持的语言')
        authorization=self.guard(url) if self.guard else None
        context=copy_context()
        owner=self.current_owner() if self.current_owner else None
        expected=self.expected_owner(target['platform']) if self.expected_owner else None
        with self.lock:
            for session in self.sessions.values():
                if session['originalUrl']!=url or session['status'] in TERMINAL:continue
                if session.get('_owner') is not owner or session.get('_authorization')!=authorization:raise ServiceError(409,'原提交属于其它账号或比赛上下文')
                if session['code']!=code or session['language']!=language:raise ServiceError(409,'本题已有原提交，请先核对该次结果')
                if not intent:session.update(autoClose=False,manualWindow=True,revealRequested=True)
                if intent and not session.get('attempted') and session.get('dispatchedAt') is None:
                    client=session.get('preferredClient') or self._client(target['platform'],expected)
                    session.update(preferredClient=client,intent=bool(client),submitRequested=True,status='loading' if client else 'needs_browser')
                return self.status(session['sessionId'])
            if sum(s['status'] not in TERMINAL and not s.get('released') for s in self.sessions.values())>=8:
                raise ServiceError(409,'请先处理尚未结束的原站任务')
            identity='official-'+uuid.uuid4().hex;client=self._client(target['platform'],expected)
            session=dict(target,sessionId=identity,code=code,title=str(title),language=language,
                capability=secrets.token_urlsafe(32),createdAt=self.clock(),createdWall=time.time(),command=0,
                preferredClient=client,intent=bool(intent and client),submitRequested=bool(intent),attempted=False,baseline=[],baselineKnown=False,
                status='loading' if client else 'needs_browser',autoClose=bool(intent),manualWindow=not intent,
                revealRequested=not intent,expectedOwner=expected,_authorization=authorization,
                _owner=owner,
                message='正在使用常用浏览器现有会话。' if client else '请先在常用浏览器加载 ToBe 浏览器连接，再继续；不会另开登录。')
            self.sessions[identity]=session;self.contexts[identity]=context
        return self.status(identity)

    def submit(self,url,code,title,language='cpp17'):return self._open(url,code,title,True,language)
    def open(self,url,code,title,language='cpp17'):return self._open(url,code,title,False,language)

    def status(self,identity):
        with self.lock:
            session=self.sessions.get(identity)
            if not session:raise ServiceError(404,'没有找到原站提交会话')
            self._expire(session)
            value={key:session[key] for key in ('sessionId','platform','url','status','message','submissionId','verdict',
                   'acceptedAt','compiler','autoClose','readOnlyRestore','windowClosed','submission') if key in session}
            if value['status']=='finished' and not session.get('saved'):value['status']='judging'
            return value

    def restore_pending(self,records,owner=None):
        for record in records:
            metadata=record.get('metadata') or {};remote=str(record.get('submissionId') or '')
            if metadata.get('_invalid') or not remote.isdecimal() or int(remote)<=0:continue
            try:target=submission_target(record['url']);accepted=dt.datetime.fromisoformat(record['acceptedAt'])
            except (ValueError,KeyError,TypeError):continue
            if accepted.tzinfo is None:continue
            identity=record['sessionId']
            with self.lock:
                if identity in self.sessions:continue
                self.sessions[identity]=dict(target,sessionId=identity,originalUrl=record['url'],url=record['url'],code=record['code'],
                    language=metadata.get('language') or 'cpp17',submissionId=remote,acceptedAt=record['acceptedAt'],
                    capability=secrets.token_urlsafe(32),createdAt=self.clock(),createdWall=time.time(),command=0,
                    status='needs_browser',intent=False,attempted=True,readOnlyRestore=True,autoClose=True,manualWindow=False,
                    preparingRecovery=True,
                    _owner=owner,_record=dict(record),_authorization=(id(owner),metadata.get('contestId')),
                    message='原提交编号已保留，正在等候常用浏览器连接以恢复查询；不会重交。')
            threading.Thread(target=self._prepare_recovery,args=(identity,),name='tb-tab-recovery',daemon=True).start()

    def _prepare_recovery(self,identity):
        from official_recovery import source_hash
        try:
            with self.lock:s=self.sessions[identity];record=s['_record'];metadata=record.get('metadata') or {}
            if not self._current(s['_owner']):return
            binding=nowcoder_binding(metadata.get('receiptBinding'),record['url']);language=metadata.get('language')
            if not binding or metadata.get('codeSha256')!=source_hash(record['code']):
                proof=self.legacy_proof(record) if self.legacy_proof else None
                if not proof:raise ValueError('Original evidence unavailable')
                binding=proof['binding'];language=proof['language']
                if metadata.get('language') and metadata['language']!=language:raise ValueError('Original language differs')
            if not self._current(s['_owner']):return
            with self.lock:
                s.update(receiptBinding=binding,expectedOwner=binding['owner'],language=language or 'cpp17',
                         prepared=True,_recoveryVerified=True,preferredClient=self._client(s['platform'],binding['owner']))
                s['status']='judging' if s.get('preferredClient') else 'needs_browser';snapshot=dict(s)
            if self.on_pending and not self.on_pending(identity,snapshot):raise ValueError('Binding could not be saved')
        except Exception:
            with self.lock:self.sessions[identity].update(prepared=False,preferredClient=None,status='unconfirmed',intent=False,message='原编号保留，但原提交证据暂未核实；请保持原页面，勿重交。')
        finally:
            with self.lock:self.sessions[identity]['preparingRecovery']=False

    def retry_recovery(self,identity,*,visible=False):
        owner=self.current_owner() if self.current_owner else None
        with self.lock:
            s=self.sessions.get(identity)
            if not s or not s.get('readOnlyRestore'):raise ServiceError(404,'没有找到原提交恢复会话')
            if self.current_owner and owner is not s.get('_owner'):raise ServiceError(403,'请先恢复本次提交所属账号')
            if visible:s.update(manualWindow=True,autoClose=False,revealRequested=True)
            if not s.get('prepared'):
                if not s.get('preparingRecovery'):
                    s['preparingRecovery']=True
                    threading.Thread(target=self._prepare_recovery,args=(identity,),name='tb-recheck-evidence',daemon=True).start()
            else:
                s['preferredClient']=s.get('preferredClient') or self._client(s['platform'],s.get('expectedOwner'))
                s.update(status='judging' if s.get('preferredClient') else 'needs_browser',intent=False)
            return self.status(identity)

    def _guard(self,session):
        if session.get('readOnlyRestore'):return
        if self.guard:
            answer=self.contexts[session['sessionId']].copy().run(self.guard,session['originalUrl'])
            if answer!=session.get('_authorization'):raise ServiceError(403,'本次账号或比赛授权已变化，未发送代码')

    def exchange(self,body,capability):
        # Account checks enter the account barrier before the bridge lock.
        owner=self.current_owner() if self.current_owner else None
        with self.lock:
            session=self._authenticate(body.get('sessionId'),capability)
            if self.current_owner and session.get('_owner') is not owner:raise ServiceError(403,'请先恢复该任务所属的 ToBe 账号')
            if body.get('clientId')!=session.get('preferredClient'):raise ServiceError(403,'任务属于另一个浏览器连接')
            if body.get('claim'):
                session['claimed']=True
                return {'url':session['url'],'sessionId':session['sessionId'],'status':session['status'],
                        'manual':session.get('manualWindow',False),'mode':'tabs'}
            if body.get('closed') is True:
                if session.get('control') and session.get('controlClosed') or session.get('displayAcknowledged') and session.get('saved') and session.get('autoClose'):
                    session['windowClosed']=True;session['released']=True
                return {'ack':True}
            if body.get('released') is True:
                if session.get('manualWindow') and (session.get('saved') or session.get('controlClosed')):session['released']=True
                return {'ack':True}
            page=urlsplit(str(body.get('pageUrl','')))
            if page.scheme!='https' or page.hostname not in LOGIN_HOSTS[session['platform']] or page.port not in (None,443) or page.username or page.password:
                raise ServiceError(403,'只接受本次原站页面')
            session['lastSeen']=self.clock()
            event=body.get('event')
            proof=(event.get('value') or {}).get('identity') if session.get('control') and isinstance(event,dict) and isinstance(event.get('value'),dict) else None
            if proof is None and isinstance(event,dict):proof=event.get('ownerProof')
            handle=valid_identity(proof,session['platform']);expected=session.get('expectedOwner')
            matched=bool(handle and (not expected or expected.casefold()==handle.casefold()))
        # Binding can acquire account/storage locks. Never call it under the
        # bridge lock, including a late receipt after the UI changed account.
        bound=matched and (not self.on_identity or self.on_identity(session['_owner'],session['platform'],handle))
        checkpoint=isinstance(event,dict) and event.get('status')=='submitted' and event.get('attempted') is True and not session.get('attempted')
        if checkpoint:
            if not bound or session.get('dispatchedAt') is None:raise ServiceError(403,'账号或提交授权已变化，尚未点击原站提交')
            # Native forms may have waited tens of seconds for their own lock
            # or verification. Recheck again at the actual pre-click ACK.
            self._guard(session)
        with self.lock:
            if session.get('control'):
                return self._control_exchange(session,event,bound)
            if isinstance(event,dict):
                if bound:
                    session['ownerVerified']=True;session['verifiedOwner']=handle
                    if not expected:session['expectedOwner']=handle
                else:session['ownerVerified']=False
                self._update(session,event,inspection=body.get('inspection') is True)
        self._persist(session['sessionId'])
        with self.lock:
            if session['status']=='finished':
                close=bool(session.get('saved') and session.get('displayAcknowledged') and session.get('autoClose'))
                return {'stop':close or session.get('saved') and not session.get('autoClose'),'closeOwned':close,'status':'finished','awaitingDisplayAck':not close}
            if session['status'] in ('closed','error'):return {'stop':True,'closeOwned':False,'status':session['status']}
            reveal=session['status'] in ('needs_login','needs_verification')
            if isinstance(event,dict):
                answer={'ack':True,'reveal':reveal,'status':session['status']}
                if (event.get('loggedIn') is True and session.get('ownerVerified') and
                        (session.get('readOnlyRestore') or session.get('intent') and not session.get('attempted') and session.get('dispatchedAt') is None)):
                    answer['navigate']=session['url']
                return answer
            action='inspect'
            dispatch=(session.get('intent') and session['status']=='ready' and session.get('ownerVerified')
                and page.path==urlsplit(session['url']).path and not session.get('attempted')
                and session.get('dispatchedAt') is None and not session.get('readOnlyRestore'))
        if dispatch:self._guard(session)
        with self.lock:
            if dispatch and (session.get('attempted') or not session.get('intent') or session.get('dispatchedAt') is not None or session['status']!='ready'):dispatch=False
            if dispatch:
                session.update(intent=False,dispatchedAt=self.clock(),status='submitted');session['command']+=1;action='submit'
            context={key:session.get(key) for key in ('sessionId','platform','problem','code','language','originalUrl','attempted',
                'baseline','baselineKnown','baselineOwner','submissionId','retry','readOnlyRestore','receiptBinding','acceptedAt')}
            context['nativeFormOnly']=True
            context['resumeAfterLogin']=bool(session.get('readOnlyRestore') or session.get('intent') and session.get('dispatchedAt') is None)
            if not session.get('ownerVerified') and session.get('expectedOwner'):context['expectedOwner']=session['expectedOwner']
            return {'context':context,'action':action,'command':session['command'],'reveal':reveal,'status':session['status']}

    def _update(self,session,value,inspection=False):
        status=value.get('status')
        if session['status'] in ('closed','finished') or status not in {'loading','ready','submitted','judging','finished','needs_login','needs_verification','unconfirmed','error','awaiting_submit'}:return
        if session.get('readOnlyRestore') and status=='error':status='unconfirmed'
        remote=str(value.get('submissionId') or session.get('submissionId') or '')
        if remote and (not remote.isascii() or not remote.isdigit() or int(remote)<=0):return
        if session.get('submissionId') and remote!=session['submissionId']:return
        if status=='error' and session.get('attempted') and value.get('attempted') is not False:status='unconfirmed'
        if status in ('judging','finished'):
            if not session.get('ownerVerified') or not session.get('attempted') or not remote.isascii() or not remote.isdigit() or int(remote)<=0:return
            if status=='finished' and value.get('verdict') not in VERDICTS:return
            if session['platform']=='Codeforces' and session.get('baselineKnown') and any(int(remote)<=int(old) for old in (session.get('baseline') or []) if str(old).isdigit()):return
        if session.get('attempted') and status in ('ready','loading','awaiting_submit'):return
        if session.get('submissionId') and status=='submitted':return
        if (not inspection and status in ('loading','needs_login','needs_verification') and value.get('attempted') is False
                and not session.get('attempted') and session.get('submitRequested') and session.get('dispatchedAt') is not None):
            session.pop('dispatchedAt',None);session['intent']=True
        if status in ('needs_login','needs_verification','error') and session.get('attempted'):session['intent']=False
        if status=='ready' and not session.get('ownerVerified'):
            status='needs_login';value={**value,'message':'请在当前浏览器确认本题原站账号，随后继续本次提交。'}
        for key in ('message','compiler','verdictDetail','baseline','baselineKnown','baselineOwner','acceptedAt'):
            if key not in value:continue
            item=value[key]
            if key in ('message','compiler','verdictDetail','baselineOwner'):
                if not isinstance(item,str):continue
                item=item[:500]
            if key=='baselineKnown' and not isinstance(item,bool):continue
            if key=='baseline' and (not isinstance(item,list) or len(item)>1000 or any(not isinstance(v,str) or not v.isascii() or not v.isdigit() for v in item)):continue
            if key=='acceptedAt' and (session.get('readOnlyRestore') or session.get('submissionId') and session.get('acceptedAt')):continue
            session[key]=item
        # The durable pre-click checkpoint is monotonic. A late inspection or
        # page reload can never turn an attempted intent back into a new POST.
        if value.get('attempted') is True:session['attempted']=True
        if value.get('receiptBinding'):
            b=nowcoder_binding(value['receiptBinding'],session['originalUrl'])
            if b:session['receiptBinding']=b
        session['status']=status
        if remote:session['submissionId']=remote
        if session.get('attempted'):session.setdefault('acceptedAt',dt.datetime.now(dt.timezone.utc).isoformat())
        if status=='finished':session['verdict']=value['verdict']

    def _persist(self,identity):
        with self.lock:
            session=self.sessions[identity]
            if session.get('persisting'):return
            session['persisting']=True;snapshot=dict(session)
        try:
            if snapshot.get('submissionId') and self.on_pending:self.on_pending(identity,snapshot)
            if snapshot['status']=='finished' and not snapshot.get('saved'):
                try:saved=self.on_receipt(identity,snapshot) if self.on_receipt else None
                except Exception:saved=None
                with self.lock:
                    if isinstance(saved,dict):session.update(saved=True,receiptSaved=True,submission=saved.get('submission',saved))
                    else:session.update(status='unconfirmed' if session.get('readOnlyRestore') else 'judging',message='原回执保存尚未完成，编号已保留，不会重交。')
        finally:
            with self.lock:
                session['persisting']=False
        if self.on_status:
            try:self.on_status(self.status(identity))
            except Exception:pass

    def acknowledge(self,identity):
        with self.lock:
            s=self.sessions.get(identity)
            if not s:raise ServiceError(404,'没有找到本次提交')
            record=s.get('submission') or {};remote=str(s.get('submissionId') or '')
            if (s['status']!='finished' or not s.get('saved') or not s.get('autoClose') or not remote.isdecimal() or int(remote)<=0 or record.get('scope')!='official'
                    or record.get('mode')!='submit' or record.get('verdict')!=s.get('verdict') or not record.get('finishedAt')
                    or not re.fullmatch(r'official-[0-9a-f]{64}',str(record.get('id') or ''))
                    or not re.match(r'^原站确认提交 #'+remote+r'(?:\s|$)',str(record.get('message') or ''))):return {'closed':False}
            s['displayAcknowledged']=True
            return {'closed':s.get('windowClosed',False),'displayAcknowledged':True}

    def close(self,identity=None):
        with self.lock:
            for key,s in self.sessions.items():
                if identity is None or key==identity:s.update(status='closed',intent=False)
        return {'closed':True}

    def on_closing(self):self.stopping.set()

    def page(self,url,owner,platform,*,manual=False):
        return ConnectedPage(self,self._control_open(url,owner,platform,manual=manual))

    def _control_open(self,url,owner,platform,*,manual=False):
        page=urlsplit(url)
        if platform not in LOGIN_HOSTS or page.scheme!='https' or page.hostname not in LOGIN_HOSTS[platform] or page.username or page.password or page.port not in (None,443):
            raise ServiceError(400,'原站页面地址无效')
        if not self._current(owner):raise ServiceError(409,'账号已切换，请重新打开原站')
        expected=self.expected_owner(platform) if self.expected_owner else None
        with self.lock:
            client=self._client(platform,expected)
            if not client:raise ServiceError(412,'请先在常用浏览器加载 ToBe 浏览器连接；不会另开独立登录')
            identity='page-'+uuid.uuid4().hex
            self.sessions[identity]=dict(sessionId=identity,capability=secrets.token_urlsafe(32),control=True,
                platform=platform,url=url,originalUrl=url,createdAt=self.clock(),status='loading',
                preferredClient=client,expectedOwner=expected,_owner=owner,manualWindow=manual,autoClose=not manual,
                command=0,controlWait=threading.Event(),controlParts={})
            return identity

    def _control_exchange(self,s,event,bound=False):
        if s.get('controlClosed'):
            return {'stop':True,'closeOwned':not s.get('manualWindow'),'status':'finished'}
        if isinstance(event,dict) and event.get('controlCommand')==s.get('command'):
            value=event.get('value')
            if not isinstance(value,dict):return {'ack':False}
            proof=value.get('identity') or event.get('ownerProof')
            handle=valid_identity(proof,s['platform']);expected=s.get('expectedOwner')
            if handle and expected and handle.casefold()!=expected.casefold():
                s.update(status='needs_login',message='当前原站账号与 ToBe 绑定不一致，请切换原站账号。')
                return {'ack':True,'reveal':True,'status':s['status']}
            if handle and not bound:
                s.update(status='needs_login',message='原站账号与当前 ToBe 账号不一致。')
                return {'ack':True,'reveal':True,'status':s['status']}
            if handle and bound and not expected:s['expectedOwner']=handle
            allowed={'url','ready','identity','html','state','startedMs','intentKey'}
            clean={key:item for key,item in value.items() if key in allowed}
            part=event.get('htmlPart')
            if part is not None:
                if (not isinstance(part,dict) or type(part.get('index')) is not int or type(part.get('total')) is not int
                        or not 0<=part['index']<part['total']<=128 or not isinstance(part.get('text'),str) or len(part['text'])>32000):
                    raise ServiceError(400,'题面片段无效')
                parts=s['controlParts'];old=parts.get(part['index'])
                if old is not None and old!=part['text']:raise ServiceError(409,'题面片段已变化，请重新读取')
                if s.get('controlTotal',part['total'])!=part['total']:raise ServiceError(409,'题面片段数已变化')
                parts[part['index']]=part['text'];s['controlTotal']=part['total']
                if sum(len(text.encode()) for text in parts.values())>4000000:raise ServiceError(413,'原站题面超过读取大小限制')
                if len(parts)<part['total']:return {'ack':True}
                clean['html']=''.join(parts[index] for index in range(part['total']))
            s['controlResult']=clean;s['controlWait'].set()
            state=clean.get('state')
            s['status']='needs_verification' if state=='verification' else 'needs_login' if state=='login' or proof and proof.get('state')=='logged_out' else 'ready'
            if s.get('manualWindow'):s['controlClosed']=True
            return {'ack':True,'reveal':s['status'] in ('needs_login','needs_verification'),'status':s['status']}
        request=s.get('controlRequest')
        if not request or s['controlWait'].is_set():return {'ack':True,'status':s['status']}
        if request.get('kind')=='virtual' and request.get('context',{}).get('action')=='start':
            # Starting a VP is also an explicit, single native form action. If
            # the browser disappears after delivery, preserve uncertainty.
            if s.get('controlSent')==s['command']:return {'ack':True,'status':'unconfirmed'}
            s['controlSent']=s['command']
        return {'action':'control','context':{'sessionId':s['sessionId'],'platform':s['platform'],
            'control':request,'controlCommand':s['command'],'expectedOwner':s.get('expectedOwner')},'command':s['command'],'status':s['status']}


class ConnectedPage:
    """Small static page operations; never accepts JavaScript or a request body."""
    def __init__(self,bridge,identity):self.bridge,self.identity=bridge,identity

    def request(self,kind,*,context=None,timeout=20):
        if kind not in ('identity','read','virtual'):raise ValueError('Unsupported page operation')
        bridge=self.bridge
        with bridge.lock:s=bridge.sessions[self.identity]
        if not bridge._current(s['_owner']):raise ServiceError(409,'账号已切换，原站操作已停止')
        with bridge.lock:
            s['command']+=1;s['controlWait'].clear();s['controlParts']={};s.pop('controlTotal',None)
            s['controlRequest']={'kind':kind,**({'context':context} if context is not None else {})}
            wait=s['controlWait']
        deadline=time.monotonic()+timeout
        while not wait.wait(.1):
            if not bridge._current(s['_owner']):raise ServiceError(409,'账号已切换，原站操作已停止')
            if time.monotonic()>=deadline:raise ServiceError(409,'常用浏览器尚未确认原站页面，请检查连接后重试；不会重复点击。')
        if not bridge._current(s['_owner']):raise ServiceError(409,'账号已切换，原站操作已停止')
        return s['controlResult']

    def close(self,*,keep=False):
        with self.bridge.lock:
            s=self.bridge.sessions[self.identity]
            if keep or s['status'] in ('needs_login','needs_verification'):s['manualWindow']=True
            s['controlClosed']=True;s['status']='finished'
