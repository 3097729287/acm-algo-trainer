"""Native official submission in a docked WebView2 on the existing main Form."""
from __future__ import annotations
import datetime as dt
import json
import logging
import threading
import uuid
import sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urlencode

HOSTS={'codeforces.com':'Codeforces','www.codeforces.com':'Codeforces','atcoder.jp':'AtCoder','ac.nowcoder.com':'牛客','www.luogu.com.cn':'洛谷','luogu.com.cn':'洛谷'}
LOGIN_HOSTS={'Codeforces':{'codeforces.com','www.codeforces.com'},'AtCoder':{'atcoder.jp'},'牛客':{'ac.nowcoder.com','nowcoder.com','www.nowcoder.com'},'洛谷':{'www.luogu.com.cn','luogu.com.cn','login.luogu.com.cn'}}
STATUSES={'loading','needs_login','needs_verification','ready','submitted','judging','finished','error','closed','hidden'}

def submission_target(url):
    import re
    p=urlsplit(url or '');platform=HOSTS.get((p.hostname or '').lower());problem='';path=p.path
    if not platform or p.scheme not in ('https','http') or p.username or p.password or p.port not in (None,80,443):raise ValueError('只能打开题库中四个竞赛平台的官方题目地址')
    if platform=='Codeforces':
        m=re.fullmatch(r'/(contest|gym)/(\d+)/problem/([A-Za-z]\d?)',path)
        if m:kind,contest,problem=m.groups();path=f'/{kind}/{contest}/submit'
        else:
            m=re.fullmatch(r'/problemset/problem/(\d+)/([A-Za-z]\d?)',path)
            if not m:raise ValueError('Codeforces 题目地址无效')
            contest,problem=m.groups();path=f'/contest/{contest}/submit'
    elif platform=='AtCoder':
        m=re.fullmatch(r'/contests/([\w-]+)/tasks/([\w-]+)',path)
        if not m:raise ValueError('AtCoder 题目地址无效')
        contest,problem=m.groups();path=f'/contests/{contest}/submit'
    elif platform=='牛客':
        if not re.fullmatch(r'/acm/contest/\d+/[A-Za-z]\d?',path):raise ValueError('牛客题目地址无效')
        problem=path.rsplit('/',1)[-1]
    elif not re.fullmatch(r'/problem/[A-Za-z0-9_]+',path):raise ValueError('洛谷题目地址无效')
    query=urlencode({'taskScreenName':problem}) if platform=='AtCoder' else ''
    return {'platform':platform,'url':urlunsplit(('https',p.netloc,path,query,'submit' if platform=='洛谷' else '')),'problem':problem,'originalUrl':url}

def page_script(session,action='inspect'):
    context=json.dumps({k:session.get(k) for k in ('sessionId','platform','problem','code','originalUrl','attempted','baseline','baselineKnown','baselineOwner')},ensure_ascii=True)
    asset_root=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
    languages=(asset_root/'official_languages.js').read_text(encoding='utf-8')
    nowcoder=(asset_root/'official_nowcoder.js').read_text(encoding='utf-8')
    return r'''(()=>{
const ctx=CONTEXT,action=ACTION;
COMPILER_SELECTION
NOWCODER_RECEIPTS
const ncReceipt=installNowcoderReceipts(ctx);

const send=value=>{chrome.webview.postMessage(JSON.stringify({tbOfficial:true,sessionId:ctx.sessionId,...value}));return value;};
const visible=e=>e&&e.getClientRects().length>0;
const editors=()=>[...document.querySelectorAll('textarea')].filter(e=>/source|code|editor/i.test((e.name||'')+' '+(e.id||'')));
const hasEditor=()=>editors().length||document.querySelector('.CodeMirror,.ace_editor,.monaco-editor');
const login=()=>[...document.querySelectorAll('input[type=password]')].some(visible)||/\/login|\/enter(?:\/|$)|\/auth\/login/i.test(location.pathname);
const verification=()=>!hasEditor()&&(/just a moment|checking your browser|人机验证|安全验证|验证码/i.test(document.title+' '+(document.body?.innerText||'').slice(0,1200))||[...document.querySelectorAll('iframe')].some(e=>visible(e)&&/captcha|challenge/i.test(e.src)));
function normal(text){
text=(text||'').trim().replace(/_/g,' ').replace(/\s+/g,' ');
const map={'AC':'AC','OK':'AC','ACCEPTED':'AC','通过':'AC','WA':'WA','WRONG ANSWER':'WA','答案错误':'WA','TLE':'TLE','TIME LIMIT EXCEEDED':'TLE','超时':'TLE','MLE':'MLE','MEMORY LIMIT EXCEEDED':'MLE','内存超限':'MLE','RE':'RE','RUNTIME ERROR':'RE','运行错误':'RE','CE':'CE','COMPILATION ERROR':'CE','COMPILE ERROR':'CE','编译错误':'CE','OLE':'OLE','OUTPUT LIMIT EXCEEDED':'OLE'};
const exact=map[text.toUpperCase()];if(exact)return exact;
for(const [label,value] of Object.entries(map))if(label.length>3&&new RegExp('^'+label+'(?:\\s+(?:on|in|at)\\b|$)','i').test(text))return value;
return /^(WJ|WR|TESTING|Judging|Running|Waiting|Pending|Queuing|评测中|等待评测)(\b|$)/i.test(text)?'JUDGING':null;
}
function taskPath(path){return path.replace(/^\/problemset\/problem\/(\d+)\/([A-Za-z]\d?)$/,'/contest/$1/problem/$2');}
function receipts(doc=document){const rows=[];doc.querySelectorAll('tr').forEach(row=>{const links=[...row.querySelectorAll('a[href]')];const a=links.find(a=>/\/submission(?:s)?\/\d+/.test(a.getAttribute('href')||''));if(!a)return;const id=(a.getAttribute('href')||'').match(/\/submission(?:s)?\/(\d+)/)?.[1];const task=links.some(a=>{try{const target=new URL(a.getAttribute('href'),location.href),original=new URL(ctx.originalUrl);return target.origin===location.origin&&taskPath(target.pathname)===taskPath(original.pathname)}catch{return false}});const owner=!ctx.baselineOwner||links.some(a=>{try{const link=new URL(a.getAttribute('href'),location.href);return link.origin===location.origin&&link.pathname==='/profile/'+ctx.baselineOwner}catch{return false}});const verdict=[...row.querySelectorAll('.label,.submissionVerdictWrapper,.verdict,[data-verdict],.verdict-accepted,.verdict-rejected,.status-cell')].map(e=>normal(e.getAttribute('data-verdict')||e.getAttribute('verdict')||e.textContent)).find(Boolean);if(id&&task&&owner)rows.push({id,verdict});});return rows;}
function newerReceipt(id,baseline){
if(!/^\d+$/.test(id))return false;
const previous=[...baseline].filter(value=>/^\d+$/.test(value));
return !baseline.has(id)&&previous.every(value=>BigInt(id)>BigInt(value));
}
function inspect(){
if(login())return {status:'needs_login',message:'请在当前官方面板登录，然后明确点击“提交到官方”重试。'};
if(verification())return {status:'needs_verification',message:'原站要求 CAPTCHA 或登录验证，请在当前面板完成后重试。'};
if(ncReceipt?.receipt)return ncReceipt.receipt;
if(ctx.attempted&&ctx.baselineKnown){const baseline=new Set(ctx.baseline||[]);const receipt=receipts().find(r=>newerReceipt(r.id,baseline));if(receipt?.verdict)return {status:receipt.verdict==='JUDGING'?'judging':'finished',submissionId:receipt.id,verdict:receipt.verdict==='JUDGING'?undefined:receipt.verdict,message:receipt.verdict==='JUDGING'?'原站已接收，正在评测。':'已读取原站本次新提交结果：'+receipt.verdict};}
return hasEditor()?{status:ctx.attempted?'submitted':'ready',message:ctx.attempted?'提交操作已发出，等待可靠原站回执；暂不宣称通过。':'官方编辑器已就绪；提交使用原站正常控件。'}:{status:ctx.attempted?'submitted':'loading',message:ctx.attempted?'等待原站回执；无可靠结果时不宣称通过。':'正在加载原站，可在当前面板登录或进入提交页。'};
}
async function submit(){
const state=inspect();if(['needs_login','needs_verification'].includes(state.status))return send(state);
if(!hasEditor())return send({status:'error',message:'没有找到原站代码编辑器，请进入本题提交页；不会点击其它表单。'});
let task=!ctx.problem,filled=0;
document.querySelectorAll('select').forEach(s=>{const field=(s.name||s.id||'').toLowerCase();if(/problem|task/.test(field)&&ctx.problem){const o=[...s.options].find(o=>o.value===ctx.problem);if(o){s.value=o.value;s.dispatchEvent(new Event('change',{bubbles:true}));task=true;}}});
if(['牛客','洛谷'].includes(ctx.platform))task=location.pathname===new URL(ctx.originalUrl).pathname;
if(!task)return send({status:'error',message:'未能准确选定本题，已停止；请在原站确认题目。'});
const compiler=await selectOfficialCompiler(ctx.code,ctx.platform);
if(!compiler)return send({status:'error',message:'没有找到支持当前代码的 C++17 / C++20 / C++23 编译器，请在原站确认语言后重试。'});
editors().forEach(e=>{Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,ctx.code);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));filled++;});
document.querySelectorAll('.CodeMirror').forEach(e=>{if(e.CodeMirror){e.CodeMirror.setValue(ctx.code);filled++;}});document.querySelectorAll('.ace_editor').forEach(e=>{try{if(window.ace){window.ace.edit(e).setValue(ctx.code,-1);filled++;}}catch{}});try{window.monaco?.editor?.getModels?.().filter(m=>!m.isDisposed()&&/cpp|c\+\+/.test(m.getLanguageId?.()||'')).forEach(m=>{m.setValue(ctx.code);filled++;});}catch{}
if(!filled)return send({status:'error',message:'编辑器接口不可用，请手动粘贴并提交；未发出自动提交。'});
let baseline=[],baselineKnown=false,baselineOwner='';
if(ctx.platform==='Codeforces'){
const profile=[...document.querySelectorAll('#header a[href],.lang-chooser a[href]')].map(a=>{try{const url=new URL(a.getAttribute('href'),location.href);return url.origin===location.origin&&url.pathname.match(/^\/profile\/([A-Za-z0-9_.-]{1,64})$/)?.[1]}catch{return null}}).find(Boolean);
baselineOwner=profile||'';
}
try{let path=null;if(ctx.platform==='AtCoder')path=location.pathname.replace(/\/submit$/,'/submissions/me');if(ctx.platform==='Codeforces')path=location.pathname.replace(/\/submit$/,'/my');if(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(15000)});if(r.ok&&new URL(r.url).origin===location.origin&&new URL(r.url).pathname===path){const html=await r.text();const doc=new DOMParser().parseFromString(html.slice(0,2000000),'text/html');const challenge=/just a moment|checking your browser|人机验证|安全验证|验证码/i.test(doc.title+' '+(doc.body?.textContent||'').slice(0,1200));const table=doc.querySelector('table.status-frame-datatable')||[...doc.querySelectorAll('table')].some(t=>/submission|提出|提交|status|verdict|結果|时间|when/i.test([...t.querySelectorAll('th, tr:first-child td')].map(e=>e.textContent).join(' ')));if(!challenge&&table&&!doc.querySelector('input[type=password],iframe[src*=captcha],iframe[src*=challenge]')){baseline=receipts(doc).map(r=>r.id);baselineKnown=true;}}}}catch{}
// The official public API provides a bounded snapshot when the HTML list is
// unavailable. Only the authenticated page's own handle is used. A global ID
// lower bound prevents older records outside this snapshot from becoming AC.
if(ctx.platform==='Codeforces'&&!baselineKnown&&baselineOwner){
try{const r=await fetch('/api/user.status?handle='+encodeURIComponent(baselineOwner)+'&from=1&count=100',{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(15000)});if(r.ok){const value=await r.json();if(value.status==='OK'&&Array.isArray(value.result)&&value.result.every(row=>Number.isSafeInteger(row.id)&&row.id>0)){baseline=value.result.map(row=>String(row.id));baselineKnown=true;}}}catch{}
}
const form=editors().map(e=>e.closest('form')).find(Boolean)||[...document.querySelectorAll('form')].find(f=>f.querySelector('.CodeMirror,.ace_editor,.monaco-editor'));
let button=form?.querySelector('button[type=submit],input[type=submit],#submit');if(!button&&['牛客','洛谷'].includes(ctx.platform))button=[...document.querySelectorAll('button,[role=button],.submit-btn,.submit-button')].find(b=>visible(b)&&!b.disabled&&/^(?:保存并)?提交(?:代码|题目|评测)?$/.test(b.textContent.trim()));
if(!button)return send({status:'error',message:'未找到与代码编辑器对应的官方提交控件，请手动提交；未点击其它按钮。'});
if(ncReceipt){ncReceipt.armed=true;ncReceipt.pending=null;ncReceipt.receipt=null;}
send({status:'submitted',message:'已选择 '+compiler.label+(baselineKnown||ncReceipt?'，等待原站回执。':'；已发出官方提交，但暂未取得可核对的提交记录，请在原站查看结果。'),compiler:compiler.label,baseline,baselineKnown,baselineOwner,attempted:true});button.click();return {status:'submitted'};
}
if(action==='submit'){submit().catch(e=>send({status:'error',message:'表单操作未完成：'+String(e).slice(0,160)}));return {status:'loading'};}
const state=inspect();
if(ctx.platform==='Codeforces'&&ctx.attempted&&ctx.baselineKnown&&ctx.baselineOwner&&state.status!=='finished'){
  (async()=>{try{
    const response=await fetch('/api/user.status?handle='+encodeURIComponent(ctx.baselineOwner)+'&from=1&count=100',{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(15000)});
    if(!response.ok||new URL(response.url,location.href).origin!==location.origin)return;
    const value=await response.json(),original=new URL(ctx.originalUrl),match=taskPath(original.pathname).match(/^\/(?:contest|gym)\/(\d+)\/problem\/([A-Za-z]\d?)$/);
    if(value.status!=='OK'||!Array.isArray(value.result)||!match)return;
    const baseline=new Set(ctx.baseline||[]);
    const receipt=value.result.filter(row=>Number.isSafeInteger(row.id)&&newerReceipt(String(row.id),baseline)&&String(row.problem?.contestId)===match[1]&&row.problem?.index===match[2]&&row.author?.members?.some(member=>member.handle?.toLowerCase()===ctx.baselineOwner.toLowerCase())).sort((a,b)=>a.id-b.id)[0];
    if(!receipt)return;
    const verdict=normal(receipt.verdict)||'JUDGING';
    send({status:verdict==='JUDGING'?'judging':'finished',submissionId:String(receipt.id),...(verdict==='JUDGING'?{}:{verdict}),message:verdict==='JUDGING'?'原站已接收，正在评测。':'已读取原站本次新提交结果：'+verdict});
  }catch{}})();
}
return state;
})()'''.replace('COMPILER_SELECTION',languages,1).replace('NOWCODER_RECEIPTS',nowcoder,1).replace('ACTION',json.dumps(action),1).replace('CONTEXT',context,1)

class OfficialBridge:
    def __init__(self,main_window,guard=None,native_setup=None,on_receipt=None,on_pending=None,resume_loader=None):
        self.main_window=main_window;self.guard=guard;self.native_setup=native_setup;self.on_receipt=on_receipt;self.on_pending=on_pending;self.resume_loader=resume_loader;self.lock=threading.RLock();self.sessions={};self.current=None;self.panel=None;self.view=None;self.status_label=None
    def _ui(self,action):
        form=getattr(self.main_window,'native',None)
        if form is None or form.IsDisposed:
            from training import ServiceError
            raise ServiceError(503,'原生主窗口尚未就绪，请稍后重试')
        if not form.InvokeRequired:return action()
        from System import Action
        value=[];form.Invoke(Action(lambda:value.append(action())))
        return value[0] if value else None
    def _eval(self,script,timeout=5,identity=None):
        from System import Action,String
        from System.Threading.Tasks import Task
        event=threading.Event();result=[]
        def done(task):
            try:result.append(json.loads(str(task.Result)))
            except Exception:result.append(None)
            finally:event.set()
        def evaluate():
            # 会话被隐藏时 current 为 None，但 view 仍属于该会话（view_identity），允许继续复查。
            if self.view is None or identity is not None and self.view_identity != identity:
                event.set();return
            self.view.CoreWebView2.ExecuteScriptAsync(script).ContinueWith(Action[Task[String]](done))
        self._ui(evaluate)
        return result[0] if event.wait(timeout) and result else None
    def _update(self,identity,value):
        if not isinstance(value,dict):return
        # 原站已受理提交（judging 且带 submissionId/acceptedAt）：冻结受理时刻并
        # 持久化 pending，供返回 TB / 重启后恢复查询与回填 submitted_at。
        if value.get('acceptedAt') and value.get('submissionId') and self.on_pending:
            with self.lock:
                session=self.sessions.get(identity)
                if session:
                    session['acceptedAt']=value.get('acceptedAt');session['submissionId']=value.get('submissionId')
                    snapshot=dict(session)
                else:snapshot=None
            if snapshot:
                try:self.on_pending(identity,snapshot)
                except Exception:logging.exception('Official pending could not be saved')
        with self.lock:
            session=self.sessions.get(identity)
            if not session or session['status']=='closed':return
            if session['status']=='finished' and value.get('status')!='finished' and not value.get('attempted'):return
            for key in ('status','message','submissionId','verdict','attempted','baseline','baselineKnown','baselineOwner','compiler','acceptedAt'):
                if key in value:session[key]=value[key]
            if session['status'] not in STATUSES:session['status']='error'
            session['updatedAt']=dt.datetime.now(dt.timezone.utc).isoformat()
            message=str(session.get('message',''))[:240]
            receipt=dict(session) if session['status']=='finished' else None
        if receipt and self.on_receipt:
            try:saved=self.on_receipt(identity,receipt)
            except Exception:
                logging.exception('Official receipt could not be saved');saved=False
            # 落库成功才发布 finished。约定：回调显式返回 False 表示未保存（失败）；
            # 返回 None/其他（旧夹具）按已保存处理，保持兼容。
            if saved is False:
                with self.lock:
                    session=self.sessions.get(identity)
                    if session:
                        session['status']='judging';session['saveError']=True
                        session['message']='官方已返回结果，但本地保存失败，正在重试；暂不宣称通过。'
                message='官方已返回结果，但本地保存失败，正在重试；暂不宣称通过。'
        def display():
            if self.current==identity and self.status_label is not None and not self.status_label.IsDisposed:self.status_label.Text=message
        try:self._ui(display)
        except Exception:logging.debug('Official status label unavailable',exc_info=True)
    def _try_submit(self,identity):
        try:
            with self.lock:
                if self.current!=identity or self.sessions[identity]['status']=='closed':return
                session=dict(self.sessions[identity])
            if self.guard:self.guard(session['originalUrl'])
            self._eval(page_script(session,'submit'),identity=identity)
        except Exception as error:self._update(identity,{'status':'error','message':'提交已停止：'+str(error)[:180]})
    def _watch_receipts(self,identity):
        # 主前端在本面板打开时被隐藏，它的定时器会被挂起，所以回执轮询放在宿主侧。
        # 会话即使被“返回 TB”隐藏（status=hidden）也继续轮询，直到命中终态或真正释放。
        deadline=dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=15)
        while True:
            with self.lock:
                session=self.sessions.get(identity)
                if not session or session['status']=='closed':return
                snapshot=dict(session)
            if snapshot.get('attempted') and snapshot.get('status')!='finished':
                if dt.datetime.now(dt.timezone.utc)>deadline:
                    self._update(identity,{'status':'judging','message':'等待原站回执超时；请在原站确认结果或在面板重新提交。'});return
                # view 即使隐藏也保留（WebView2 隐藏时仍可执行脚本），对已绑定 ID 复查页内状态。
                if self.view is not None and getattr(self,'view_identity',None)==identity:
                    try:self._update(identity,self._eval(page_script(snapshot),identity=identity))
                    except Exception:logging.debug('Official receipt not ready',exc_info=True)
            with self.lock:
                session=self.sessions.get(identity)
                if session and session['status']=='finished':
                    self.release(identity);return
            threading.Event().wait(1.5)
    def _bind_accelerators(self,view,identity):
        from System import Action
        from System.Reflection import BindingFlags
        from System.Windows.Forms import Control,Keys
        # WinForms does not publicly expose its controller. The shipped WebView2
        # assembly owns this exact field; inspect its type before using it.
        field=view.GetType().GetField('_coreWebView2Controller',BindingFlags.Instance|BindingFlags.NonPublic)
        controller=field.GetValue(view) if field is not None else None
        if controller is None or str(controller.GetType().FullName)!='Microsoft.Web.WebView2.Core.CoreWebView2Controller':
            raise RuntimeError('当前 WebView2 组件不支持官方面板快捷键，请使用 Tab 到工具栏')
        def accelerator(_,event):
            if str(event.KeyEventKind) not in ('KeyDown','SystemKeyDown'):return
            if Control.ModifierKeys!=Keys.Alt or int(event.VirtualKey) not in (66,83):return
            event.Handled=True
            if event.PhysicalKeyStatus.WasKeyDown:return
            if int(event.VirtualKey)==66:
                self.main_window.native.BeginInvoke(Action(lambda:self.close(identity)))
            else:threading.Thread(target=self._try_submit,args=(identity,),daemon=True).start()
        controller.AcceleratorKeyPressed+=accelerator
    def _attach(self,identity):
        import System.Windows.Forms as Forms
        from System.Drawing import Color
        from Microsoft.Web.WebView2.WinForms import WebView2,CoreWebView2CreationProperties
        import webview
        form=self.main_window.native
        # 已有面板时先彻底释放（本函数只建新面板；复用同一会话走 _reopen）。
        if self.panel is not None:self._release_panel()
        session=self.sessions[identity]
        panel=Forms.TableLayoutPanel();panel.Dock=Forms.DockStyle.Fill
        panel.ColumnCount=1;panel.RowCount=2;panel.Margin=Forms.Padding(0);panel.Padding=Forms.Padding(0)
        panel.BackColor=Color.FromArgb(246,248,251)
        panel.ColumnStyles.Add(Forms.ColumnStyle(Forms.SizeType.Percent,100))
        panel.RowStyles.Add(Forms.RowStyle(Forms.SizeType.Absolute,54))
        panel.RowStyles.Add(Forms.RowStyle(Forms.SizeType.Percent,100))
        bar=Forms.TableLayoutPanel();bar.Dock=Forms.DockStyle.Fill;bar.ColumnCount=3;bar.RowCount=1
        bar.Margin=Forms.Padding(0);bar.Padding=Forms.Padding(8,7,8,7);bar.BackColor=panel.BackColor
        for width in (126,154):bar.ColumnStyles.Add(Forms.ColumnStyle(Forms.SizeType.Absolute,width))
        bar.ColumnStyles.Add(Forms.ColumnStyle(Forms.SizeType.Percent,100))
        submit=Forms.Button();submit.Text='提交到官方 (&S)';submit.Dock=Forms.DockStyle.Fill
        back=Forms.Button();back.Text='返回 TB (&B)';back.Dock=Forms.DockStyle.Fill
        for button in (back,submit):
            button.BackColor=Color.White;button.ForeColor=Color.FromArgb(34,48,65)
            button.FlatStyle=Forms.FlatStyle.Flat;button.FlatAppearance.BorderColor=Color.FromArgb(202,213,227)
            button.UseVisualStyleBackColor=False;button.Margin=Forms.Padding(0,0,8,0)
        submit.Click+=lambda *_:threading.Thread(target=self._try_submit,args=(identity,),daemon=True).start()
        back.Click+=lambda *_:self.close(identity)
        label=Forms.Label();label.Text=session['platform']+' · 在原站登录后提交'
        label.Dock=Forms.DockStyle.Fill;label.AutoEllipsis=True
        label.TextAlign=__import__('System.Drawing',fromlist=['ContentAlignment']).ContentAlignment.MiddleLeft
        label.ForeColor=Color.FromArgb(34,48,65);label.Margin=Forms.Padding(4,0,0,0)
        bar.Controls.Add(back,0,0);bar.Controls.Add(submit,1,0);bar.Controls.Add(label,2,0)
        view=WebView2();view.Dock=Forms.DockStyle.Fill;view.Margin=Forms.Padding(0)
        props=CoreWebView2CreationProperties();props.UserDataFolder=form.browser.user_data_folder
        props.set_IsInPrivateModeEnabled(webview._state['private_mode']);view.CreationProperties=props;view.DefaultBackgroundColor=Color.White
        # Separate layout rows reserve real space for the toolbar. A Fill-docked
        # browser behind a Top-docked overlay hides the website account header.
        panel.Controls.Add(bar,0,0);panel.Controls.Add(view,0,1);form.Controls.Add(panel)
        self.panel,self.view,self.current,self.status_label=panel,view,identity,label
        self.view_identity=identity
        threading.Thread(target=self._watch_receipts,args=(identity,),daemon=True).start()
        form.browser.webview.Visible=False;panel.BringToFront()
        def navigation(_,args):
            p=urlsplit(str(args.Uri))
            if p.scheme!='https' or p.hostname not in LOGIN_HOSTS[session['platform']]:args.Cancel=True;self._update(identity,{'status':'error','message':'已阻止离开原站的跳转；面板只支持该平台官方登录与提交。'})
        def message(_,args):
            try:
                if urlsplit(str(args.Source)).hostname not in LOGIN_HOSTS[session['platform']]:return
                value=json.loads(str(args.TryGetWebMessageAsString()))
                if value.get('tbOfficial') and value.get('sessionId')==identity:self._update(identity,value)
            except Exception:logging.exception('Official native status message failed')
        def loaded(_,args):
            if not args.IsSuccess:self._update(identity,{'status':'error','message':'原站页面未能加载，请检查网络或在当前面板重试。'});return
            def inspect():
                try:
                    self._update(identity,self._eval(page_script(dict(self.sessions[identity])),identity=identity))
                    if self.sessions[identity].pop('intent',False):self._try_submit(identity)
                except Exception:logging.exception('Official native page inspection failed')
            threading.Thread(target=inspect,daemon=True).start()
        def initialized(_,args):
            if not args.IsSuccess:self._update(identity,{'status':'error','message':'原生提交面板初始化失败，请检查 WebView2。'});return
            core=view.CoreWebView2;core.Settings.AreDevToolsEnabled=False;core.Settings.IsStatusBarEnabled=False;core.NavigationStarting+=navigation;core.WebMessageReceived+=message
            try:self._bind_accelerators(view,identity)
            except Exception:logging.exception('Official native keyboard binding unavailable')
            def popup(_,event):
                event.Handled=True
                if urlsplit(str(event.Uri)).hostname in LOGIN_HOSTS[session['platform']]:core.Navigate(str(event.Uri))
            core.NewWindowRequested+=popup
            if self.native_setup:self.native_setup(view)
            core.Navigate(session['url'])
        view.CoreWebView2InitializationCompleted+=initialized;view.NavigationCompleted+=loaded;view.EnsureCoreWebView2Async(form.browser.webview.CoreWebView2.Environment)
    def _open(self,url,code,title,intent):
        from training import ServiceError
        target=submission_target(url)
        if not isinstance(code,str) or not code.strip() or len(code.encode('utf-8'))>65536:raise ServiceError(400,'请先输入不超过 64 KiB 的待提交代码')
        if self.guard:self.guard(url)
        # 同题已有未终态会话（含已隐藏的）：直接重新显示，不新建、不丢 pending。
        from insights import canonical_url
        key=canonical_url(target.get('originalUrl'))
        with self.lock:
            for sid,session in self.sessions.items():
                if session['status'] in ('closed','finished'):continue
                if key and canonical_url(session.get('url'))==key:
                    self._ui(lambda:self._reopen(sid))
                    return self.status(sid,inspect=False)
        identity='official-'+uuid.uuid4().hex
        with self.lock:
            self.sessions[identity]={**target,'sessionId':identity,'code':code,'title':str(title),'status':'loading','message':'正在主窗口打开官方原生提交面板。','intent':intent,'attempted':False,'baseline':[],'baselineKnown':False,'baselineOwner':''}
            if len(self.sessions)>30:
                for old in list(self.sessions):
                    if self.sessions[old]['status']=='closed':self.sessions.pop(old)
                    if len(self.sessions)<=20:break
        self._ui(lambda:self._attach(identity));return self.status(identity,inspect=False)
    def open(self,url,code,title):return self._open(url,code,title,False)
    def submit(self,url,code,title):return self._open(url,code,title,True)
    def status(self,identity,inspect=True):
        from training import ServiceError
        with self.lock:
            if identity not in self.sessions:raise ServiceError(404,'没有找到本次原站提交会话')
            session=dict(self.sessions[identity])
        if inspect and identity==self.current and self.view is not None and session['status'] not in ('hidden','loading','closed','error','finished'):
            try:self._update(identity,self._eval(page_script(session),identity=identity))
            except Exception:pass
        with self.lock:return {k:v for k,v in self.sessions[identity].items() if k not in ('code','problem','originalUrl','title','intent','attempted','baseline','baselineKnown','baselineOwner')}
    def _hide_current(self,identity=None):
        # 返回 TB 只隐藏面板、保留 webview 与 pending，后台 watcher 继续等终态；
        # 不解绑代码、不置 closed，用户可再次打开同一会话。
        if self.panel is not None:self.panel.Visible=False
        if self.current:
            self.sessions[self.current].update(status='hidden')
            self._hidden_sessions=self._hidden_sessions if hasattr(self,'_hidden_sessions') else []
            if self.current not in self._hidden_sessions:self._hidden_sessions.append(self.current)
            self.current=None
        main=self.main_window.native.browser.webview;main.Visible=True;main.BringToFront();main.Focus()
    def _reopen(self,identity):
        session=self.sessions.get(identity)
        if session is None:return
        if self.panel is not None:
            self.panel.Visible=True;self.panel.BringToFront()
            self.main_window.native.browser.webview.Visible=False
            self.current=identity;session['status']=session.get('status') if session.get('status') not in (None,'hidden') else ('submitted' if session.get('attempted') else 'loading')
            if self._hidden_sessions and identity in self._hidden_sessions:self._hidden_sessions.remove(identity)
    def close(self,identity=None):
        from training import ServiceError
        if identity is not None and identity not in self.sessions:raise ServiceError(404,'没有找到本次原站提交会话')
        if self.current and (identity is None or identity==self.current):self._ui(lambda:self._hide_current(identity))
        return {'status':'hidden','message':'已返回 TB；仍在等待原站回执。'} if identity is None else self.status(identity,inspect=False)
    def release(self,identity):
        """真正结束一个会话并释放它的 webview（命中终态或用户显式丢弃时）。"""
        with self.lock:
            session=self.sessions.get(identity)
            if self.current==identity:
                self._ui(self._release_panel)
            if session:session.update(status='closed',code='')
    def _release_panel(self):
        if self.panel is not None:
            try:self.panel.Dispose()
            except Exception:pass
            self.panel=self.view=self.status_label=None
    def on_closing(self):
        # pywebview hashes event return values; API response dictionaries cannot
        # be returned from a native window lifecycle callback.
        self.close()
