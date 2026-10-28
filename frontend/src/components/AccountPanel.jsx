import {useEffect, useRef, useState} from 'react';
import {Check, ExternalLink, LoaderCircle, LockKeyhole, LogOut, RefreshCw} from 'lucide-react';
import './AccountPanel.css';

const PLATFORMS=[['codeforces','Codeforces'],['atcoder','AtCoder'],['nowcoder','牛客'],['luogu','洛谷']];
const fields=value=>Object.fromEntries(PLATFORMS.map(([key])=>[key,value?.settings?.accounts?.[key]||'']));

export default function AccountPanel({api, account, profileSnapshot, hub, onProfileChanged, onHubChanged}){
  const [nickname,setNickname]=useState(profileSnapshot?.profile?.nickname||account?.nickname||'');
  const [draft,setDraft]=useState(()=>fields(hub)), [passwords,setPasswords]=useState({oldPassword:'',newPassword:'',confirmation:''});
  const [busy,setBusy]=useState(''), [error,setError]=useState(''), [saved,setSaved]=useState(''), [preparation,setPreparation]=useState(null);
  const dirty=useRef(new Set()), changed=useRef({onProfileChanged,onHubChanged}), live=useRef(true), generation=useRef(0);
  changed.current={onProfileChanged,onHubChanged};
  useEffect(()=>{const next=fields(hub);setDraft(previous=>({...previous,...Object.fromEntries(Object.entries(next).filter(([key])=>!dirty.current.has(key)))}));},[hub?.settings?.accounts]);
  useEffect(()=>{
    live.current=true;let timer;
    const poll=async()=>{
      const revision=generation.current;
      try{
        const [status,value]=await Promise.all([api('browser-preparation'),api('hub')]);
        if(!live.current)return;if(revision!==generation.current){timer=setTimeout(poll,3000);return;}setPreparation(status);changed.current.onHubChanged?.(value);
        const next=fields(value);setDraft(previous=>({...previous,...Object.fromEntries(Object.entries(next).filter(([key])=>!dirty.current.has(key)))}));
      }catch{/* Manual account binding remains usable when the browser is closed. */}
      if(live.current)timer=setTimeout(poll,3000);
    };void poll();return()=>{live.current=false;clearTimeout(timer);};
  },[api]);
  const run=async(kind,action)=>{
    if(busy)return;generation.current++;setBusy(kind);setError('');setSaved('');
    try{await action();if(live.current)setSaved(kind);}catch(issue){if(live.current)setError(issue.message);}finally{generation.current++;if(live.current)setBusy('');}
  };
  const saveNickname=event=>{event.preventDefault();void run('nickname',async()=>{const value=await api('profile',{nickname:nickname.trim()});if(live.current){setNickname(value.profile.nickname);changed.current.onProfileChanged?.(value);}});};
  const saveAccounts=event=>{
    event.preventDefault();const keys=[...dirty.current];const sent=Object.fromEntries(keys.map(key=>[key,draft[key].trim()]));
    void run('accounts',async()=>{const value=await api('hub/configure',{accounts:sent});if(live.current){for(const key of keys)if(draft[key].trim()===sent[key])dirty.current.delete(key);setDraft(fields(value));changed.current.onHubChanged?.(value);}});
  };
  const changePassword=event=>{
    event.preventDefault();if(passwords.newPassword!==passwords.confirmation){setError('两次输入的新密码不一致');return;}
    void run('password',async()=>{await api('account/password',{oldPassword:passwords.oldPassword,newPassword:passwords.newPassword});if(live.current)setPasswords({oldPassword:'',newPassword:'',confirmation:''});});
  };
  const login=platform=>void run('login:'+platform,async()=>{const value=preparation||await api('browser-preparation');const browser=value.preferredBrowser||value.browsers?.find(item=>item.available)?.id||'edge';await api('browser-preparation',{action:'open-login',platform,browser});});
  return <div className="account-panel">
    <div className="account-panel-top"><form onSubmit={saveNickname} className="account-nickname"><label htmlFor="account-panel-nickname">修改昵称</label><input id="account-panel-nickname" aria-label="用户昵称" autoComplete="nickname" maxLength={32} value={nickname} required disabled={Boolean(busy)} onChange={event=>{setNickname(event.target.value);setSaved('');}}/><button type="submit" className="icon-button primary" aria-label="保存昵称" title="保存昵称" disabled={Boolean(busy)||!nickname.trim()}>{busy==='nickname'?<LoaderCircle size={17} className="spin"/>:<Check size={17}/>}</button></form>
    {!window.__tbAdmin&&<details className="account-password-edit"><summary><LockKeyhole size={16}/>修改密码</summary><form onSubmit={changePassword}>{[['oldPassword','原密码','current-password'],['newPassword','新密码','new-password'],['confirmation','确认新密码','new-password']].map(([key,label,complete])=><label key={key}><span>{label}</span><input type="password" aria-label={label} autoComplete={complete} minLength={8} maxLength={128} required disabled={Boolean(busy)} value={passwords[key]} onChange={event=>setPasswords(previous=>({...previous,[key]:event.target.value}))}/></label>)}<button type="submit" className="icon-button primary" aria-label="保存新密码" title="修改密码" disabled={Boolean(busy)}>{busy==='password'?<LoaderCircle size={17} className="spin"/>:<Check size={17}/>}</button></form></details>}
    </div>
    <form className="account-platform-form" onSubmit={saveAccounts}><div className="account-platform-grid">{PLATFORMS.map(([key,label])=><label key={key}><span>{label}</span><div><input aria-label={`${label}公开账号`} value={draft[key]} autoComplete="off" spellCheck={false} disabled={Boolean(busy)} onChange={event=>{dirty.current.add(key);setDraft(previous=>({...previous,[key]:event.target.value}));setSaved('');}}/><button type="button" className="icon-button" aria-label={`登录${label}`} title={`登录${label}`} disabled={Boolean(busy)} onClick={()=>login(label)}>{busy==='login:'+label?<LoaderCircle size={15} className="spin"/>:<ExternalLink size={15}/>}</button></div></label>)}</div>
      <div className="account-panel-actions"><button type="submit" className="icon-button primary" aria-label="保存平台账号" title="保存账号" disabled={Boolean(busy)||dirty.current.size===0}>{busy==='accounts'?<LoaderCircle size={17} className="spin"/>:<Check size={17}/>}</button><button type="button" className="icon-button" aria-label="刷新公开记录" title="刷新公开记录" disabled={Boolean(busy)} onClick={()=>void run('refresh',async()=>changed.current.onHubChanged?.(await api('hub/sync',{})))}><RefreshCw size={17} className={busy==='refresh'?'spin':''}/></button><span className="account-panel-saved" role="status">{saved&&<Check size={16} aria-label="已保存"/>}</span>{!window.__tbAdmin&&<button type="button" className="icon-button account-panel-logout" aria-label="退出账号" title="退出账号" disabled={Boolean(busy)} onClick={()=>void run('logout',async()=>{const {saveBeforeLogout}=await import('@/app/Workbench.jsx');await saveBeforeLogout();await api('account/logout',{});window.dispatchEvent(new Event('tb:account-change'));})}><LogOut size={17}/></button>}</div>
    </form>
    {error&&<p role="alert" className="connection-error">{error}</p>}
  </div>;
}
