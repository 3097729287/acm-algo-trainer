function tbOfficialPage(ctx, action, postMessage) {
if(typeof window!=='undefined'&&(window!==window.top||!['codeforces.com','www.codeforces.com','atcoder.jp','ac.nowcoder.com','www.luogu.com.cn','luogu.com.cn','qoj.ac'].includes(location.hostname)))return null;
QOJ_ADAPTER
if(ctx.platform==='QOJ')return tbQojPage(ctx,action,postMessage);
COMPILER_SELECTION
NOWCODER_RECEIPTS
LUOGU_RECEIPTS
const send=value=>{postMessage({tbOfficial:true,sessionId:ctx.sessionId,...value});return value;};
const ncReceipt=installNowcoderReceipts(ctx, send);
const lgReceipt=installLuoguReceipts(ctx, send);
const visible=e=>e&&e.getClientRects().length>0;
const editors=()=>[...document.querySelectorAll('textarea')].filter(e=>/source|code|editor/i.test((e.name||'')+' '+(e.id||'')));
const hasEditor=()=>editors().length||document.querySelector('.CodeMirror,.cm-editor,.ace_editor,.monaco-editor');
// CodeMirror 6 now attaches cmTile; older versions expose cmView. Change the
// actual view document so the site's native submit handler sees the same code.
const codeMirrorView=e=>e.cmView?.view||e.cmTile?.root?.view;
const hasReadyEditor=()=>editors().some(visible)||[...document.querySelectorAll('.CodeMirror,.ace_editor,.monaco-editor')].some(visible)||[...document.querySelectorAll('.cm-editor .cm-content')].some(e=>{const view=codeMirrorView(e);return visible(e)&&view?.state?.doc&&typeof view.dispatch==='function';});
const login=()=>[...document.querySelectorAll('input[type=password]')].some(visible)||/\/login|\/enter(?:\/|$)|\/auth\/login/i.test(location.pathname);
const pageKey=ctx.sessionId+':'+ctx.originalUrl;
const host=typeof window==='undefined'?globalThis:window;
if(host.__tbSubmissionWork?.key!==pageKey)host.__tbSubmissionWork?.observer?.disconnect();
const work=host.__tbSubmissionWork?.key===pageKey?host.__tbSubmissionWork:(host.__tbSubmissionWork={key:pageKey,preparing:null,snapshot:null,polling:false,nextPoll:0});
if(work.retry!==(ctx.retry||0)){
work.retry=ctx.retry||0;
if(ctx.platform==='AtCoder'&&ctx.nativeFormOnly&&!ctx.attempted)work.attempted=false;
// Clear a rejected request only on the user's next explicit Submit click.
// Inspection, opening verification, and receiving a token never resubmit.
for(const receipt of [ncReceipt,lgReceipt])if(!ctx.attempted&&!receipt?.pending&&['needs_verification','needs_login','error'].includes(receipt?.receipt?.status))receipt.receipt=null;
}
if(ctx.platform==='AtCoder'&&ctx.nativeFormOnly&&(ctx.attempted||work.attempted))ctx.attempted=work.attempted=true;
function acSubmitForm(){return editors().map(e=>e.form||e.closest('form')).find(form=>visible(form))||[...document.querySelectorAll('form[action$="/submit"]')].find(visible);}
function acLanguageSelect(form){return form&&[...form.elements].find(e=>e.tagName==='SELECT'&&visible(e.parentElement)&&/language|lang/i.test((e.name||'')+' '+(e.id||'')));}
function acEditorReady(form){
if(!form)return false;
return editors().some(e=>e.form===form&&visible(e))
||[...form.querySelectorAll('.CodeMirror')].some(e=>visible(e)&&typeof e.CodeMirror?.setValue==='function')
||[...form.querySelectorAll('.ace_editor')].some(e=>visible(e)&&typeof window.ace?.edit==='function')
||[...form.querySelectorAll('.monaco-editor')].some(e=>visible(e)&&window.monaco?.editor?.getModels?.().some(model=>!model.isDisposed()))
||[...form.querySelectorAll('.cm-editor .cm-content')].some(e=>visible(e)&&codeMirrorView(e)?.state?.doc&&typeof codeMirrorView(e)?.dispatch==='function');
}
function acFormPending(){
if(ctx.platform!=='AtCoder'||ctx.attempted)return false;
const form=acSubmitForm(),language=acLanguageSelect(form);
return !form||!acEditorReady(form)||!language||language.disabled||![...language.options].some(option=>!option.disabled&&option.value&&option.value!=='0')||!form.querySelector('[name="csrf_token"]')?.value.trim();
}
function acVerificationState(){
if(ctx.platform!=='AtCoder')return null;
const form=acSubmitForm(),widget=form?.querySelector('.cf-challenge,.cf-turnstile'),token=form?.querySelector('[name="cf-turnstile-response"]');
if(!widget&&!token||token?.value.trim()){delete work.verifyingAt;return null;}
if(ctx.attempted)return {status:'unconfirmed',message:'原站要求提交验证，尚未确认本次代码受理；请在浏览器核对记录。'};
work.verifyingAt??=Date.now();
return Date.now()-work.verifyingAt<30000?{status:'loading',attempted:false,message:'正在等待 AtCoder 完成提交验证，尚未发送代码。'}:{status:'needs_verification',attempted:false,message:ctx.resumeAfterLogin?'请在弹出的浏览器完成 AtCoder 验证，完成后会继续本次提交。':'请在浏览器完成 AtCoder 验证，核对后再提交。'};
}
function luoguLoggedOut(){
if(ctx.platform!=='洛谷')return false;
try{const data=JSON.parse(document.querySelector('#lentille-context')?.textContent||'null');if(data&&Object.prototype.hasOwnProperty.call(data,'user'))return data.user===null;}catch{}
const legacy=window._feInjection;if(legacy&&Object.prototype.hasOwnProperty.call(legacy,'currentUser'))return !legacy.currentUser;
return false;
}
const verification=()=>[...document.querySelectorAll('iframe')].some(e=>visible(e)&&/captcha|challenge/i.test(e.src)&&!(ctx.platform==='AtCoder'&&e.closest('.cf-challenge,.cf-turnstile')?.closest('form')===acSubmitForm()))
||/just a moment|checking your browser|人机验证|安全验证/i.test(document.title)
||!hasEditor()&&!lgReceipt?.hasSubmitApi()&&/just a moment|checking your browser|人机验证|安全验证|验证码/i.test((document.body?.innerText||'').slice(0,1200));
function normal(text){
text=(text||'').trim().replace(/_/g,' ').replace(/\s+/g,' ');
const map={'AC':'AC','OK':'AC','ACCEPTED':'AC','通过':'AC','WA':'WA','WRONG ANSWER':'WA','答案错误':'WA','TLE':'TLE','TIME LIMIT EXCEEDED':'TLE','超时':'TLE','MLE':'MLE','MEMORY LIMIT EXCEEDED':'MLE','内存超限':'MLE','RE':'RE','RUNTIME ERROR':'RE','运行错误':'RE','CE':'CE','COMPILATION ERROR':'CE','COMPILE ERROR':'CE','编译错误':'CE','OLE':'OLE','OUTPUT LIMIT EXCEEDED':'OLE'};
const exact=map[text.toUpperCase()];if(exact)return exact;
for(const [label,value] of Object.entries(map))if(label.length>3&&new RegExp('^'+label+'(?:\\s+(?:on|in|at)\\b|$)','i').test(text))return value;
return /^(WJ|WR|TESTING|Judging|Running|Waiting|Pending|Queuing|评测中|等待评测)(\b|$)/i.test(text)?'JUDGING':null;
}
function taskPath(path){return path.replace(/^\/problemset\/problem\/(\d+)\/([A-Za-z]\d?)$/,'/contest/$1/problem/$2');}
function receipts(doc=document){const rows=[];doc.querySelectorAll('tr').forEach(row=>{const links=[...row.querySelectorAll('a[href]')];const a=links.find(a=>/\/submission(?:s)?\/\d+/.test(a.getAttribute('href')||''));if(!a)return;const id=(a.getAttribute('href')||'').match(/\/submission(?:s)?\/(\d+)/)?.[1];const task=links.some(a=>{try{const target=new URL(a.getAttribute('href'),location.href),original=new URL(ctx.originalUrl);return target.origin===location.origin&&taskPath(target.pathname)===taskPath(original.pathname)}catch{return false}});const owner=!ctx.baselineOwner||links.some(a=>{try{const link=new URL(a.getAttribute('href'),location.href);return link.origin===location.origin&&link.pathname===(ctx.platform==='AtCoder'?'/users/':'/profile/')+ctx.baselineOwner}catch{return false}});const verdict=[...row.querySelectorAll('.label,.submissionVerdictWrapper,.verdict,[data-verdict],.verdict-accepted,.verdict-rejected,.status-cell')].map(e=>normal(e.getAttribute('data-verdict')||e.getAttribute('verdict')||e.textContent)).find(Boolean);if(id&&task&&owner)rows.push({id,verdict});});return rows;}
function newerReceipt(id,baseline){
if(!/^\d+$/.test(id))return false;
const previous=[...baseline].filter(value=>/^\d+$/.test(value));
return !baseline.has(id)&&previous.every(value=>BigInt(id)>BigInt(value));
}
function cfOwner(doc=document){
return [...doc.querySelectorAll('#header a[href],header a[href],.lang-chooser a[href]')].map(a=>{try{const url=new URL(a.getAttribute('href'),location.href);return url.origin===location.origin&&url.pathname.match(/^\/profile\/([A-Za-z0-9_.-]{1,64})\/?$/)?.[1]}catch{return null}}).find(Boolean)||'';
}
function acOwner(doc=document){
return [...doc.querySelectorAll('.navbar a[href],#navbar-collapse a[href],header a[href]')].map(a=>{try{const url=new URL(a.getAttribute('href'),location.href);return url.origin===location.origin&&url.pathname.match(/^\/users\/([A-Za-z0-9_]{1,64})\/?$/)?.[1]}catch{return null}}).find(Boolean)||'';
}
function cfLoggedOut(){
return ctx.platform==='Codeforces'&&!cfOwner()&&[...document.querySelectorAll('#header a[href],header a[href],.lang-chooser a[href]')].some(a=>{try{return new URL(a.getAttribute('href'),location.href).pathname==='/enter'}catch{return false}});
}
function myPaths(){
const original=new URL(ctx.originalUrl),match=taskPath(original.pathname).match(/^\/(contest|gym)\/(\d+)\/problem\//);
return match?[`/${match[1]}/${match[2]}/my`,...(match[1]==='contest'?['/problemset/my']:[])]:[];
}
async function myPage(path){
const response=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(5000)});
const final=new URL(response.url||path,location.href);
if(!response.ok||final.origin!==location.origin||!myPaths().includes(final.pathname))return null;
const doc=new DOMParser().parseFromString((await response.text()).slice(0,2000000),'text/html');
if(/just a moment|checking your browser|人机验证|安全验证|验证码/i.test(doc.title+' '+(doc.body?.textContent||'').slice(0,1200))||doc.querySelector('input[type=password],iframe[src*=captcha],iframe[src*=challenge]'))return null;
const table=doc.querySelector('table.status-frame-datatable')||[...doc.querySelectorAll('table')].find(t=>/submission|提交|status|verdict|结果|when/i.test([...t.querySelectorAll('th,tr:first-child td')].map(e=>e.textContent).join(' ')));
return table?doc:null;
}
async function acMyPage(){
const path=new URL(ctx.originalUrl).pathname.replace(/\/tasks\/[^/]+$/,'/submissions/me');
const r=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(5000)});
const final=new URL(r.url||path,location.href);
if(!r.ok||final.origin!==location.origin||final.pathname!==path)return null;
const doc=new DOMParser().parseFromString((await r.text()).slice(0,2000000),'text/html');
if(/just a moment|checking your browser|人机验证|安全验证|验证码/i.test(doc.title+' '+(doc.body?.textContent||'').slice(0,1200))||doc.querySelector('input[type=password],iframe[src*=captcha],iframe[src*=challenge]'))return null;
const owner=acOwner(doc),expected=ctx.baselineOwner||acOwner();
if(expected&&owner!==expected)return null;
const table=[...doc.querySelectorAll('table')].some(t=>/submission|提出|提交|status|verdict|結果|时间|when/i.test([...t.querySelectorAll('th, tr:first-child td')].map(e=>e.textContent).join(' ')));
// AtCoder omits the table for a user's first submission in a contest.
// Require the authenticated personal page and its explicit empty state.
const empty=owner&&/My Submissions|自分の提出/i.test(doc.title)&&[...doc.querySelectorAll('.panel-body,p,.alert,h3,h4')].some(e=>/^(?:No Submissions|提出はありません|提出がありません|提出が存在しません)[.!。]?$/.test(e.textContent.trim()));
return table||empty?doc:null;
}
function prepare(){
if(work.preparing)return work.preparing;
work.preparing=(async()=>{
if(ctx.platform==='AtCoder'){
const doc=await acMyPage();if(!doc)return null;
return {baseline:[...doc.querySelectorAll('a[href]')].map(a=>(a.getAttribute('href')||'').match(/\/submissions\/(\d+)/)?.[1]).filter(Boolean),baselineKnown:true,baselineOwner:acOwner(doc)||acOwner()};
}
if(ctx.platform==='Codeforces'){
const owner=cfOwner();
// The fastest valid personal list wins. A slow/blocked endpoint never holds
// the other list or the official owner-scoped API behind serial timeouts.
const candidates=myPaths().map(async path=>{const doc=await myPage(path);if(!doc)throw new Error('No personal list');return {baseline:[...doc.querySelectorAll('a[href]')].map(a=>(a.getAttribute('href')||'').match(/\/submission\/(\d+)/)?.[1]).filter(Boolean),baselineKnown:true,baselineOwner:owner||cfOwner(doc)};});
if(owner)candidates.push((async()=>{const r=await fetch('/api/user.status?handle='+encodeURIComponent(owner)+'&from=1&count=100',{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(5000)});if(!r.ok||new URL(r.url||'/api/user.status',location.href).origin!==location.origin)throw new Error('No owner snapshot');const value=await r.json();if(value.status!=='OK'||!Array.isArray(value.result)||!value.result.every(row=>Number.isSafeInteger(row.id)&&row.id>0&&row.author?.members?.some(member=>member.handle?.toLowerCase()===owner.toLowerCase())))throw new Error('Invalid owner snapshot');return {baseline:value.result.map(row=>String(row.id)),baselineKnown:true,baselineOwner:owner};})());
return await Promise.any(candidates);
}
return {baseline:[],baselineKnown:false,baselineOwner:''};
})().catch(()=>null).then(value=>{work.snapshot=value;if(!value)work.preparing=null;return value;});
return work.preparing;
}
function receiptValue(receipt){return {status:receipt.verdict==='JUDGING'?'judging':'finished',submissionId:receipt.id,...(receipt.verdict==='JUDGING'?{}:{verdict:receipt.verdict}),message:receipt.verdict==='JUDGING'?'原站已接收，正在评测。':'本次提交结果：'+receipt.verdict};}
function observeAtCoderForm(){
if(ctx.platform!=='AtCoder'||!ctx.nativeFormOnly||ctx.attempted)return;
const form=acSubmitForm();if(!form)return;
prepare();
if(work.nativeForm===form)return;
work.nativeForm=form;
form.addEventListener('submit',event=>{
  // A native site handler can reject the form before a request is sent.
  if(event.defaultPrevented||work.attempted||ctx.attempted)return;
  const snapshot=work.snapshot;
  work.attempted=ctx.attempted=true;
  const submittedCode=[...form.elements].find(e=>e.tagName==='TEXTAREA'&&/source|code|editor/i.test((e.name||'')+' '+(e.id||'')))?.value;
  if(!snapshot?.baselineKnown||submittedCode!==ctx.code){ctx.baselineKnown=false;send({status:'unconfirmed',attempted:true,baselineKnown:false,message:'尚未收到原站受理编号，正在后台查询。'});return;}
  Object.assign(ctx,snapshot);
  send({status:'submitted',attempted:true,...snapshot,message:'已在官网提交，正在读取原站结果。'});
});
}
function inspect(){
lgReceipt?.inspectRejection?.();
if(login()||cfLoggedOut()||luoguLoggedOut()||lgReceipt?.loggedOut()||ncReceipt?.loggedOut?.()||(ctx.platform==='牛客'&&window.globalInfo?.ownerId!=null&&Number(window.globalInfo.ownerId)<=0))return {status:'needs_login',...(!ctx.attempted?{attempted:false}:{}),message:ctx.resumeAfterLogin?'请在弹出的浏览器登录原站，登录后会自动填码并继续本次提交。':'请在浏览器登录原站，然后核对本次提交状态。'};
if(verification())return {status:'needs_verification',...(!ctx.attempted?{attempted:false}:{}),message:ctx.resumeAfterLogin?'请在弹出的浏览器完成原站验证，完成后会继续本次提交。':'请在浏览器完成原站验证，然后回到 TB 查看状态。'};
observeAtCoderForm();
// Some native logins return to the site home page instead of the submit URL.
// Only a positive account marker may resume this unsent submission there.
if(ctx.resumeAfterLogin&&!ctx.attempted&&!hasEditor()){
let luoguOwner=null;try{luoguOwner=JSON.parse(document.querySelector('#lentille-context')?.textContent||'null')?.user?.uid;}catch{}
const loggedIn=ctx.platform==='AtCoder'?!!acOwner():ctx.platform==='Codeforces'?!!cfOwner():ctx.platform==='牛客'?Number(window.globalInfo?.ownerId)>0:ctx.platform==='洛谷'&&Number(luoguOwner||window._feInjection?.currentUser?.uid)>0;
if(loggedIn)return {status:'loading',loggedIn:true,message:'登录成功，正在返回本题提交页。'};
}
if(ncReceipt?.isGlobalTarget()&&!ncReceipt.pageMatches())return {status:window.pageInfo?'error':'loading',attempted:false,message:'未能准确选定本题，已停止；请在原站确认题目。'};
if(ctx.platform==='AtCoder'&&new URL(ctx.originalUrl).pathname.replace(/\/tasks\/[^/]+$/,'/submit')===location.pathname){
const errors=[...document.querySelectorAll('.alert-danger,.has-error .help-block,.error-message')].filter(visible).map(e=>e.textContent.trim()).filter(Boolean);
if(errors.length)return {status:'error',attempted:false,message:'AtCoder 未受理代码：'+errors.join('；').slice(0,200)};
}
const acVerification=acVerificationState();if(acVerification)return acVerification;
if(acFormPending())return {status:'loading',attempted:false,message:'正在加载原站提交表单。'};
if(ncReceipt?.receipt)return ncReceipt.receipt;
if(lgReceipt?.receipt)return lgReceipt.receipt;
if(lgReceipt&&!ctx.attempted)lgReceipt.prepare();
if(ctx.attempted&&!ctx.submissionId){
const errors=[...document.querySelectorAll('.el-message--error,.el-notification.error,.ivu-message-error,.ant-message-error')].filter(visible).map(e=>e.textContent.trim()).filter(Boolean);
if(errors.length)return {status:'error',attempted:false,message:'原站未受理代码：'+errors.join('；').slice(0,200)};
}
if(ctx.platform==='Codeforces'&&ctx.attempted&&/\/submit$/.test(location.pathname)){
const errors=[...document.querySelectorAll('span.error,.error-message,.submit-error')].filter(visible).map(e=>e.textContent.trim()).filter(Boolean);
if(errors.length)return {status:'error',attempted:false,message:'Codeforces 未受理代码：'+errors.join('；').slice(0,200)};
}
if(ctx.attempted&&ctx.baselineKnown){const baseline=new Set(ctx.baseline||[]);const receipt=receipts().find(r=>newerReceipt(r.id,baseline)&&(!ctx.submissionId||r.id===ctx.submissionId));if(receipt?.verdict)return receiptValue(receipt);}
if(!ctx.attempted&&document.readyState==='loading')return {status:'loading',message:'正在加载原站提交表单。'};
if(!ctx.attempted&&hasEditor()&&['Codeforces','AtCoder'].includes(ctx.platform))prepare();
return (ctx.platform==='洛谷'?(ctx.nativeFormOnly?hasReadyEditor():lgReceipt?.hasSubmitApi()):hasEditor())?{status:ctx.attempted?'submitted':'ready',message:ctx.attempted?'已发送原站提交请求，正在等待受理编号。':'后台连接已就绪。'}:{status:ctx.attempted?'submitted':'loading',message:ctx.attempted?'尚未收到原站受理编号，正在后台查询。':ctx.platform==='洛谷'&&ctx.nativeFormOnly?'正在等待洛谷代码编辑器加载，尚未发送代码。':'正在准备原站提交接口。'};
}
async function submit(manual=false){
if(ctx.attempted)return send(inspect());
if(manual&&work.manualFilled)return send({status:'awaiting_submit',message:'代码已填入浏览器，请在官网点击提交。结果会自动同步到 TB。'});
const state=inspect();if(state.status==='needs_login'||!manual&&(['needs_verification'].includes(state.status)||ctx.platform==='AtCoder'&&['loading','error'].includes(state.status)))return send(state);
if(!manual&&ctx.nativeFormOnly&&ctx.platform==='洛谷'&&state.status==='loading')return send(state);
const checkpoint=value=>postMessage({tbOfficial:true,sessionId:ctx.sessionId,...value});
if(!manual&&!ctx.nativeFormOnly&&lgReceipt?.hasSubmitApi())return lgReceipt.submitApi(checkpoint);
if(!hasEditor())return send({status:manual?'awaiting_submit':'error',attempted:false,message:manual?'请在浏览器完成验证并打开提交编辑器，TB 会继续尝试填入代码。':'没有找到原站代码编辑器，请进入本题提交页；不会点击其它表单。'});
let task=!ctx.problem,filled=0;
document.querySelectorAll('select').forEach(s=>{const field=(s.name||s.id||'').toLowerCase();if(/problem|task/.test(field)&&ctx.problem){const o=[...s.options].find(o=>o.value===ctx.problem);if(o){if(s.value!==o.value){s.value=o.value;s.dispatchEvent(new Event('change',{bubbles:true}));}task=true;}}});
if(['牛客','洛谷'].includes(ctx.platform))task=location.pathname===new URL(ctx.originalUrl).pathname;
if(ncReceipt?.isGlobalTarget())task=ncReceipt.pageMatches();
if(!task)return send({status:'error',attempted:false,message:'未能准确选定本题，已停止；请在原站确认题目。'});
const compilerForm=ctx.platform==='AtCoder'?acSubmitForm():document;
if(ctx.platform==='AtCoder'&&(!compilerForm||acFormPending()))return send({status:'loading',attempted:false,message:'正在加载原站提交表单。'});
const compiler=await selectOfficialCompiler(ctx.code,ctx.platform,ctx.language || 'cpp17',compilerForm);
if(!compiler)return send({status:'error',attempted:false,message:ctx.language==='python3'?'没有找到 Python 3 / PyPy 3，请在原站确认语言后重试。':'没有找到支持当前代码的 C++17 / C++20 / C++23 编译器，请在原站确认语言后重试。'});
if(!manual&&!ctx.nativeFormOnly&&ctx.language!=='python3'&&ncReceipt?.hasLegacyApi())return ncReceipt.submitLegacy(compiler,checkpoint);
editors().forEach(e=>{Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,ctx.code);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));filled++;});
document.querySelectorAll('.CodeMirror').forEach(e=>{if(e.CodeMirror){e.CodeMirror.setValue(ctx.code);filled++;}});document.querySelectorAll('.ace_editor').forEach(e=>{try{if(window.ace){window.ace.edit(e).setValue(ctx.code,-1);filled++;}}catch{}});try{window.monaco?.editor?.getModels?.().filter(m=>!m.isDisposed()&&/cpp|c\+\+/.test(m.getLanguageId?.()||'')).forEach(m=>{m.setValue(ctx.code);filled++;});}catch{}
document.querySelectorAll('.cm-editor .cm-content').forEach(e=>{const view=codeMirrorView(e);if(view?.state?.doc&&typeof view.dispatch==='function'){view.dispatch({changes:{from:0,to:view.state.doc.length,insert:ctx.code}});filled++;}});
if(!filled)return send({status:'error',attempted:false,message:'编辑器接口不可用，请手动粘贴并提交；未发出自动提交。'});
if(manual){
work.manualFilled=true;
const snapshot=await prepare();
if(snapshot)Object.assign(ctx,snapshot);
// Keep the user's native form, CSRF and verification behavior. Never click it.
const form=ctx.platform==='AtCoder'?acSubmitForm():editors().map(e=>e.closest('form')).find(Boolean);
form?.addEventListener('submit',()=>{ctx.attempted=true;const submittedCode=editors().map(e=>e.value).find(v=>v.trim())||'';postMessage({tbOfficial:true,sessionId:ctx.sessionId,status:'submitted',attempted:true,submittedCode,...(snapshot||{}),message:'已在官网提交，正在读取原站结果。'});},{once:true});
if(ncReceipt)ncReceipt.armed=true;if(lgReceipt)lgReceipt.armed=true;
return send({status:'awaiting_submit',...(snapshot||{}),message:'代码已填入浏览器，请在官网点击提交。结果会自动同步到 TB。'});
}
const snapshot=await prepare(),{baseline=[],baselineKnown=false,baselineOwner=''}=snapshot||{};
if(['Codeforces','AtCoder'].includes(ctx.platform)&&!baselineKnown)return send({status:'error',attempted:false,message:'暂时无法读取本账号的提交记录，尚未发送代码，请稍后重试。'});
// The site may refresh/expire its token while language/editor/list preparation
// is in flight. Recheck this form immediately before the dispatch checkpoint.
const verificationAfterPreparation=acVerificationState();if(verificationAfterPreparation)return send(verificationAfterPreparation);
const submitForm=f=>f&&[...f.elements].some(e=>e.tagName==='SELECT'&&/language|programType/i.test((e.name||'')+' '+(e.id||'')))&&(f.querySelector('.CodeMirror,.cm-editor,.ace_editor,.monaco-editor')||editors().some(e=>e.form===f));
const form=ctx.platform==='AtCoder'?acSubmitForm():editors().map(e=>e.form||e.closest('form')).find(submitForm)||[...document.forms].find(submitForm);
if(ctx.platform==='AtCoder'){
const language=acLanguageSelect(form);
if(form!==compilerForm||acFormPending()||!compilerCandidate(language?.selectedOptions[0]?.textContent,ctx.code,ctx.platform,ctx.language||'cpp17'))return send({status:'loading',attempted:false,message:'正在加载原站提交表单。'});
}
if(ctx.platform==='AtCoder'&&form&&!form.checkValidity())return send({status:'error',attempted:false,message:'AtCoder 提交表单未通过校验，尚未发送代码；请检查原站题目和语言选择。'});
// Use DOM form ownership, including external controls and default-type buttons.
// CF also uses an input[type=button].submit with its own native click handler.
const controls=()=>[...(form?.elements||[])].filter(b=>b.isConnected&&b.form===form&&(['BUTTON','INPUT'].includes(b.tagName)&&b.type==='submit'||ctx.platform==='Codeforces'&&b.type==='button'&&b.matches('.submit,#submit')&&/^(submit|提交)$/i.test(b.value||b.textContent.trim())));
const enabledButton=()=>controls().find(b=>visible(b)&&!b.disabled);
let button=enabledButton();
// CF keeps #singlePageSubmitButton disabled until its asynchronous problemLock
// POST grants permission. Existing source/language changes can restart that
// request. Wait for the real page; never force-enable or replace its handler.
if(!button&&controls().length&&ctx.platform==='Codeforces'){
  const deadline=Date.now()+30000;
  while(!button&&Date.now()<deadline){
    if(login()||cfLoggedOut())return send({status:'needs_login',attempted:false,message:'原站登录已失效，请登录后重试。'});
    if(verification())return send({status:'needs_verification',attempted:false,message:'原站要求验证，请完成后再提交。'});
    await new Promise(resolve=>setTimeout(resolve,100));
    button=enabledButton();
  }
}
if(!button&&['牛客','洛谷'].includes(ctx.platform))button=[...document.querySelectorAll('button,[role=button],.btn-submit,.submit-btn,.submit-button')].find(b=>visible(b)&&!b.disabled&&b.getAttribute('aria-disabled')!=='true'&&/^(?:保存并)?提交(?:代码|题目|评测)?$/.test(b.textContent.trim()));
if(!button)return send({status:'error',attempted:false,message:'原站提交控件尚未就绪，未发送代码。请稍后重试或查看原站页面。'});
if(ncReceipt){ncReceipt.armed=true;ncReceipt.pending=null;ncReceipt.receipt=null;}
if(lgReceipt){lgReceipt.armed=true;lgReceipt.pending=null;lgReceipt.receipt=null;}
// Persist the pre-submit snapshot before a native form can navigate away.
// Browser transport acknowledges this checkpoint; WebView transport is immediate.
ctx.attempted=true;if(ctx.platform==='AtCoder'&&ctx.nativeFormOnly)work.attempted=true;
await postMessage({tbOfficial:true,sessionId:ctx.sessionId,status:'submitted',message:'已选择 '+compiler.label+'，正在操作原站表单，尚未确认受理。',compiler:compiler.label,baseline,baselineKnown,baselineOwner,attempted:true});button.click();return {status:'submitted'};
}
// Native verdict cells update independently of our fallback inspection timer.
// Observe only document changes and retain the newest validated context.
work.readReceipt=()=>{
  if(!ctx.attempted||!ctx.baselineKnown||!['Codeforces','AtCoder'].includes(ctx.platform))return;
  const state=inspect();
  if(!state.submissionId||!['judging','finished'].includes(state.status))return;
  const key=state.submissionId+':'+state.status+':'+(state.verdict||'');
  if(work.lastReceipt===key)return;
  work.lastReceipt=key;send(state);
};
if(typeof MutationObserver!=='undefined'&&!work.observer&&document.documentElement){
  work.observer=new MutationObserver(()=>work.readReceipt?.());
  work.observer.observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class','data-verdict']});
}
if(action==='observe')return null;
if(action==='prepare'){if(!work.filling){work.filling=true;submit(true).catch(e=>send({status:'awaiting_submit',message:'请在官网检查代码并提交；'+String(e).slice(0,120)})).finally(()=>{work.filling=false});}return null;}
if(action==='submit'){if(!work.submitting){work.submitting=true;submit().catch(e=>send({status:ctx.attempted?'unconfirmed':'error',attempted:!!ctx.attempted,message:ctx.attempted?'原站响应中断，正在核对记录，请勿重复提交。':'表单操作未完成，尚未发送代码：'+String(e).slice(0,160)})).finally(()=>{work.submitting=false;});}return {status:'loading'};}
const state=inspect();
if(ctx.attempted&&ncReceipt)ncReceipt.poll();
if(ctx.attempted&&lgReceipt)lgReceipt.poll();
if(ctx.platform==='AtCoder'&&ctx.attempted&&ctx.baselineKnown&&state.status!=='finished'&&!work.polling&&Date.now()>=work.nextPoll){
  work.polling=true;
  (async()=>{try{
    const doc=await acMyPage();if(!doc)return;
    const receipt=receipts(doc).find(r=>newerReceipt(r.id,new Set(ctx.baseline||[]))&&(!ctx.submissionId||r.id===ctx.submissionId));
    if(receipt?.verdict)send(receiptValue(receipt));
  }catch{}finally{work.polling=false;work.nextPoll=Date.now()+1000;}})();
}
if(ctx.platform==='Codeforces'&&ctx.attempted&&ctx.baselineKnown&&state.status!=='finished'&&!work.polling&&Date.now()>=work.nextPoll){
  work.polling=true;
  const owner=ctx.baselineOwner||cfOwner();
  (async()=>{try{
    // A hidden CF page may stop updating its live verdict cells. Read a fresh
    // authenticated list as well as the public API instead of waiting for DOM.
    for(const path of myPaths()){
      try{const doc=await myPage(path);if(!doc)continue;const candidate=receipts(doc).find(row=>newerReceipt(row.id,new Set(ctx.baseline||[]))&&(!ctx.submissionId||row.id===ctx.submissionId));if(candidate?.verdict){send(receiptValue(candidate));return;}}catch{}
    }
    if(!owner)return;
    const response=await fetch('/api/user.status?handle='+encodeURIComponent(owner)+'&from=1&count=100',{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(5000)});
    if(!response.ok||new URL(response.url,location.href).origin!==location.origin)return;
    const value=await response.json(),original=new URL(ctx.originalUrl),match=taskPath(original.pathname).match(/^\/(?:contest|gym)\/(\d+)\/problem\/([A-Za-z]\d?)$/);
    if(value.status!=='OK'||!Array.isArray(value.result)||!match)return;
    const baseline=new Set(ctx.baseline||[]);
    const receipt=value.result.filter(row=>Number.isSafeInteger(row.id)&&newerReceipt(String(row.id),baseline)&&(!ctx.submissionId||String(row.id)===ctx.submissionId)&&String(row.problem?.contestId)===match[1]&&row.problem?.index.toUpperCase()===match[2].toUpperCase()&&row.author?.members?.some(member=>member.handle?.toLowerCase()===owner.toLowerCase())).sort((a,b)=>a.id-b.id)[0];
    if(!receipt)return;
    const verdict=normal(receipt.verdict)||'JUDGING';
    send({status:verdict==='JUDGING'?'judging':'finished',submissionId:String(receipt.id),...(verdict==='JUDGING'?{}:{verdict}),message:verdict==='JUDGING'?'原站已接收，正在评测。':'已读取原站本次新提交结果：'+verdict});
  }catch{}finally{work.polling=false;work.nextPoll=Date.now()+1000;}})();
}
return state;
}
