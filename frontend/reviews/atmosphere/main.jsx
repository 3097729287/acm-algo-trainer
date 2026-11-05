import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {catalogue,approval,inputSha256} from 'virtual:material-review';
import {StickerArt,STICKER_NAMES} from '../../src/components/StickerArt.jsx';
import BackgroundArt from '../../src/components/BackgroundArt.jsx';
import StickerReaction,{useStickerReaction} from '../../src/components/StickerReaction.jsx';
import {STICKER_FEEDBACK} from '../../src/lib/stickerFeedbackCatalog.js';
import '../../src/components/StickerCanvas.css';
import './review.css';

const backgrounds=catalogue.filter(item=>item.kind==='background'),stickers=catalogue.filter(item=>item.kind!=='background');
const prior=new Map(approval.items.map(item=>[item.id,item]));
const details={night:'蓝灰夜色、暮紫地平线与少量星光。',morning:'清冷蓝天融入浅杏色晨雾，地面渐入灰绿。',rain:'冷灰雨幕与湿润青绿，远处被细雾轻轻融开。',coast:'青蓝海面、雾化海平线与更宽的浅色岸滩。',beach:'粉紫天空与暖杏沙地，温柔海湾从画面一侧延伸。',desert:'藕灰天空、暖金薄雾与舒缓起伏的玫瑰沙丘。',rainforest:'深浅绿层层过渡，以雾和林冠表现雨林纵深。',mountains:'青灰山脉在暖色远光里逐层淡去，没有规则尖峰。',snow:'灰蓝雪影、柔和雪脊与淡桃色天光。',river:'午后暖雾、灰绿河岸与向前景展开的清蓝河面。',sky:'蓝色高空、粉白云海与低处的暖色反光。',underground:'青碧幽光、柔化洞壁与漂浮微尘；点击洞顶会落下碎屑。',room:'暖木色室内与冷色窗景；点击窗户开合，打开后窗帘轻动。',galaxy:'身在银河星带之中：星云缓慢流动，远近星光轻闪，偶有流星；点击空白处可短暂穿行。'};
function readSaved(){try{return JSON.parse(localStorage.getItem('tobe-material-review-atmosphere-v2')||'{}');}catch{return {};}}
function App(){
 const [kind,setKind]=useState('background'),[selected,setSelected]=useState('background-galaxy-legendary'),[demo,setDemo]=useState(0),[reviews,setReviews]=useState(readSaved),[saved,setSaved]=useState(false),[light,setLight]=useState(false);
 const [reaction,react]=useStickerReaction('offline-material-review-v2');
 const items=kind==='background'?backgrounds:stickers,item=catalogue.find(item=>item.id===selected)||items[0],feedback=STICKER_FEEDBACK[item.shape],old=prior.get(item.id),edit=reviews[item.id]||{},reviewed=Object.values(reviews).filter(value=>value.approved).length;
 const update=changes=>setReviews(previous=>{const next={...previous,[item.id]:{...previous[item.id],...changes}};try{localStorage.setItem('tobe-material-review-atmosphere-v2',JSON.stringify(next));}catch{}return next;});
 const choose=next=>{setSelected(next.id);setDemo(0);};
 function exportReview(){const value={schema:'tobe-material-review-atmosphere-v2',sourceVersion:'1.6.1',exportedAt:new Date().toISOString(),appliedInputSha256:inputSha256,catalogueCount:{stickers:stickers.length,backgrounds:backgrounds.length},duckSound:{status:'applied',keepCall:1,keepSourceIndex:0,removeOtherCall:true},items:catalogue.map(entry=>({id:entry.id,title:entry.title,kind:entry.kind||'sticker',shape:entry.shape,rarity:entry.rarity,...(reviews[entry.id]||{})}))};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));a.download='ToBe-背景重制审批结果.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);setSaved(true);}
 return <main className={light?'material-review light':'material-review'}>
  <header className="review-header"><a className="review-brand" href="#">ToBe<span>素材工作室</span></a><div className="review-top-actions"><button onClick={()=>setLight(value=>!value)}>{light?'深色查看':'浅色查看'}</button><button className="review-primary" onClick={exportReview}>导出意见{saved?' ✓':''}</button></div></header>
  <section className="review-intro"><div className="review-kicker">色彩 / 空气 / 光</div><h1>让背景有自己的氛围。</h1><p>14 个独立背景，每个主题一种稀有度。天空与地面重新调色，太阳与月亮已移除。</p><div className="review-counts"><span>14 个背景</span><span>62 张贴纸</span><span>小黄鸭保留第 1 段原声</span><span>{reviewed} 项已确认</span></div></section>
  <section className="review-workbench">
   <div className={'review-stage '+(item.kind==='background'?'background-stage':'sticker-stage')}>
    {item.kind==='background'?<BackgroundArt key={item.id} item={item} demo={demo}/>:<button type="button" className={'review-sticker placed-sticker'+(reaction?.unitId===item.id?' legendary-reacting':'')} aria-label={'演示 '+item.title} onClick={()=>react({id:item.id},item)}><StickerArt item={item} size="100%"/>{reaction?.unitId===item.id&&<StickerReaction reaction={reaction}/>}</button>}
    <div className="stage-label">{item.title}<span>{STICKER_NAMES[item.rarity]}</span></div>
   </div>
   <aside className="review-inspector"><div className="review-eyebrow">{item.kind==='background'?'背景':'贴纸'} / {STICKER_NAMES[item.rarity]}</div><h2>{item.title}</h2><p>{item.kind==='background'?details[item.theme]:feedback?.animation||feedback?.sound||'查看修订后的图案与边缘。'}</p>
    {old?.notes&&<blockquote><span>你的原意见</span>{old.notes}</blockquote>}
    <div className="inspector-actions">{item.kind==='background'&&['room','underground','galaxy'].includes(item.theme)?<button onClick={()=>setDemo(value=>value+1)}>演示互动</button>:feedback&&<button onClick={()=>react({id:item.id},item)}>{item.rarity==='legendary'?'声音与动画':'试听声音'}</button>}<button className={edit.approved?'approved':''} aria-pressed={!!edit.approved} onClick={()=>update({approved:!edit.approved})}>{edit.approved?'已确认 ✓':'确认此项'}</button></div>
    <label>稀有度<select aria-label="建议稀有度" value={edit.requestedRarity||item.rarity} onChange={event=>update({requestedRarity:event.target.value})}>{Object.entries(STICKER_NAMES).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
    <label>还想怎么调整<textarea aria-label="修改意见" value={edit.notes||''} onChange={event=>update({notes:event.target.value})} placeholder="色调、层次或动画节奏…"/></label><small>意见保存在本机；导出后可继续修改。</small>
   </aside>
  </section>
  <nav className="review-kind-tabs" aria-label="素材类别"><button aria-pressed={kind==='background'} onClick={()=>{setKind('background');choose(backgrounds.find(item=>item.theme==='galaxy'));}}>背景 <span>14</span></button><button aria-pressed={kind==='sticker'} onClick={()=>{setKind('sticker');choose(stickers[0]);}}>贴纸 <span>62</span></button></nav>
  <section className="review-gallery" aria-label={kind==='background'?'14 个背景':'62 张贴纸'}>{[...items].sort((a,b)=>(b.theme==='galaxy')-(a.theme==='galaxy')).map(entry=><button className={'review-card'+(entry.id===item.id?' selected':'')} key={entry.id} aria-label={'查看 '+entry.title} aria-pressed={entry.id===item.id} onClick={()=>choose(entry)}><div className={'review-card-art '+(kind==='sticker'?'small-sticker':'')}>{entry.kind==='background'?<BackgroundArt item={entry} thumbnail/>:<StickerArt item={entry} size="100%"/>}</div><div className="review-card-label"><strong>{entry.title}</strong><span data-rarity={entry.rarity}>{STICKER_NAMES[entry.rarity]}</span>{reviews[entry.id]?.approved&&<i>✓</i>}</div></button>)}</section>
  <footer className="review-footer">ToBe · 背景与贴纸修订 / 2026.11.05</footer>
 </main>;
}
createRoot(document.getElementById('root')).render(<App/>);
