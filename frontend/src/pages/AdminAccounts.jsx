import {useEffect,useRef,useState} from 'react';
import {KeyRound,Search,Trash2} from 'lucide-react';
import './AdminAccounts.css';

function ConfirmAccountAction({pending,busy,onConfirm,onClose}) {
  const dialog=useRef(null),[confirmation,setConfirmation]=useState('');
  useEffect(()=>{dialog.current?.showModal();},[]);
  const deleting=pending.action==='delete';
  return <dialog ref={dialog} className="admin-account-confirm" aria-labelledby="admin-account-confirm-title" onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
    <form onSubmit={event=>{event.preventDefault();if(confirmation===pending.target.loginId&&!busy)onConfirm();}}>
      <h3 id="admin-account-confirm-title">{deleting?'删除账号':'重置密码'}</h3>
      <p><strong>{pending.target.nickname}</strong> · {pending.target.loginId}</p>
      <p>{deleting?'将删除这个账号的云端学习数据、会话和社交关联。':'重置后，这个账号在所有设备上的原登录会话都会失效。'}</p>
      <label>输入登录号确认<input aria-label="确认操作的登录号" value={confirmation} maxLength={32} autoComplete="off" disabled={busy} onChange={event=>setConfirmation(event.target.value)}/></label>
      <div className="admin-account-confirm-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>取消</button><button type="submit" className={deleting?'danger':'primary'} disabled={busy||confirmation!==pending.target.loginId}>{busy?'正在处理…':deleting?'确认删除':'确认重置'}</button></div>
    </form>
  </dialog>;
}

export default function AdminAccounts({api}) {
  const [query,setQuery]=useState(''),[accounts,setAccounts]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[pending,setPending]=useState(null);
  async function search(event) {
    event.preventDefault();if(busy)return;
    setBusy(true);setError('');setNotice('');setAccounts(null);setPending(null);
    try {const result=await api('admin/accounts?q='+encodeURIComponent(query.trim()));setAccounts(result.accounts);}
    catch(issue){setError(issue.message);}finally{setBusy(false);}
  }
  async function perform() {
    if(busy||!pending)return;
    setBusy(true);setError('');setNotice('');
    const {target,action}=pending;
    try {
      await api('admin/accounts/'+(action==='delete'?'delete':'reset-password'),{userId:target.userId,loginId:target.loginId,confirmation:action==='delete'?'delete-account':'reset-password'});
      if(action==='delete')setAccounts([]);
      setNotice(action==='delete'?'账号已删除':'密码已重置，原登录已失效');setPending(null);
    }catch(issue){setError(issue.message);setPending(null);}finally{setBusy(false);}
  }
  return <section className="admin-accounts" aria-label="账号维护">
    <h3>账号维护</h3>
    <form className="admin-account-search" onSubmit={search}><input aria-label="查找账号" placeholder="完整登录号或公开 ID" value={query} minLength={4} maxLength={80} autoComplete="off" required disabled={busy} onChange={event=>{setQuery(event.target.value);setAccounts(null);setNotice('');setError('');}}/><button type="submit" className="secondary icon-button" aria-label="查找账号" title="查找账号" disabled={busy||query.trim().length<4}><Search size={18}/></button></form>
    {error&&<p className="connection-error" role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
    {accounts?.length===0&&!notice&&<p role="status">没有找到账号</p>}
    {accounts?.map(target=><div className="admin-account-row" key={target.userId}><div><strong>{target.nickname}</strong><small>{target.loginId}</small></div><div className="admin-account-actions"><button type="button" className="secondary icon-button" aria-label={`重置 ${target.loginId} 的密码`} title={target.protected?'管理员账号不可修改':'重置密码'} disabled={busy||target.protected} onClick={()=>setPending({action:'reset',target})}><KeyRound size={18}/></button><button type="button" className="secondary icon-button" aria-label={`删除账号 ${target.loginId}`} title={target.protected?'管理员账号不可修改':'删除账号'} disabled={busy||target.protected} onClick={()=>setPending({action:'delete',target})}><Trash2 size={18}/></button></div></div>)}
    {pending&&<ConfirmAccountAction pending={pending} busy={busy} onConfirm={perform} onClose={()=>setPending(null)}/>}
  </section>;
}
