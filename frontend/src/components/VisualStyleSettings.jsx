import BackgroundPlaylist, {addBackgroundFiles,clearBackgrounds} from './BackgroundPlaylist.jsx';
import { useRef, useState } from 'react';
import { Circle, Grid2X2, Image, ImagePlus, Palette, RotateCcw, Sparkles, Sunset, Trash2 } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
import BoundedNumber from './BoundedNumber.jsx';
import { SettingRow } from './SettingsControls.jsx';
import SettingsCategories from './SettingsCategories.jsx';
import {OPACITY_GROUPS,surfaceOpacityValue} from '@/lib/surfaceOpacity.js';

export default function VisualStyleSettings({prefs,setPrefs,onError}) {
  const input=useRef(null),[hasImage,setHasImage]=useState(()=>Boolean(localStorage.getItem('tb.appearance.background'))),[opacityGroup,setOpacityGroup]=useState('');
  async function selected(event) {
    const file=event.target.files?.[0];if(!file)return;
    try {
      await addBackgroundFiles([file]);setHasImage(true);setPrefs(previous=>({...previous,backdrop:'custom'}));
    } catch(error){onError?.(error.message);} finally {event.target.value='';}
  }
  return <section className="appearance-studio" aria-label="工作台风格"><h2><Palette size={18}/>工作台风格</h2>
    <div className="style-preset-grid">{[['minimal','清简','轻盈留白'],['outlined','线框','圆角与轮廓'],['aurora','极光','柔和渐变'],['blueprint','蓝图','网格与虚线']].map(([id,title,hint])=><Tooltip text={hint} key={id}><button className={`style-preset style-${id}`} aria-label={title} aria-pressed={prefs.panelStyle===id} onClick={()=>setPrefs(previous=>({...previous,panelStyle:id}))}><i aria-hidden="true"/><strong>{title}</strong></button></Tooltip>)}</div>
    <SettingRow title="页面背景" hint="支持静态背景、动图和定时轮播；自选图片只保存在本机。"><div className="background-options" role="group" aria-label="页面背景">{[['none','纯色',Circle],['aurora','夜空极光',Sparkles],['grid','细线网格',Grid2X2],['sunset','落日余晖',Sunset],['custom','我的背景',Image]].map(([id,title,Icon])=><Tooltip text={title} key={id}><button className="background-option" aria-label={title} aria-pressed={prefs.backdrop===id} onClick={()=>setPrefs(previous=>({...previous,backdrop:id}))}><Icon size={18}/></button></Tooltip>)}<input ref={input} hidden type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={selected}/><Tooltip text="选择背景图片；PNG、JPEG、WebP 或 GIF，最大 12 MB。"><button className="background-option" aria-label="选择背景图片" onClick={()=>input.current.click()}><ImagePlus size={18}/></button></Tooltip>{hasImage&&<Tooltip text="清除本机背景图片"><button className="background-option" aria-label="清除背景图片" onClick={async()=>{try{await clearBackgrounds();setHasImage(false);setPrefs(previous=>({...previous,backdrop:'none'}));}catch(error){onError?.(error.message);}}}><Trash2 size={16}/></button></Tooltip>}</div></SettingRow>
    <BackgroundPlaylist setPrefs={setPrefs} onError={onError}/>
    <SettingRow title="面板不透明度" hint="范围 0–100%；数值越低越透明。"><input type="range" aria-label="面板不透明度" min={0} max={100} value={prefs.panelOpacity??76} onChange={event=>setPrefs(previous=>({...previous,panelOpacity:Number(event.target.value)}))}/><BoundedNumber aria-label="面板不透明度数值" min={0} max={100} unit="%" value={prefs.panelOpacity??76} required onChange={event=>setPrefs(previous=>({...previous,panelOpacity:Number(event.target.value)}))}/></SettingRow>
    <div className="page-opacity-settings"><header><h3>各界面透明度</h3><Tooltip text="重置所有透明度"><button type="button" className="icon-button" aria-label="重置所有透明度" onClick={()=>setPrefs(previous=>({...previous,panelOpacity:76,pageOpacities:{}}))}><RotateCcw size={17}/></button></Tooltip></header><SettingsCategories groups={OPACITY_GROUPS} selected={opacityGroup} onSelect={setOpacityGroup} label="透明度板块">{group=>group.items.map(([key,label])=><SettingRow title={label} key={key}><input type="range" aria-label={`${label}不透明度滑块`} min={0} max={100} value={surfaceOpacityValue(prefs,key)} onChange={event=>setPrefs(previous=>({...previous,pageOpacities:{...previous.pageOpacities,[key]:Number(event.target.value)}}))}/><BoundedNumber aria-label={`${label}不透明度`} min={0} max={100} value={surfaceOpacityValue(prefs,key)} unit="%" required onChange={event=>setPrefs(previous=>({...previous,pageOpacities:{...previous.pageOpacities,[key]:Number(event.target.value)}}))}/><Tooltip text="跟随统一不透明度"><button type="button" className="background-option" disabled={prefs.pageOpacities?.[key]==null} aria-label={`${label}跟随统一`} onClick={()=>setPrefs(previous=>{const next={...previous.pageOpacities};delete next[key];return {...previous,pageOpacities:next};})}><RotateCcw size={15}/></button></Tooltip></SettingRow>)}</SettingsCategories></div>
  </section>;
}
