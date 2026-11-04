import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import DuelCommunity from '../src/components/DuelCommunity.jsx';
import AvatarFrame from '../src/components/AvatarFrame.jsx';
import TierIcon from '../src/components/TierIcon.jsx';
import WikiPage from '../src/pages/WikiPage.jsx';
import TemplatesPage from '../src/pages/TemplatesPage.jsx';
import {loadDuelBoard} from '../src/lib/duelBoardCache.js';
import {loadCatalogue} from '../src/lib/catalogueCache.js';
import {trainingDay} from '../src/lib/trainingDate.js';
import '../src/styles/workspace.css';
import '../src/styles/unified.css';
window.__tbAccountUserId='perf-A';
const fixture=window.instant={holdBoard:false,holdWiki:false,holdTemplates:false,pending:[],calls:[]};
const article={id:'ds/dsu',title:'并查集',url:'https://oi-wiki.org/ds/dsu/',category:'数据结构',html:'<h1>正文已经读取</h1><p>正文不需要等待慢目录。</p>'};
const templates={templates:[{id:'own:cached',title:'已经缓存的模板',category:'我的模板',language:'cpp17',code:'int main(){return 0;}',notes:'缓存显示',builtin:false}]};
const board=owner=>({owner,mode:'ranked',date:trainingDay(),entries:[{userId:owner,nickname:owner==='perf-A'?'已确认玩家':'新账号玩家',rank:1,rating:1234,online:true,activity:'problem'}],records:[],next:null});
const api=async path=>{
 const owner=window.__tbAccountUserId;fixture.calls.push(path);
 if(path.startsWith('duel/board')){if(fixture.holdBoard)await new Promise(resolve=>fixture.pending.push(resolve));return board(owner);}
 if(path==='templates'){if(fixture.holdTemplates)await new Promise(resolve=>fixture.pending.push(resolve));return templates;}
 if(path==='wiki'){if(fixture.holdWiki)await new Promise(resolve=>fixture.pending.push(resolve));return {articles:[article]};}
 if(path.startsWith('wiki?id='))return {article};
 throw Error('Unexpected isolated request '+path);
};
fixture.seed=async()=>{await loadDuelBoard(api,'perf-A','ranked');await loadCatalogue(api,'perf-A','templates');};
function Fixture(){
 const [page,setPage]=useState(null),[owner,setOwner]=useState('perf-A');fixture.show=page=>{fixture.started=performance.now();setPage(page);requestAnimationFrame(()=>requestAnimationFrame(()=>{fixture.paint={ms:performance.now()-fixture.started,text:document.querySelector('main')?.innerText||''};}));};fixture.owner=value=>{window.__tbAccountUserId=value;setOwner(value);};fixture.release=()=>fixture.pending.splice(0).forEach(fn=>fn());
 return <main style={{height:'100dvh',overflow:'auto'}}>{page==='board'&&<><div style={{position:'relative',width:180,height:180,margin:30}}><AvatarFrame index={1}/></div><TierIcon badge="tier-1" size={64}/><DuelCommunity api={api} owner={owner} mode="ranked" revision={0}/></>}{page==='wiki'&&<WikiPage api={api} initialArticle="ds/dsu"/>}{page==='templates'&&<TemplatesPage api={api}/>}</main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
