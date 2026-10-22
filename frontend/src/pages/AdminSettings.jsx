import { useEffect, useState } from 'react';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { TIER_NAMES } from '@/components/TierIcon.jsx';
import { SettingRow } from '@/components/SettingsControls.jsx';
import Tooltip from '@/components/Tooltip.jsx';
export default function AdminSettings({ api, onChanged, onError }) {
  const [config,setConfig]=useState(null),[busy,setBusy]=useState(false);
  const [session,setSession]=useState(null),[password,setPassword]=useState(''),[authError,setAuthError]=useState('');
  useEffect(()=>{let alive=true;api('admin/session').then(value=>{if(alive)setSession(value)}).catch(error=>{if(alive)setAuthError(error.message)});return()=>{alive=false}},[api]);
  async function authenticate(event){event.preventDefault();if(busy)return;setBusy(true);setAuthError('');try{setSession(await api('admin/session',{password}));setPassword('');}catch(error){setAuthError(error.message)}finally{setBusy(false)}}
  async function logout(){setBusy(true);setAuthError('');try{setSession(await api('admin/logout',{}));}catch(error){setAuthError(error.message)}finally{setBusy(false)}}
  useEffect(()=>{let alive=true;api('admin').then(value=>{if(alive)setConfig(value);}).catch(error=>onError?.(error.message));return()=>{alive=false;};},[api]);
  async function save(patch){setBusy(true);try{const value=await api('admin',{...config,...patch});setConfig(value);await onChanged?.();}catch(error){onError?.(error.message);}finally{setBusy(false);}}
  if(!config)return <p role="status">正在读取管理员设置…</p>;
  return <section aria-label="管理员控制"><h2>管理员控制<Tooltip label="管理员工作区说明" text="本地测试数据与用户版隔离；公共榜单管理须登录已授权的 admin 账号。"/></h2><SettingRow title="管理账号"><strong>admin</strong></SettingRow>{session?.authenticated?<SettingRow title="公共榜单"><button type="button" className="secondary" disabled={busy} onClick={logout}>退出管理账号</button></SettingRow>:<form onSubmit={authenticate}><SettingRow title="管理员密码"><input aria-label="admin 密码" type="password" autoComplete="current-password" minLength={8} maxLength={128} required value={password} disabled={busy} onChange={event=>setPassword(event.target.value)}/></SettingRow><button className="primary" disabled={busy||!session?.configured}>登录管理账号</button></form>}{authError&&<p className="connection-error" role="alert">{authError}</p>}<SettingRow title="经验等级"><BoundedNumber aria-label="管理员等级" min={1} max={100} value={config.level} required disabled={busy} onChange={event=>save({level:Number(event.target.value)})}/></SettingRow><SettingRow title="能力段位"><ThemedSelect aria-label="管理员段位" value={config.tier} disabled={busy} onChange={event=>save({tier:Number(event.target.value)})}>{TIER_NAMES.map((name,index)=><option key={name} value={index}>{name}</option>)}</ThemedSelect></SettingRow><SettingRow title="成就"><button type="button" className="primary" disabled={busy||config.allAchievements} onClick={()=>save({allAchievements:true})}>{config.allAchievements?'全部成就已获得':'解锁全部成就与称号'}</button></SettingRow></section>;
}
