import { useEffect, useState } from 'react';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { TIER_NAMES } from '@/components/TierIcon.jsx';
import { SettingRow } from '@/components/SettingsControls.jsx';
import Tooltip from '@/components/Tooltip.jsx';
export default function AdminSettings({ api, onChanged, onError }) {
  const [config,setConfig]=useState(null),[busy,setBusy]=useState(false);
  useEffect(()=>{let alive=true;api('admin').then(value=>{if(alive)setConfig(value);}).catch(error=>onError?.(error.message));return()=>{alive=false;};},[api]);
  async function save(patch){setBusy(true);try{const value=await api('admin',{...config,...patch});setConfig(value);await onChanged?.();}catch(error){onError?.(error.message);}finally{setBusy(false);}}
  if(!config)return <p role="status">正在读取管理员设置…</p>;
  return <section aria-label="管理员控制"><h2>管理员控制<Tooltip label="管理员工作区说明" text="这些设置只用于独立管理员工作区。"/></h2><SettingRow title="经验等级"><BoundedNumber aria-label="管理员等级" min={1} max={100} value={config.level} required disabled={busy} onChange={event=>save({level:Number(event.target.value)})}/></SettingRow><SettingRow title="能力段位"><ThemedSelect aria-label="管理员段位" value={config.tier} disabled={busy} onChange={event=>save({tier:Number(event.target.value)})}>{TIER_NAMES.map((name,index)=><option key={name} value={index}>{name}</option>)}</ThemedSelect></SettingRow><SettingRow title="成就"><button type="button" className="primary" disabled={busy||config.allAchievements} onClick={()=>save({allAchievements:true})}>{config.allAchievements?'全部成就已获得':'解锁全部成就与称号'}</button></SettingRow></section>;
}
