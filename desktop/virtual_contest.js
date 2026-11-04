// Runs only in the authenticated, account-bound original contest target.
// CSRF/session material stays in the native form. A click is never a receipt.
function tbVirtualContest(ctx){
 const {spec,action,startMs}=ctx;
 const href=new URL(location.href),expected=new URL(spec.registrationUrl);
 if(href.protocol==='about:')return {state:'loading'};
 if(href.origin!==expected.origin)return {state:'login'};
 const result={url:location.origin+location.pathname,ready:document.readyState};
 if(document.readyState==='loading')return {...result,state:'loading'};
 if(/just a moment|checking your browser|人机验证|安全验证/i.test(document.title))return {...result,state:'verification'};
 if(/\/enter|\/login|\/auth\//.test(href.pathname))return {...result,state:'login'};
 const visible=node=>node&&!node.disabled&&getComputedStyle(node).display!=='none'&&getComputedStyle(node).visibility!=='hidden';
 const timeText=text=>{const match=String(text||'').trim().match(/^(?:(\d+)\s*d\s*)?(\d+):(\d{2}):(\d{2})$/);return match?Number(match[1]||0)*86400+Number(match[2])*3600+Number(match[3])*60+Number(match[4]):null;};
 if(spec.platform==='Codeforces'){
  const regular=[...document.querySelectorAll('.contest-state-regular')].find(node=>/virtual|虚拟|виртуал/i.test(node.textContent));
  if(regular&&href.pathname.replace(/\/$/,'')===new URL(spec.url).pathname){
   const panel=regular.closest('.roundbox')||regular.parentElement.parentElement;
   const phase=panel?.querySelector('.contest-state-phase')?.textContent||'';
   const seconds=timeText(panel?.querySelector('.countdown')?.textContent);
   if(seconds!==null&&seconds>0){
    const before=/before|尚未|开始前|до начала/i.test(phase);
    const inferred=before?Date.now()+seconds*1000:Date.now()+seconds*1000-spec.duration*60000;
    return {...result,state:'confirmed',startedMs:startMs&&Math.abs(startMs-inferred)<4000?startMs:Math.round(inferred/1000)*1000};
   }
   return {...result,state:'awaiting-clock'};
  }
  if(href.pathname!==expected.pathname)return {...result,state:'unsupported'};
  const form=[...document.forms].find(form=>form.querySelector('[name="virtual"][value="true"]')&&form.querySelector('[name="startDay"]')&&form.querySelector('[name="startTime"]'));
  if(!form)return {...result,state:'login'};
  const button=[...form.querySelectorAll('input[type=submit],button[type=submit]')].find(node=>/virtual|虚拟|виртуал/i.test(node.value||node.textContent));
  if(!button||!visible(button))return {...result,state:'unsupported'};
  if(action!=='start')return {...result,state:'ready'};
  if(window.__tbVpDispatched)return {...result,state:'dispatched'};
  if(!Number.isFinite(startMs)||startMs<Date.now()+5000||startMs>Date.now()+180000)return {...result,state:'invalid-time'};
  const setter=(name,value)=>{const input=form.elements.namedItem(name);if(!input)return false;Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));return true;};
  const date=new Date(startMs),months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  setter('startDay',months[date.getMonth()]+'/'+String(date.getDate()).padStart(2,'0')+'/'+date.getFullYear());
  setter('startTime',String(date.getHours()).padStart(2,'0')+':'+String(date.getMinutes()).padStart(2,'0'));
  setter('clientTimezoneOffset',String(-date.getTimezoneOffset()));
  const individual=form.querySelector('[name=takePartAs][value=personal]');if(individual&&!individual.checked)individual.click();
  window.__tbVpDispatched=true;button.click();return {...result,state:'dispatched'};
 }
 if(spec.platform==='QOJ'){
  const dashboard='/contest/'+spec.contestId,registration=dashboard+'/virtual/register';
  if(![dashboard,registration].includes(href.pathname.replace(/\/$/,'')))return {...result,state:'unsupported'};
  // The confirmation page exposes the provider's actual VP duration. Never
  // register a shorter local mock against a longer original-site clock.
  const confirm=document.querySelector('form#form-register_vp'),entry=document.querySelector('form#form-regvir');
  const form=href.pathname===registration?confirm:entry;
  if(form){
   const destination=new URL(form.getAttribute('action')||location.href,location.href);
   if(destination.origin!==href.origin||destination.pathname!==href.pathname)return {...result,state:'unsupported'};
   const button=form.querySelector(href.pathname===registration?'#button-submit-register_vp[name=submit-register_vp]':'#button-submit-regvir[name=submit-regvir]');
   if(!visible(button))return {...result,state:'unsupported'};
   const intentKey=href.pathname===registration?'qoj-confirm':'qoj-entry';
   if(confirm){
    const durations=[...document.querySelectorAll('li')].map(node=>node.textContent.trim().match(/^The contest is (\d+) minutes long\.$/i)||node.textContent.trim().match(/^(?:本场)?比赛(?:的)?时长(?:为|是|：|:)\s*(\d+)\s*分钟[。.！!]?$/)).filter(Boolean).map(match=>Number(match[1]));
    if(new Set(durations).size!==1)return {...result,state:'awaiting-clock'};
    if(durations[0]!==spec.duration)return {...result,state:'duration-mismatch'};
   }
   if(action!=='start')return {...result,state:'ready',intentKey};
   if(window.__tbVpDispatched)return {...result,state:'dispatched',intentKey};
   window.__tbVpDispatched=true;button.click();return {...result,state:'dispatched',intentKey};
  }
  // Match two values from the same server-rendered response. Browser clock
  // skew and a ticking text label do not redefine the original start time.
  if(ctx.attempted?.length){
   const clocks=[...document.querySelectorAll('.countdown[data-rest]')].filter(node=>/^Contest ends in$/i.test(node.closest('.card')?.querySelector('.card-header')?.textContent.trim()||''));
   const stamps=[...document.querySelectorAll('.uoj-footer p')].map(node=>node.textContent.trim().match(/^Server Time:\s*(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\s*\(UTC([+-])(\d{1,2})(?::(\d{2}))?\)$/)).filter(Boolean);
   if(clocks.length===1&&stamps.length===1&&/^\d{1,8}$/.test(clocks[0].dataset.rest)){
    const remaining=Number(clocks[0].dataset.rest),stamp=stamps[0];
    const hours=Number(stamp[4]),minutes=Number(stamp[5]||0);
    const serverMs=Date.parse(stamp[1]+'T'+stamp[2]+stamp[3]+String(hours).padStart(2,'0')+':'+String(minutes).padStart(2,'0'));
    if(hours<=14&&minutes<60&&remaining>0&&remaining<=spec.duration*60&&Number.isFinite(serverMs))return {...result,state:'confirmed',startedMs:serverMs+remaining*1000-spec.duration*60000};
   }
  }
  return {...result,state:'awaiting-clock'};
 }
 // QOJ and Nowcoder are detected on the actual contest page. A platform name
 // or an ordinary practice/start control alone is not a VP capability.
 const heading=[...document.querySelectorAll('h3,h4,h5,.panel-heading,.card-header')].find(node=>/^(?:Virtual Contest|Virtual participation|虚拟比赛|虚拟参赛|VP)$/i.test(node.textContent.trim()));
 if(!heading)return {...result,state:'unsupported'};
 const panel=heading.closest('.panel,.card,.roundbox')||heading.parentElement;
 const timer=panel.querySelector('[data-start-time],[data-end-time],time[datetime]');
 if(timer){
  const began=Date.parse(timer.dataset.startTime||timer.getAttribute('datetime')||'');
  if(Number.isFinite(began)&&/in progress|进行中|即将开始|已开始/i.test(panel.textContent))return {...result,state:'confirmed',startedMs:began};
 }
 const button=[...panel.querySelectorAll('button,input[type=submit]')].find(node=>[node.textContent,node.value].some(label=>/^(?:Start!?|开始(?:虚拟比赛|虚拟参赛)?|开始 VP)$/i.test((label||'').trim())));
 if(!button||!visible(button))return {...result,state:'awaiting-clock'};
 const form=button.form;
 if(!form||new URL(form.getAttribute('action')||location.href,location.href).origin!==href.origin)return {...result,state:'unsupported'};
 if(action!=='start')return {...result,state:'ready'};
 if(window.__tbVpDispatched)return {...result,state:'dispatched'};
 window.__tbVpDispatched=true;button.click();return {...result,state:'dispatched'};
}
