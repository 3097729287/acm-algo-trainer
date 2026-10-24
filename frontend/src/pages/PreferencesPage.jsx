import ShortcutSettings from './ShortcutSettings.jsx';
import { ArrowLeft, Heart, ShieldCheck, Command, Download, Keyboard, Layers, Palette, RefreshCw, Settings2, SlidersHorizontal, UserRound, X } from 'lucide-react';
import { lazy, Suspense, useLayoutEffect, useRef } from 'react';
import SettingsScene from '@/components/SettingsScene.jsx';
import AdminSettings from './AdminSettings.jsx';
import { GrowthAccountPanel } from './ProgressPanels.jsx';
import VisualStyleSettings from '../components/VisualStyleSettings.jsx';
import { InteractionSettings, VisualPreferences } from '../components/SettingsControls.jsx';
import Tooltip from '../components/Tooltip.jsx';
import NavigationSettings from './NavigationSettings.jsx';
import { SoftwareUpdatePanel } from './SoftwareUpdates.jsx';
import { TranslationSettings, UpdatePanel } from './ProgressPanels.jsx';
const DataHelpSettings=lazy(()=>import('./DataHelpSettings.jsx'));


export default function PreferencesPage({insights,onTrain,rows,tab,onTab,prefs,setPrefs,display,onFullscreen,api,softwareUpdate,hub,account,accountFocus,profileSnapshot,onProfileChanged,onRefresh,onHubChanged,onError,onContent,onMessages,onTutorial,onKeyboard,commands}) {
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
  const tabs=[['appearance','外观',Palette],['interaction','交互与导航',SlidersHorizontal],['updates','更新',RefreshCw],['training','快捷键',Keyboard],['help','数据统计',Download],['advanced','翻译 API',Settings2],['accounts','账号与身份',UserRound],['thanks','鸣谢',Heart],...(window.__tbAdmin?[['admin','管理员',ShieldCheck]]:[])];
  return <div ref={panel} onScroll={savePosition} className="settings-page scroll-panel" aria-label="设置">{tab!=='home'&&<div className="settings-subpage-controls"><button type="button" className="icon-button settings-return-button" aria-label="返回设置首页" title="返回设置首页 · Esc" onClick={()=>onTab('home')}><ArrowLeft size={19}/></button></div>}<nav className={"settings-subpage-tabs " + (tab==='home'?'settings-home-grid':'settings-hidden-nav')} role="tablist" aria-label="设置分类">{tabs.map(([key,label,Icon])=><span className="settings-tile" data-section={key} key={key}><button role="tab" aria-label={label} aria-selected={tab===key} onClick={()=>onTab(key)}><Icon size={17}/><span>{label}</span><SettingsScene kind={{appearance:'dino',interaction:'globe',updates:'balloon',training:'cloud',help:'coffee',advanced:'orbit',accounts:'bulb',thanks:'stars',admin:'compass'}[key]}/></button></span>)}</nav>
    <div className="settings-column">
      {tab==='thanks'&&<section className="acknowledgements" aria-label="鸣谢"><h2>鸣谢</h2><div className="special-thanks-list"><section className="special-thanks" aria-label="特别鸣谢猫猫头教主"><h3>特别鸣谢</h3><p className="special-thanks-name special-thanks-cat">猫猫头教主</p><div>感谢提供的专业性知识以及大量必要建议</div></section><section className="special-thanks" aria-label="特别鸣谢 LT"><h3>特别鸣谢</h3><p className="special-thanks-name special-thanks-lt">LT</p><div>感谢给予的资金支持以及信任</div></section></div><div className="thanks-contributors">{['InkStarry','蒟蒻','她不爱吃酸','jiahao27','NiuXyn'].map(name=><p key={name}>{name}</p>)}</div></section>}
      {tab==='accounts'&&<GrowthAccountPanel accountFocus={accountFocus} api={api} hub={hub} account={account} profileSnapshot={profileSnapshot} onProfileChanged={onProfileChanged} onHubChanged={onHubChanged} onError={onError}/>}
      {tab==='admin'&&window.__tbAdmin&&<AdminSettings api={api} onChanged={onRefresh} onError={onError}/>}
      {tab==='appearance'&&<><VisualPreferences prefs={prefs} setPrefs={setPrefs}/><VisualStyleSettings prefs={prefs} setPrefs={setPrefs} onError={onError}/></>}
      {tab==='interaction'&&<><InteractionSettings prefs={prefs} setPrefs={setPrefs} display={display} onFullscreen={onFullscreen}/><NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs}/></>}
      {tab==='navigation'&&<NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs}/>}
      {tab==='advanced'&&<section className="settings-translation-panel"><TranslationSettings api={api} onError={onError}/></section>}
      {tab==='help'&&<Suspense fallback={<p role="status">正在读取…</p>}><DataHelpSettings api={api} rows={rows} insights={insights} account={account} onTrain={onTrain} onTutorial={onTutorial} onError={onError}/></Suspense>}
      {tab==='training'&&<ShortcutSettings prefs={prefs} setPrefs={setPrefs}/>}
      {tab==='updates'&&<><SoftwareUpdatePanel update={softwareUpdate}/><UpdatePanel softwareState={softwareUpdate.state} showNotifications={false} hub={hub} api={api} onContent={onContent} onChanged={onHubChanged} onError={onError}/></>}
    </div>
  </div>;
}
