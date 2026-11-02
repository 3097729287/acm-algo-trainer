import {prepareStickerAudio} from '../src/lib/stickerSound.js';
import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-1434.css';
const catalogue=['duck','semicolon','rainbow','envelope','orbit','gem','crown','galaxy','phoenix','cloud','leaf'].map((shape,i)=>({id:'art-'+shape,shape,title:shape,rarity:i<9?'legendary':'common'}));
const units=catalogue.map((item,i)=>({id:'unit-'+item.shape,stickerId:item.id,revision:0,placement:{x:.12+(i%4)*.24,y:.18+Math.floor(i/4)*.3,angle:0,scale:1}}));
let inventory={owner:'fixture-a',revision:1,catalogue,units,placementPolicy:{scale:true}};
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function Fixture(){
 const [owner,setOwner]=useState('fixture-a');
 window.stickerFeedbackFixture={switchOwner:()=>{inventory={...inventory,owner:'fixture-b',units:[]};setOwner('fixture-b');},audioReady:()=>prepareStickerAudio(),state:()=>inventory};
 async function api(path,body){if(path==='stickers'){await wait(1400);return structuredClone(inventory);}if(path==='stickers/place'){const unit=inventory.units.find(item=>item.id===body.unitId);unit.placement={x:body.x,y:body.y,angle:body.angle,...body.scale===undefined?{}:{scale:body.scale}};unit.revision++;inventory.revision++;return structuredClone(inventory);}throw new Error('Unexpected isolated request '+path);}
 return <main className="growth-account-hero" style={{maxWidth:1000,margin:'40px auto'}}><StickerCanvas api={api} owner={owner}><div style={{height:420,pointerEvents:'none'}}/></StickerCanvas></main>;
}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<Fixture/>);
