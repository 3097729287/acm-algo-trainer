import { Bell, Command, Download, Keyboard, Layers, Palette, RefreshCw, Settings2, SlidersHorizontal, UserRound, X } from 'lucide-react';
import { lazy, Suspense, useLayoutEffect, useRef } from 'react';
import VisualStyleSettings from '../components/VisualStyleSettings.jsx';
import { InteractionSettings, VisualPreferences } from '../components/SettingsControls.jsx';
import Tooltip from '../components/Tooltip.jsx';
import NavigationSettings from './NavigationSettings.jsx';
import { SoftwareUpdatePanel } from './SoftwareUpdates.jsx';
import { TranslationSettings, UpdatePanel } from './ProgressPanels.jsx';
const DataHelpSettings=lazy(()=>import('./DataHelpSettings.jsx'));


export default function PreferencesPage({tab,onTab,prefs,setPrefs,display,onFullscreen,api,softwareUpdate,hub,onHubChanged,onError,onContent,onMessages,onTutorial,onKeyboard,commands}) {
  const panel=useRef(null),restoring=useRef(false);
  const locationKey=`tb.settings.location.${window.__tbAccount?.userId || window.__tbAccount?.loginId || 'local'}`;
  const positions=useRef((()=>{try{return JSON.parse(sessionStorage.getItem(locationKey)||'{}').scroll || {};}catch{return {};}})());
  const savePosition=()=>{if(restoring.current||!panel.current)return;positions.current[tab]=panel.current.scrollTop;try{sessionStorage.setItem(locationKey,JSON.stringify({tab,scroll:positions.current}));}catch{}};
  useLayoutEffect(()=>{
    const element=panel.current,target=positions.current[tab] || 0;restoring.current=true;
    const restore=()=>{element.scrollTop=target;};restore();
    const observer=new ResizeObserver(restore);Array.from(element.children).forEach(child=>observer.observe(child));
    const timer=setTimeout(()=>{restore();observer.disconnect();restoring.current=false;},250);
    try{sessionStorage.setItem(locationKey,JSON.stringify({tab,scroll:positions.current}));}catch{}
    return()=>{clearTimeout(timer);observer.disconnect();restoring.current=false;};
  },[tab]);
  const tabs=[['appearance','外观',Palette],['interaction','交互与导航',SlidersHorizontal],['updates','更新',RefreshCw],['training','训练与筛选',Keyboard],['help','数据与帮助',Download],['advanced','翻译 API',Settings2]];
  return <div ref={panel} onScroll={savePosition} className="settings-page scroll-panel" aria-label="设置">{tab !== 'home' && <button className="settings-back" onClick={()=>onTab('home')}>← 全部设置</button>}<nav className={"settings-subpage-tabs " + (tab==='home'?'settings-home-grid':'settings-hidden-nav')} role="tablist" aria-label="设置分类">{tabs.map(([key,label,Icon])=><Tooltip text={label} key={key}><button role="tab" aria-label={label} aria-selected={tab===key} onClick={()=>onTab(key)}><Icon size={17}/><span>{label}</span></button></Tooltip>)}</nav>
    {tab==='home'&&<div className="acknowledgements"><span>鸣谢</span><strong>InkStarry</strong><strong>猫猫头教主</strong><strong>蒟蒻</strong><strong>她不爱吃酸</strong></div>}<div className="settings-column">
      {tab==='appearance'&&<><VisualPreferences prefs={prefs} setPrefs={setPrefs}/><VisualStyleSettings prefs={prefs} setPrefs={setPrefs} onError={onError}/></>}
      {tab==='interaction'&&<><InteractionSettings prefs={prefs} setPrefs={setPrefs} display={display} onFullscreen={onFullscreen}/><NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs}/><NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs} orderOnly/></>}
      {tab==='navigation'&&<NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs}/>}
      {tab==='advanced'&&<TranslationSettings api={api} onError={onError}/>}
      {tab==='help'&&<Suspense fallback={<p role="status">正在读取…</p>}><DataHelpSettings api={api} onTutorial={onTutorial} onError={onError}/></Suspense>}
      {tab==='training'&&<><section aria-label="训练与筛选"><div className="settings-page-description"><h2>训练与筛选</h2><Tooltip text="原站 AC 计入训练统计；样例通过单独保留。取消训练保留代码和历史。复习按 7 天 / 30 天安排。" label="训练规则说明"/></div></section>
      <section aria-label="已保存筛选"><h2>已保存筛选</h2>{prefs.views?.map(view=><div className="setting-line" key={view.id}><strong>{view.name}</strong><Tooltip text={`删除筛选 ${view.name}`}><button className="icon-button" aria-label={`删除筛选 ${view.name}`} onClick={()=>setPrefs(previous=>({...previous,views:previous.views.filter(item=>item.id!==view.id)}))}><X size={16}/></button></Tooltip></div>)}</section></>}
      {tab==='updates'&&<section className="settings-updates" aria-label="更新设置"><div className="settings-page-description"><h2>更新</h2><Tooltip text="消息通知"><button className="icon-button" aria-label="查看更新通知" onClick={onMessages}><Bell size={18}/></button></Tooltip></div><SoftwareUpdatePanel update={softwareUpdate}/><UpdatePanel softwareState={softwareUpdate.state} showNotifications={false} hub={hub} api={api} onContent={onContent} onChanged={onHubChanged} onError={onError}/></section>}
    </div>
  </div>;
}
