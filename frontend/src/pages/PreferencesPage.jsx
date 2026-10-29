import ShortcutSettings from './ShortcutSettings.jsx';
import { ArrowLeft, Code2, GraduationCap, Heart, ShieldCheck, Command, Download, Keyboard, Layers, Palette, RefreshCw, Settings2, SlidersHorizontal, UserRound, X } from 'lucide-react';
import { lazy, Suspense, useLayoutEffect, useRef } from 'react';
import SettingsScene from '@/components/SettingsScene.jsx';
import AdminSettings from './AdminSettings.jsx';
import InitialCodeSettings from './InitialCodeSettings.jsx';
import VisualStyleSettings from '../components/VisualStyleSettings.jsx';
import { InteractionSettings, VisualPreferences } from '../components/SettingsControls.jsx';
import Tooltip from '../components/Tooltip.jsx';
import NavigationSettings from './NavigationSettings.jsx';
import { SoftwareUpdatePanel } from './SoftwareUpdates.jsx';
import { TranslationSettings, UpdatePanel } from './ProgressPanels.jsx';
import { GUIDE_LABELS, PAGE_GUIDES } from '@/lib/guideCatalog.js';
const DataHelpSettings=lazy(()=>import('./DataHelpSettings.jsx'));


export default function PreferencesPage({availablePages,level,insights,onTrain,rows,tab,onTab,prefs,setPrefs,display,onFullscreen,api,softwareUpdate,hub,account,accountFocus,profileSnapshot,onProfileChanged,onRefresh,onHubChanged,onError,onContent,onMessages,onTutorial,onKeyboard,commands}) {
  const panel=useRef(null),restoring=useRef(false);
  const locationKey=`tb.settings.location.${window.__tbAccount?.userId || window.__tbAccount?.loginId || 'local'}`;
  const positions=useRef((()=>{try{return {appearance:JSON.parse(sessionStorage.getItem(locationKey)||'{}').scroll?.appearance||0};}catch{return {};}})());
  const savePosition=()=>{if(restoring.current||!panel.current||tab!=='appearance')return;positions.current.appearance=panel.current.scrollTop;try{sessionStorage.setItem(locationKey,JSON.stringify({tab:'appearance',scroll:positions.current}));}catch{}};
  useLayoutEffect(()=>{
    const element=panel.current,target=tab==='appearance'?positions.current.appearance||0:0;restoring.current=true;
    const restore=()=>{element.scrollTop=target;};restore();
    const observer=new ResizeObserver(restore);Array.from(element.children).forEach(child=>observer.observe(child));
    const timer=setTimeout(()=>{restore();observer.disconnect();restoring.current=false;},250);
    try{sessionStorage.setItem(locationKey,JSON.stringify({tab:tab==='appearance'?'appearance':'home',scroll:positions.current}));}catch{}
    return()=>{clearTimeout(timer);observer.disconnect();restoring.current=false;};
  },[tab]);
  const tabs=[['appearance','外观',Palette],['interaction','交互与导航',SlidersHorizontal],['updates','更新',RefreshCw],['training','快捷键',Keyboard],['help','数据统计',Download],['advanced','翻译 API',Settings2],['accounts','初始代码模板',Command],['thanks','鸣谢',Heart],['guide','新手指引',GraduationCap],...(window.__tbAdmin?[['admin','管理员',ShieldCheck]]:[])];
  const guideIcons={...Object.fromEntries(commands.pages.map(({id,icon})=>[id,icon])),...Object.fromEntries(tabs.map(([key,,Icon])=>['settings:'+key,Icon])),practice:Code2,settings:Settings2,'settings:animation':Layers};
  return <div ref={panel} onScroll={savePosition} className="settings-page scroll-panel" aria-label="设置">{tab!=='home'&&<div className="settings-subpage-controls"><button type="button" className="icon-button settings-return-button" aria-label="返回设置首页" title="返回设置首页 · Esc" onClick={()=>onTab('home')}><ArrowLeft size={19}/></button></div>}<nav className={"settings-subpage-tabs " + (tab==='home'?'settings-home-grid':'settings-hidden-nav')} role="tablist" aria-label="设置分类">{tabs.map(([key,label,Icon])=><span className="settings-tile" data-section={key} key={key}><button role="tab" aria-label={label} aria-selected={tab===key} onClick={()=>onTab(key)}><Icon size={17}/><span>{label}</span><SettingsScene kind={{appearance:'dino',interaction:'globe',updates:'balloon',training:'cloud',help:'coffee',advanced:'orbit',accounts:'bulb',thanks:'stars',guide:'compass',admin:'compass'}[key]}/></button></span>)}</nav>
    <div className="settings-column">
      {tab==='thanks'&&<section className="acknowledgements" aria-label="鸣谢"><h2>鸣谢</h2><div className="special-thanks-list"><section className="special-thanks" aria-label="特别鸣谢猫猫头教主"><h3>特别鸣谢</h3><p className="special-thanks-name special-thanks-cat">猫猫头教主</p><div>感谢提供的专业性知识以及大量必要建议</div></section><section className="special-thanks" aria-label="特别鸣谢 LT"><h3>特别鸣谢</h3><p className="special-thanks-name special-thanks-lt">LT</p><div>感谢给予的资金支持以及信任</div></section></div><div className="thanks-contributors">{['InkStarry','蒟蒻','她不爱吃酸','jiahao27','NiuXyn'].map(name=><p key={name}>{name}</p>)}</div></section>}
      {tab==='accounts'&&<InitialCodeSettings api={api} shortcuts={prefs.shortcuts}/>}
      {tab==='admin'&&window.__tbAdmin&&<AdminSettings api={api} onChanged={onRefresh} onError={onError}/>}
      {tab==='appearance'&&<><VisualPreferences prefs={prefs} setPrefs={setPrefs}/><VisualStyleSettings prefs={prefs} setPrefs={setPrefs} onError={onError}/></>}
      {tab==='interaction'&&<><InteractionSettings prefs={prefs} setPrefs={setPrefs} display={display} onFullscreen={onFullscreen}/><NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs} level={level}/></>}
      {tab==='navigation'&&<NavigationSettings pages={commands.pages} prefs={prefs} setPrefs={setPrefs} level={level}/>}
      {tab==='advanced'&&<section className="settings-translation-panel"><TranslationSettings api={api} onError={onError}/></section>}
      {tab==='help'&&<Suspense fallback={<p role="status">正在读取…</p>}><DataHelpSettings api={api} rows={rows} insights={insights} account={account} onTrain={onTrain} onTutorial={onTutorial} onError={onError}/></Suspense>}
      {tab==='guide'&&<section className="settings-guide" aria-label="新手指引"><h2><GraduationCap size={19}/>新手指引</h2><button type="button" className="tour-overview-button" aria-label="入门总览" onClick={()=>onTutorial('overview')}><GraduationCap size={22} aria-hidden="true"/><span className="guide-entry-copy"><strong>入门总览</strong><small>从连接账号、选题到运行与原站提交</small></span></button><h3>各页指引</h3><div className="tour-guide-grid">{Object.entries(GUIDE_LABELS).filter(([id])=>!availablePages||id==='practice'||id.startsWith('settings:')||availablePages.includes(id)).map(([id,label])=>{const Icon=guideIcons[id];return <button type="button" key={id} aria-label={label} disabled={!PAGE_GUIDES[id]?.length} onClick={()=>onTutorial(id)}>{Icon&&<Icon size={22} aria-hidden="true"/>}<span className="guide-entry-copy"><strong>{label}</strong><small>{PAGE_GUIDES[id]?.length||0} 项操作说明</small></span></button>;})}</div></section>}
      {tab==='training' &&<ShortcutSettings prefs={prefs} setPrefs={setPrefs}/>}
      {tab==='updates'&&<><SoftwareUpdatePanel update={softwareUpdate}/><UpdatePanel softwareState={softwareUpdate.state} showNotifications={false} hub={hub} api={api} onContent={onContent} onChanged={onHubChanged} onError={onError}/></>}
    </div>
  </div>;
}
