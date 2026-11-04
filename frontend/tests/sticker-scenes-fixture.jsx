import React,{useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import {CommentDialog} from '../src/components/Social.jsx';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';

const calls=[];let held=null,delayApply=false;
function Fixture(){
 const [owner,setOwner]=useState(window.sceneFixtureData.a),[comment,setComment]=useState(false),[lastMessage,setLastMessage]=useState(null);
 window.__tbAccountUserId=owner;
 const api=useMemo(()=>async(path,body)=>{calls.push({owner,path,body});const answer=await window.sceneFixtureCall(owner,path,body);if(path==='stickers/scene-apply'&&delayApply){delayApply=false;await new Promise(resolve=>held=resolve);}if(answer.status>=400)throw Object.assign(Error(answer.value.error?.message||answer.value.error||answer.value.message||'Scene fixture request failed'),{status:answer.status});return answer.value.inventory?{...answer.value.inventory,...(answer.value.scene?{scene:answer.value.scene}:{}),...(answer.value.opening?{opening:answer.value.opening}:{})}:answer.value;},[owner]);
 window.sceneFixture={calls,owner:setOwner,delay:()=>delayApply=true,release:()=>{held?.();held=null;},refresh:()=>window.dispatchEvent(new Event('tb:sticker-rewards'))};
 return <><div className="growth-dashboard" style={{height:850,padding:20}}><section className="growth-account-hero" style={{height:'100%',padding:16}}><StickerCanvas api={api} owner={owner}><div style={{height:700}}/></StickerCanvas></section></div><button type="button" onClick={()=>setComment(true)}>给朋友赠送</button>{comment&&<CommentDialog target={{userId:window.sceneFixtureData.b,nickname:'朋友'}} api={api} onClose={()=>setComment(false)} onSent={setLastMessage}/>}<output>{lastMessage?.text}</output></>;
}
document.documentElement.dataset.theme='dark';
const footer=document.createElement('footer');footer.className='app-statusbar';footer.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:20';document.body.append(footer);
createRoot(document.getElementById('root')).render(<Fixture/>);
