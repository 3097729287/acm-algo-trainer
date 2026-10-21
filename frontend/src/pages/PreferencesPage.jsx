import { Bell, Command, Download, Keyboard, Layers, Palette, RefreshCw, Settings2, SlidersHorizontal, UserRound, X } from 'lucide-react';
import { lazy, Suspense } from 'react';
import VisualStyleSettings from '../components/VisualStyleSettings.jsx';
import { InteractionSettings, VisualPreferences } from '../components/SettingsControls.jsx';
import Tooltip from '../components/Tooltip.jsx';
import NavigationSettings from './NavigationSettings.jsx';
import { SoftwareUpdatePanel } from './SoftwareUpdates.jsx';
import { UpdatePanel } from './ProgressPanels.jsx';
const DataHelpSettings=lazy(()=>import('./DataHelpSettings.jsx'));
const AvatarSettings=lazy(()=>import('../components/AvatarSettings.jsx'));

export default function PreferencesPage({tab,onTab,prefs,setPrefs,display,onFullscreen,api,softwareUpdate,hub,onHubChanged,onError,onContent,onMessages,onTutorial,onKeyboard,commands}) {
  const tabs=[['appearance','外观',Palette],['account','头像',UserRound],['interaction','交互设置',SlidersHorizontal],['navigation','导航',Layers],['updates','更新',RefreshCw],['training','训练与快捷操作',Keyboard],['help','数据与帮助',Download],['advanced','高级设置',Settings2]];
  return <div className="settings-page scroll-panel" aria-label="偏好设置"><nav className="settings-subpage-tabs" role="tablist" aria-label="设置分类">{tabs.map(([key,label,Icon])=><Tooltip text={label} key={key}><button role="tab" aria-label={label} aria-selected={tab===key} onClick={()=>onTab(key)}><Icon size={17}/><span>{label}</span></button></Tooltip>)}</nav>
    <div className="settings-column">
      {tab==='appearance'&&<><VisualPreferences prefs={prefs} setPrefs={setPrefs}/><VisualStyleSettings prefs={prefs} setPrefs={setPrefs} onError={onError}/></>}
      {tab==='account'&&<Suspense fallback={<p role="status">正在读取…</p>}><AvatarSettings prefs={prefs} setPrefs={setPrefs} onError={onError}/></Suspense>}
      {tab==='interaction'&&<InteractionSettings prefs={prefs} setPrefs={setPrefs} display={display} onFullscreen={onFullscreen}/>}
      {tab==='navigation'&&<NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs}/>}
      {tab==='advanced'&&<NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs} orderOnly/>}
      {tab==='help'&&<Suspense fallback={<p role="status">正在读取…</p>}><DataHelpSettings api={api} onTutorial={onTutorial} onError={onError}/></Suspense>}
      {tab==='training'&&<><section aria-label="训练与快捷操作"><div className="settings-page-description"><h2>训练与快捷操作</h2><Tooltip text="原站 AC 计入训练统计；样例通过单独保留。取消训练保留代码和历史。复习按 7 天 / 30 天安排。" label="训练规则说明"/></div><div className="settings-command-grid"><Tooltip text="完整键盘操作"><button className="secondary" aria-label="查看键位" onClick={onKeyboard}><Keyboard size={20}/></button></Tooltip>{commands.items.map((command,index)=><Tooltip text={`${command.name}${command.detail?' · '+command.detail:''}`} key={command.name}><button className="secondary" aria-label={command.name} onClick={command.action}><Command size={18}/><span className="settings-command-index">{index+1}</span></button></Tooltip>)}</div></section>
      <section aria-label="已保存筛选"><h2>已保存筛选</h2>{prefs.views?.map(view=><div className="setting-line" key={view.id}><strong>{view.name}</strong><Tooltip text={`删除筛选 ${view.name}`}><button className="icon-button" aria-label={`删除筛选 ${view.name}`} onClick={()=>setPrefs(previous=>({...previous,views:previous.views.filter(item=>item.id!==view.id)}))}><X size={16}/></button></Tooltip></div>)}</section></>}
      {tab==='updates'&&<section className="settings-updates" aria-label="更新设置"><div className="settings-page-description"><h2>更新</h2><Tooltip text="消息通知"><button className="icon-button" aria-label="查看更新通知" onClick={onMessages}><Bell size={18}/></button></Tooltip></div><SoftwareUpdatePanel update={softwareUpdate}/><UpdatePanel softwareState={softwareUpdate.state} showNotifications={false} hub={hub} api={api} onContent={onContent} onChanged={onHubChanged} onError={onError}/></section>}
    </div>
  </div>;
}
