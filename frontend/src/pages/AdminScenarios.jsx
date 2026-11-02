import {useEffect,useState} from 'react';
import {RotateCcw,Trash2} from 'lucide-react';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import './AdminAccounts.css';

export default function AdminScenarios({api,onError}){
 const [state,setState]=useState(null),[busy,setBusy]=useState(false),[pending,setPending]=useState(null);
 useEffect(()=>{let alive=true;api('admin/scenario').then(value=>{if(alive)setState(value);}).catch(issue=>{if(alive)onError?.(issue.message);});return()=>{alive=false;};},[api]);
 async function change(body){
  if(busy)return;setBusy(true);setPending(null);
  try{await api('admin/scenario',body);window.dispatchEvent(new Event('tb:account-change'));}
  catch(issue){onError?.(issue.message);setBusy(false);}
 }
 async function recycle(){
  if(busy)return;setBusy(true);setPending(null);
  try{let next=state;for(const row of state.workspaces.filter(row=>row.id!==state.active))next=await api('admin/scenario',{action:'recycle',id:row.id});setState(next);}
  catch(issue){onError?.(issue.message);setState(await api('admin/scenario').catch(()=>state));}
  finally{setBusy(false);}
 }
 if(!state)return null;
 const inactive=state.workspaces.filter(row=>row.id!==state.active);
 return <div className="admin-scenario-actions" role="group" aria-label="管理员测试工作区操作">
  <ThemedSelect aria-label="测试工作区" value={state.active} disabled={busy} onChange={event=>change({action:'select',id:event.target.value})}>
   <option value="maintenance">维护工作区</option>
   {state.workspaces.map((row,index)=><option key={row.id} value={row.id}>测试 {index+1}</option>)}
  </ThemedSelect>
  <button type="button" className="secondary icon-button" aria-label="重置为新注册状态" title="重置为新注册状态" disabled={busy||state.workspaces.length>=state.limit} onClick={event=>setPending({action:'fresh',anchor:event.currentTarget,requestId:crypto.randomUUID()})}><RotateCcw size={18}/></button>
  <button type="button" className="secondary icon-button" aria-label="回收未使用的测试工作区" title="回收未使用的测试工作区" disabled={busy||!inactive.length} onClick={event=>setPending({action:'recycle',anchor:event.currentTarget})}><Trash2 size={18}/></button>
  {pending&&<PopConfirm anchor={pending.anchor} label="测试工作区操作确认" title={pending.action==='fresh'?'创建新的初次注册测试？当前工作区会保留。':'将未使用的测试工作区移入系统回收站？'} cancelLabel="取消" confirmLabel="确认" onCancel={()=>setPending(null)} onConfirm={()=>pending.action==='fresh'?change({action:'fresh',requestId:pending.requestId}):recycle()}/>}
 </div>;
}
