import ThemedSelect from './ThemedSelect.jsx';
import { Check, Moon, Sun } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
import BoundedNumber from './BoundedNumber.jsx';
import './SettingsControls.css';

export function SettingRow({title,hint,children}){
  return <div className="setting-line"><div className="setting-label"><strong>{title}</strong>{hint&&<Tooltip text={hint} label={`${title}说明`}/>}</div><div className="setting-control">{children}</div></div>;
}
export function VisualPreferences({prefs,setPrefs}){
  return <section className="visual-preferences" aria-label="界面偏好"><h2>界面偏好</h2>
    <SettingRow title="主题" hint="为阅读区和控件选择深浅配色。"><div className="choice-group">{[['dark','石墨深色',Moon],['light','云白浅色',Sun]].map(([key,label,Icon])=><Tooltip key={key} text={label}><button aria-label={label} aria-pressed={prefs.theme===key} className={prefs.theme===key?'active':''} onClick={()=>setPrefs(previous=>({...previous,theme:key}))}><Icon size={18}/></button></Tooltip>)}</div></SettingRow>
    <SettingRow title="强调色" hint="用于核心操作、选中项和键盘焦点。"><div className="accent-options">{[['violet','雾紫','#9d8df1'],['blue','澄空蓝','#6fa5e8'],['teal','松石绿','#5bbda4'],['amber','暖琥珀','#d7a45e']].map(([id,name,color])=><Tooltip key={id} text={name}><button aria-label={name} aria-pressed={prefs.accent===id} style={{'--swatch':color}} className={prefs.accent===id?'active':''} onClick={()=>setPrefs(previous=>({...previous,accent:id}))}><span/>{prefs.accent===id&&<Check size={12}/>}</button></Tooltip>)}</div></SettingRow>
    <SettingRow title="难度显示"><ThemedSelect aria-label="难度显示" value={prefs.difficultyDisplay==='text'?'text':'number'} onChange={event=>setPrefs(previous=>({...previous,difficultyDisplay:event.target.value}))}><option value="number">数字</option><option value="text">文字</option></ThemedSelect></SettingRow>
    <SettingRow title="界面字号" hint="可输入 13–22 px；题目列表和控件同步调整。"><BoundedNumber aria-label="界面字号" value={prefs.fontSize} min={13} max={22} unit="px" required onChange={event=>setPrefs(previous=>({...previous,fontSize:Number(event.target.value)}))}/></SettingRow>
  </section>;
}
export function InteractionSettings({prefs,setPrefs,display,onFullscreen}){
  const switches=[['compact','紧凑列表','在同一屏显示更多题目。'],['collapsed','收起左侧栏','保留导航图标；Ctrl+B 可随时切换。'],['showPlatforms','显示比赛平台','仅控制题库单题前的平台图标。'],['widgets','底部时钟','在右下角状态栏显示北京时间。']];
  return <section aria-label="交互设置"><h2>交互设置</h2><SettingRow title="全屏" hint={display.available?'按 F11 或使用此开关。':'仅桌面版可用。'}><input className="toggle" aria-label="全屏" type="checkbox" checked={display.fullscreen} disabled={!display.available} onChange={event=>onFullscreen(event.target.checked)}/></SettingRow>{switches.map(([id,title,hint])=><SettingRow title={title} hint={hint} key={id}><input className="toggle" aria-label={title} type="checkbox" checked={prefs[id]} onChange={event=>setPrefs(previous=>({...previous,[id]:event.target.checked}))}/></SettingRow>)}<SettingRow title="题库每页题数"><BoundedNumber aria-label="题库每页题数" min={10} max={200} value={prefs.libraryPageSize??50} required onChange={event=>setPrefs(previous=>({...previous,libraryPageSize:Number(event.target.value)}))}/></SettingRow></section>;
}
