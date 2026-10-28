// The native form/field names come from QOJ's public problem page and uoj.js.
// Submission tables are parsed by their headers. Unknown DOM fails closed;
// neither a score copied from page prose nor the custom-test form is a receipt.
function tbQojPage(ctx, action, postMessage) {
  if (window!==window.top || location.origin!=='https://qoj.ac') return null;
  let target;
  try { target=new URL(ctx.originalUrl); } catch { return null; }
  const pid=target.pathname.match(/^\/problem\/([1-9]\d*)$/)?.[1];
  if (target.origin!==location.origin || !pid || target.username || target.password) return null;
  const send=value=>postMessage({tbOfficial:true,sessionId:ctx.sessionId,...value});
  const key=ctx.sessionId+':'+target.pathname;
  const state=window.__tbQoj?.key===key?window.__tbQoj:(window.__tbQoj={key,busy:false,polling:false,nextPoll:0});
  const url=value=>{try{const u=new URL(value,location.href);return u.origin===location.origin?u:null;}catch{return null;}};
  const visible=node=>node&&node.getClientRects().length>0;
  const text=node=>(node?.textContent||'').replace(/\s+/g,' ').trim();
  function owner(doc=document) {
    const nav=doc.querySelector('.navbar');if(!nav)return '';
    const links=[...nav.querySelectorAll('a[href]')];
    const logout=links.some(a=>url(a.getAttribute('href'))?.pathname==='/logout')
      || nav.querySelector('[onclick*="logout"],form[action$="/logout"]');
    if(!logout)return '';
    return links.map(a=>url(a.getAttribute('href'))?.pathname.match(/^\/user\/profile\/([A-Za-z0-9_-]{1,64})\/?$/)?.[1]).find(Boolean)||'';
  }
  function login() {return /\/login(?:\/|$)/.test(location.pathname)||[...document.querySelectorAll('input[type=password]')].some(visible);}
  function challenge(doc=document) {return /just a moment|checking your browser|安全验证|人机验证/i.test(doc.title)||!!doc.querySelector('iframe[src*=captcha],iframe[src*=challenge]');}
  const headers=table=>[...table.querySelectorAll('thead tr:first-child th,thead tr:first-child td')].length
    ?[...table.querySelectorAll('thead tr:first-child th,thead tr:first-child td')]:[...table.querySelectorAll('tr:first-child th,tr:first-child td')];
  function tableSchema(table) {
    const names=headers(table).map(text),column=pattern=>names.findIndex(name=>pattern.test(name));
    const value={table,id:column(/^(?:#|ID|Submission(?: ID)?|提交(?:编号|ID)?)$/i),problem:column(/^(?:Problem|题目)$/i),
      owner:column(/^(?:Submitter|User(?:name)?|提交者|用户名)$/i),result:column(/^(?:Result|Score|Status|Verdict|得分|结果|状态)$/i)};
    return Object.values(value).filter(v=>typeof v==='number').every(v=>v>=0)?value:null;
  }
  const schema=doc=>[...doc.querySelectorAll('table')].map(tableSchema).find(Boolean);
  function verdict(value) {
    const name=value.trim().replace(/_/g,' ').replace(/\s+/g,' ').toUpperCase();
    if(/^100(?:\.0+)?$/.test(name))return 'AC';
    return ({AC:'AC',ACCEPTED:'AC','100':'AC','100.0':'AC',WA:'WA','WRONG ANSWER':'WA',
      TLE:'TLE','TIME LIMIT EXCEEDED':'TLE',MLE:'MLE','MEMORY LIMIT EXCEEDED':'MLE',
      RE:'RE','RUNTIME ERROR':'RE',CE:'CE','COMPILE ERROR':'CE','COMPILATION ERROR':'CE',
      OLE:'OLE','OUTPUT LIMIT EXCEEDED':'OLE','答案正确':'AC','答案错误':'WA','编译错误':'CE',
      '运行错误':'RE','时间超限':'TLE','内存超限':'MLE'})[name]||null;
  }
  function receipts(doc) {
    const meta=schema(doc);if(!meta)return null;
    const expected=ctx.baselineOwner||owner(),values=[];
    for(const row of meta.table.querySelectorAll('tr')) {
      const cells=[...row.querySelectorAll(':scope > td')];if(cells.length<=Math.max(meta.id,meta.problem,meta.owner,meta.result))continue;
      const link=[...cells[meta.id].querySelectorAll('a[href]')].map(a=>url(a.getAttribute('href'))).find(u=>/^\/submission\/[1-9]\d*$/.test(u?.pathname||''));
      const problem=[...cells[meta.problem].querySelectorAll('a[href]')].some(a=>url(a.getAttribute('href'))?.pathname===target.pathname);
      const user=[...cells[meta.owner].querySelectorAll('a[href]')].some(a=>url(a.getAttribute('href'))?.pathname==='/user/profile/'+expected);
      if(!link||!problem||!expected||!user)continue;
      const id=link.pathname.split('/').pop(),result=text(cells[meta.result]);
      const status=/^(?:Judging|Waiting|Running|Pending|Queued|Compiling|评测中|等待评测)(?:\b|$)/i.test(result)?'JUDGING':verdict(result);
      values.push({id,verdict:status,score:/^\d+(?:\.\d+)?$/.test(result)?Number(result):null});
    }
    return values;
  }
  async function get(path) {
    const response=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(7000)});
    const final=url(response.url||path),wanted=url(path);
    if(!response.ok||final?.pathname!==wanted?.pathname||Number(response.headers.get('content-length'))>2000000)return null;
    for(const [key,value] of wanted.searchParams)if(final.searchParams.get(key)!==value)return null;
    const html=await response.text();if(html.length>2000000)return null;
    const doc=new DOMParser().parseFromString(html,'text/html');
    return challenge(doc)||doc.querySelector('input[type=password]')?null:doc;
  }
  async function list() {
    const current=owner();if(!current||ctx.baselineOwner&&ctx.baselineOwner!==current)return null;
    const path='/submissions?'+new URLSearchParams({problem_id:pid,submitter:current});
    const doc=await get(path);if(!doc||owner(doc)!==current||!schema(doc))return null;
    return {doc,owner:current};
  }
  async function prepare() {
    const value=await list();if(!value)return null;
    const rows=receipts(value.doc);if(!rows)return null;
    return {baseline:rows.map(r=>r.id),baselineKnown:true,baselineOwner:value.owner};
  }
  function isNew(id) {
    const previous=(ctx.baseline||[]).filter(id=>/^[1-9]\d*$/.test(id));
    return ctx.baselineKnown&&/^[1-9]\d*$/.test(id)&&!previous.includes(id)&&previous.every(old=>BigInt(id)>BigInt(old))&&(!ctx.submissionId||ctx.submissionId===id);
  }
  function report(receipt) {
    const signature=receipt.id+':'+receipt.verdict;if(state.reported===signature)return;
    state.reported=signature;
    send({status:receipt.verdict==='JUDGING'?'judging':'finished',submissionId:receipt.id,
      ...(receipt.verdict==='JUDGING'?{}:{verdict:receipt.verdict}),message:receipt.verdict==='JUDGING'?'原站已接收，正在评测。':'本次提交结果：'+receipt.verdict});
  }
  async function detail(receipt) {
    const doc=await get('/submission/'+receipt.id);if(!doc||owner(doc)!==ctx.baselineOwner)return null;
    // The exact detail URL is already bound to a new owned/problem-matched
    // list entry. Some native detail layouts omit the summary's ID column.
    const row=receipts(doc)?.find(row=>row.id===receipt.id)||receipt;
    if(row.verdict)return row;
    // A partial numeric score is not proof of WA: inspect actual judge cells.
    const cells=[...doc.querySelectorAll('.uoj-status,.verdict')];
    for(const table of doc.querySelectorAll('table')){
      const index=headers(table).map(text).findIndex(name=>/^(?:Status|Result|Verdict|状态|结果)$/i.test(name));
      if(index>=0)for(const tr of table.querySelectorAll('tr')){const cell=tr.querySelectorAll(':scope > td')[index];if(cell)cells.push(cell);}
    }
    const safe=cells.filter(node=>!node.closest('pre,code,textarea,script')&&!node.querySelector('pre,code,textarea,script'));
    const actual=safe.map(node=>verdict(text(node))).find(value=>value&&value!=='AC');
    return actual?{...row,verdict:actual}:null;
  }
  function poll() {
    if(!ctx.attempted||!ctx.baselineKnown||state.polling||Date.now()<state.nextPoll)return;
    state.polling=true;
    (async()=>{try{
      let rows=receipts(document)||[];
      if(!rows.some(row=>isNew(row.id))){const value=await list();if(value)rows=receipts(value.doc)||[];}
      const receipt=rows.filter(row=>isNew(row.id)).sort((a,b)=>BigInt(a.id)<BigInt(b.id)?-1:1)[0];
      if(!receipt)return;
      if(receipt.verdict)report(receipt);
      else {const actual=await detail(receipt);if(actual)report(actual);}
    }catch{}finally{state.polling=false;state.nextPoll=Date.now()+2000;}})();
  }
  function form() {
    const node=document.querySelector('#form-answer');
    return node&&node.method.toLowerCase()==='post'&&url(node.getAttribute('action')||location.href)?.pathname===target.pathname?node:null;
  }
  function inspect() {
    if(challenge())return {status:'needs_verification',attempted:false,message:'请在浏览器完成原站验证。'};
    if(login()||!owner()&&document.querySelector('.navbar a[href="/login"]'))return {status:'needs_login',attempted:false,message:'请在弹出的浏览器登录原站，登录后会继续本次提交。'};
    if(ctx.attempted){poll();return {status:'submitted',message:'正在读取原站本次提交结果。'};}
    if(!owner())return {status:'loading',message:'正在读取原站登录状态。'};
    if(location.pathname!==target.pathname){
      if(ctx.resumeAfterLogin)location.assign(target.href+'#tab-submit');
      return {status:'loading',message:'正在加载原站提交表单。'};
    }
    return form()?.querySelector('[name="answer_answer_language"]')?{status:'ready',message:'后台连接已就绪。'}:{status:'loading',message:'正在加载原站提交表单。'};
  }
  async function submit(manual) {
    if(manual&&state.manualFilled)return send({status:'awaiting_submit',message:'代码已填入浏览器，请在官网点击提交。结果会自动同步到 TB。'});
    const check=inspect();if(check.status!=='ready')return send(check);
    const node=form(),editor=node?.querySelector('textarea[name="answer_answer_editor"]'),language=node?.querySelector('select[name="answer_answer_language"]');
    const button=node?.querySelector('#button-submit-answer'),mode=node?.querySelector('input[type=radio][name="answer_answer_upload_type"][value=editor]');
    if(!node||!editor||!language||!button||!mode||mode.disabled)return send({status:'error',attempted:false,message:'原站提交控件尚未就绪，未发送代码。'});
    document.querySelector('a[href="#tab-submit"]')?.click();
    if(!mode.checked)mode.click();
    const item=[...language.options].map(option=>({option,candidate:compilerCandidate(text(option),ctx.code,'QOJ',ctx.language||'cpp17')}))
      .filter(value=>value.candidate&&!value.option.disabled).sort((a,b)=>a.candidate.score-b.candidate.score)[0];
    if(!item)return send({status:'error',attempted:false,message:'没有找到所需原站编译器，未发送代码。'});
    language.value=item.option.value;language.dispatchEvent(new Event('change',{bubbles:true}));
    for(const wrapper of node.querySelectorAll('.CodeMirror'))if(wrapper.CodeMirror){wrapper.CodeMirror.setValue(ctx.code);wrapper.CodeMirror.save();}
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(editor,ctx.code);
    editor.dispatchEvent(new Event('input',{bubbles:true}));editor.dispatchEvent(new Event('change',{bubbles:true}));
    const snapshot=await prepare();
    if(!snapshot||owner()!==snapshot.baselineOwner)return send({status:'error',attempted:false,message:'暂时无法读取本账号的提交记录，尚未发送代码，请稍后重试。'});
    Object.assign(ctx,snapshot);
    if(manual){
      if(!state.manualFilled){
        state.manualFilled=true;
        const submitted=event=>{if(event.defaultPrevented)return;node.removeEventListener('submit',submitted);ctx.attempted=true;send({status:'submitted',attempted:true,submittedCode:editor.value,...snapshot,message:'已在官网提交，正在读取原站结果。'});};
        node.addEventListener('submit',submitted);
      }
      return send({status:'awaiting_submit',...snapshot,message:'代码已填入浏览器，请在官网点击提交。结果会自动同步到 TB。'});
    }
    if(!node.checkValidity()||button.disabled||button.classList.contains('disabled')||!mode.checked)return send({status:'error',attempted:false,message:'原站提交控件尚未就绪，未发送代码。'});
    // The existing native handler owns CSRF, validation and the actual POST.
    // Checkpoint before navigation; never invoke submit() or construct a POST.
    await send({status:'submitted',attempted:true,...snapshot,compiler:item.candidate.label,message:'正在操作原站表单，尚未确认受理。'});
    node.addEventListener('submit',event=>{if(event.defaultPrevented){ctx.attempted=false;send({status:'error',attempted:false,message:'原站表单未通过校验，尚未发送代码。'});}},{once:true});
    ctx.attempted=true;button.click();return {status:'submitted'};
  }
  if(action==='observe')return null;
  if(action==='submit'||action==='prepare'){
    if(!state.busy&&!ctx.attempted){state.busy=true;submit(action==='prepare').catch(error=>send({status:ctx.attempted?'unconfirmed':'error',attempted:!!ctx.attempted,message:'原站表单操作未完成：'+String(error).slice(0,120)})).finally(()=>{state.busy=false;});}
    return {status:'loading'};
  }
  return inspect();
}
