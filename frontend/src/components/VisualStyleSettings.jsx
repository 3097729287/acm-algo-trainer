import { useRef, useState } from 'react';
import { Circle, Grid2X2, Image, ImagePlus, Palette, RotateCcw, Sparkles, Sunset, Trash2 } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
import BoundedNumber from './BoundedNumber.jsx';
import { SettingRow } from './SettingsControls.jsx';

export default function VisualStyleSettings({prefs,setPrefs,onError}) {
  const input=useRef(null),[hasImage,setHasImage]=useState(()=>Boolean(localStorage.getItem('tb.appearance.background')));
  async function selected(event) {
    const file=event.target.files?.[0];if(!file)return;
    try {
      if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>12*1024*1024)throw new Error('请选择 12 MB 以内的 PNG、JPEG 或 WebP 图片');
      const bitmap=await createImageBitmap(file),scale=Math.min(1,1920/Math.max(bitmap.width,bitmap.height)),canvas=document.createElement('canvas');
      canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
      const data=canvas.toDataURL('image/jpeg',.8);localStorage.setItem('tb.appearance.background',data);document.documentElement.style.setProperty('--workspace-image',`url("${data}")`);setHasImage(true);setPrefs(previous=>({...previous,backdrop:'custom'}));
    } catch(error){onError?.(error.message);} finally {event.target.value='';}
  }
  return <section className="appearance-studio" aria-label="工作台风格"><h2><Palette size={18}/>工作台风格</h2>
    <div className="style-preset-grid">{[['minimal','清简','轻盈留白'],['outlined','线框','圆角与轮廓'],['aurora','极光','柔和渐变'],['blueprint','蓝图','网格与虚线']].map(([id,title,hint])=><Tooltip text={hint} key={id}><button className={`style-preset style-${id}`} aria-label={title} aria-pressed={prefs.panelStyle===id} onClick={()=>setPrefs(previous=>({...previous,panelStyle:id}))}><i aria-hidden="true"/><strong>{title}</strong></button></Tooltip>)}</div>
    <SettingRow title="页面背景" hint="选择静态背景。自选图片只保存在本机。"><div className="background-options" role="group" aria-label="页面背景">{[['none','纯色',Circle],['aurora','夜空极光',Sparkles],['grid','细线网格',Grid2X2],['sunset','落日余晖',Sunset],...(hasImage?[['custom','我的图片',Image]]:[])].map(([id,title,Icon])=><Tooltip text={title} key={id}><button className="background-option" aria-label={title} aria-pressed={prefs.backdrop===id} onClick={()=>setPrefs(previous=>({...previous,backdrop:id}))}><Icon size={18}/></button></Tooltip>)}<input ref={input} hidden type="file" accept="image/png,image/jpeg,image/webp" onChange={selected}/><Tooltip text="选择背景图片；PNG、JPEG 或 WebP，最大 12 MB。"><button className="background-option" aria-label="选择背景图片" onClick={()=>input.current.click()}><ImagePlus size={18}/></button></Tooltip>{hasImage&&<Tooltip text="清除本机背景图片"><button className="background-option" aria-label="清除背景图片" onClick={()=>{localStorage.removeItem('tb.appearance.background');document.documentElement.style.removeProperty('--workspace-image');setHasImage(false);setPrefs(previous=>({...previous,backdrop:'none'}));}}><Trash2 size={16}/></button></Tooltip>}</div></SettingRow>
    <SettingRow title="面板不透明度" hint="范围 25–100%；数值越低越透明。"><input type="range" aria-label="面板不透明度" min={25} max={100} value={prefs.panelOpacity??76} onChange={event=>setPrefs(previous=>({...previous,panelOpacity:Number(event.target.value)}))}/><BoundedNumber aria-label="面板不透明度数值" min={25} max={100} unit="%" value={prefs.panelOpacity??76} required onChange={event=>setPrefs(previous=>({...previous,panelOpacity:Number(event.target.value)}))}/></SettingRow>
    <details className="page-opacity-settings"><summary>各界面透明度</summary><div>{[['mine','我的训练'],['library','题库'],['competitions','比赛'],['mock','模拟赛'],['rankings','排行榜'],['growth','成长与能力'],['records','提交记录'],['activity','活动记录'],['lectures','从零讲'],['settings','偏好设置'],['statement','练习题面'],['editor','代码编辑器']].map(([key,label])=><SettingRow title={label} key={key}><BoundedNumber aria-label={`${label}不透明度`} min={0} max={100} value={prefs.pageOpacities?.[key]??prefs.panelOpacity??76} unit="%" required onChange={event=>setPrefs(previous=>({...previous,pageOpacities:{...previous.pageOpacities,[key]:Number(event.target.value)}}))}/><Tooltip text="跟随统一不透明度"><button className="background-option" disabled={prefs.pageOpacities?.[key]==null} aria-label={`${label}跟随统一`} onClick={()=>setPrefs(previous=>{const next={...previous.pageOpacities};delete next[key];return {...previous,pageOpacities:next};})}><RotateCcw size={15}/></button></Tooltip></SettingRow>)}</div></details>
  </section>;
}
