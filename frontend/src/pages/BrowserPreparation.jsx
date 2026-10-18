import { useCallback, useEffect, useRef, useState } from 'react';
import { ExternalLink, Globe, RefreshCw, X } from 'lucide-react';
import './BrowserPreparation.css';
export default function BrowserPreparation({ api, enabled }) {
 const [snapshot,setSnapshot]=useState(null),[open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[browser,setBrowser]=useState('edge');
 const dialog=useRef(null),close=useRef(null),restore=useRef(null);
 const refresh=useCallback(async()=>{try{setSnapshot(await api('browser-preparation'));}catch{}},[api]);
 useEffect(()=>{if(!enabled)return;let alive=true;api('browser-preparation').then(value=>{if(alive)setSnapshot(value);}).catch(()=>{});const show=()=>{setOpen(true);refresh();};window.addEventListener('tb:browser-preparation',show);return()=>{alive=false;window.removeEventListener('tb:browser-preparation',show);};},[api,enabled,refresh]);
 useEffect(()=>{const element=dialog.current;if(!element)return;if(open&&!element.open){restore.current=document.activeElement;element.showModal();close.current?.focus();}else if(!open&&element.open){element.close();if(restore.current?.isConnected)restore.current.focus();}},[open,snapshot?.available]);
 async function action(action,platform){if(busy)return;setBusy(true);setError('');try{const value=await api('browser-preparation',{action,browser,...(platform?{platform}:{})});if(action==='refresh')setSnapshot(value);}catch(issue){setError(issue.message);}finally{setBusy(false);}}
 if(!enabled||!snapshot?.available)return null;
 return <>{!snapshot.ready&&<aside className="browser-guide-banner"><Globe size={16}/><span>浏览器提交需要 Edge 或 Chrome。</span><button onClick={()=>setOpen(true)}>查看提交说明</button></aside>}
 <dialog ref={dialog} className="browser-guide-dialog" aria-labelledby="browser-guide-heading" onCancel={event=>{event.preventDefault();setOpen(false);}}>
 <header><h2 id="browser-guide-heading"><Globe size={19}/>浏览器原站提交</h2><button ref={close} aria-label="关闭浏览器提交说明" onClick={()=>setOpen(false)}><X size={18}/></button></header>
 <div className="browser-guide-content"><p>点击 TB 的“提交”后，会打开可见的原站提交页、填入代码并触发这一次提交。最终结果仍由原站评测，TB 自动读取对应回执。</p><p>首次使用请在 <strong>TB 打开的独立浏览器窗口</strong> 登录原站。登录会保留在该浏览器配置中，与你日常浏览器分别保存。无需安装浏览器扩展。</p>
 <label className="browser-guide-browser">登录时使用<select aria-label="准备使用的浏览器" value={browser} onChange={event=>setBrowser(event.target.value)}>{(snapshot.browsers||[{id:'edge',available:true},{id:'chrome',available:true}]).map(item=><option value={item.id} key={item.id} disabled={!item.available}>{item.id==='edge'?'Microsoft Edge':'Google Chrome'}{item.available?'':'（未安装）'}</option>)}</select></label>
 <div className="browser-guide-platforms">{snapshot.platforms?.map(item=><div key={item.platform}><strong>{item.platform}</strong><span>登录状态由浏览器原站管理</span><button className="browser-guide-button" disabled={busy} onClick={()=>action('open-login',item.platform)}><ExternalLink size={14}/>打开登录</button></div>)}</div>
 <ol className="browser-guide-steps"><li><h3>在 TB 写代码并点击提交</h3><p>只操作当前题目的原站表单，保留原站语言选择、CSRF、登录及验证码。</p></li><li><h3>登录或验证码由你完成</h3><p>验证时暂停；完成后回到 TB 再点击提交。已经发送的提交不会自动重复发送。</p></li><li><h3>自动读取这次提交的结果</h3><p>包括受理编号和最终判定；断开或超时会提示待核对，代码与记录保留。</p></li></ol>{error&&<p className="browser-guide-error" role="alert">{error}</p>}</div>
 <footer><button className="browser-guide-button" disabled={busy} onClick={()=>action('refresh')}><RefreshCw size={14}/>重新检测浏览器</button><button className="browser-guide-button" onClick={()=>setOpen(false)}>返回工作台</button></footer></dialog></>;
}
