import React from 'react';
import {createRoot} from 'react-dom/client';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import {BACKGROUND_THEMES} from '../src/lib/stickerPolicy.js';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-160.css';
const owner='10000000-0000-4000-8000-000000000091';window.__tbAccountUserId=owner;
const catalogue=BACKGROUND_THEMES.filter(theme=>theme.id!=='galaxy').flatMap(theme=>['common','rare','epic','legendary'].map(rarity=>({id:`background-${theme.id}-${rarity}`,theme:theme.id,title:theme.title,shape:'background-'+theme.id,rarity,kind:'background'})));
const raw={owner,revision:1,catalogue,capabilities:{scenes:true,backgrounds:true},units:catalogue.map((item,index)=>({id:'legacy-unit-'+index,stickerId:item.id,revision:0,placement:item.id==='background-room-rare'?{x:.5,y:.5,angle:0,scale:1}:null}))};
const writes=[];window.atmosphereFixture={raw,writes};
async function api(path,body){
 if(path==='stickers')return structuredClone(raw);
 if(path==='stickers/place'){const unit=raw.units.find(unit=>unit.id===body.unitId);if(!unit||unit.revision!==body.revision)throw new Error('Unknown or stale owner unit');writes.push(body);for(const other of raw.units)if(other.id!==unit.id&&other.placement){other.placement=null;other.revision++;}unit.placement={x:.5,y:.5,angle:0,scale:1};unit.revision++;raw.revision++;return structuredClone(raw);}
 throw new Error('Unexpected isolated API '+path);
}
document.documentElement.dataset.theme='dark';document.body.style.margin=0;
createRoot(document.getElementById('root')).render(<main style={{height:'900px',padding:24}}><section className="growth-account-hero" style={{height:'800px'}}><StickerCanvas api={api} owner={owner}><div style={{height:700,pointerEvents:'none'}}/></StickerCanvas></section></main>);
