import { useEffect, useState } from 'react';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { TIER_NAMES } from '@/components/TierIcon.jsx';
import { SettingRow } from '@/components/SettingsControls.jsx';
import Tooltip from '@/components/Tooltip.jsx';
import AdminAccounts from './AdminAccounts.jsx';
import AdminScenarios from './AdminScenarios.jsx';
import {ArrowUpCircle} from 'lucide-react';
export default function AdminSettings({ api, onChanged, onError }) {
  const [config,setConfig]=useState(null),[busy,setBusy]=useState(false);
  useEffect(()=>{let alive=true;api('admin').then(value=>{if(alive)setConfig(value);}).catch(error=>onError?.(error.message));return()=>{alive=false;};},[api]);
  async function save(patch){if(busy)return;const previous=config,next={...config,...patch};if(Object.keys(next).every(key=>next[key]===previous[key]))return;let saved=false;setConfig(next);setBusy(true);try{const value=await api('admin',next);setConfig(value);saved=true;if(value.level!==previous.level)window.dispatchEvent(new CustomEvent('tb:admin-level-change',{detail:{owner:window.__tbAccountUserId,from:previous.level,to:value.level}}));await onChanged?.();}catch(error){if(!saved)setConfig(previous);onError?.(error.message);}finally{setBusy(false);}}
  if(!config)return <p role="status">正在读取管理员设置…</p>;
  return <section aria-label="管理员控制"><h2>管理员控制<Tooltip label="管理员工作区说明" text="本地测试数据与用户版隔离。"/></h2><SettingRow title="测试工作区"><AdminScenarios api={api} onError={onError}/></SettingRow><SettingRow title="经验等级"><div className="admin-level-actions"><BoundedNumber aria-label="管理员等级" min={1} max={100} value={config.level} required disabled={busy} onChange={event=>save({level:Number(event.target.value)})}/><button type="button" className="secondary icon-button" aria-label="模拟升级" title="模拟升级" disabled={busy||config.level>=100} onClick={()=>save({level:config.level+1})}><ArrowUpCircle size={18}/></button></div></SettingRow><SettingRow title="能力段位"><ThemedSelect aria-label="管理员段位" value={config.tier} disabled={busy} onChange={event=>save({tier:Number(event.target.value)})}>{TIER_NAMES.map((name,index)=><option key={name} value={index}>{name}</option>)}</ThemedSelect></SettingRow><SettingRow title="预览全部成就"><input type="checkbox" className="toggle" aria-label="预览全部成就" checked={config.allAchievements} disabled={busy} onChange={event=>save({allAchievements:event.target.checked})}/></SettingRow><AdminAccounts api={api}/></section>;
}
