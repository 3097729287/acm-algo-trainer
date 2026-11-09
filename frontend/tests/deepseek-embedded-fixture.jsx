import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {EditorView} from '@codemirror/view';
import Workbench from '../src/app/Workbench.jsx';
import {StudyPaneContext} from '../src/lib/StudyPane.jsx';
import 'katex/dist/katex.min.css';
const style=document.createElement('style');style.textContent=':root{font-family:Segoe UI,sans-serif;--panel:#fff;--panel-2:#f7f8fa;--text:#262b38;--muted:#657087;--line:#dfe4eb;--accent:#137e6c;--accent-soft:#137e6c14;--success:#137e6c;--danger:#be394c}*{box-sizing:border-box}body{margin:0}#root{height:100vh}.fixture{height:100%}';document.head.append(style);
window.__tbAccountUserId='isolated-owner';
const fixture=window.deepseekFixture={calls:[],draft:'',pane:{},bootstrapReads:0,state:{available:true,ownerKey:'a'.repeat(64),sequence:0,status:'ready',visible:false}};
fixture.nextCalls=0;fixture.nativeSequence=0;fixture.nativeQueue=[];
fixture.queueNative=(id,stale=false)=>{const frame=fixture.calls.filter(call=>call.path==='desktop/deepseek'&&call.body?.visible).at(-1)?.body,binding=frame?.shortcuts.bindings.find(item=>item.id===id);if(!binding)throw new Error('No registered fixture command '+id);fixture.nativeRegistration=frame.shortcuts.serial+(stale?1:0);fixture.nativeQueue.push({route:binding.route,id,sequence:++fixture.nativeSequence,ageSeconds:0});};
fixture.editor=()=>EditorView.findFromDOM(document.querySelector('.cm-content'));
const english='# Native pane regression\n\n'+Array.from({length:70},(_,index)=>'Paragraph '+index+': preserve the original statement while the embedded pane is open.').join('\n\n');
const problem=id=>({id,title:'Isolated statement',url:'https://codeforces.com/contest/1016/problem/A',markdown:english,samples:[{name:'Sample',input:'1\n',output:'1\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,locked:false,draft:fixture.draft,submissions:[]});
async function api(path,body){
 fixture.calls.push({path,body});const url=new URL(path,'http://fixture/');
 if(path==='desktop/deepseek'){
  if(!body&&fixture.bootstrapReads++===0)return {available:false,status:'idle',sequence:0};
  if(body&&body.ownerKey!==fixture.state.ownerKey){const error=new Error('Isolated session changed');error.status=409;throw error;}
  if(body)fixture.state={...fixture.state,sequence:body.sequence,visible:body.visible};
  if(body?.retry)fixture.state.status='ready';
  return {...fixture.state};
 }
 if(path==='desktop/deepseek-shortcuts'){const frame=fixture.calls.filter(call=>call.path==='desktop/deepseek'&&call.body?.visible).at(-1)?.body;return {available:true,viewId:frame?.viewId,ownerKey:fixture.state.ownerKey,registration:fixture.nativeRegistration,sequence:fixture.nativeSequence,actions:fixture.nativeQueue};}
 if(url.pathname==='/problem')return problem(url.searchParams.get('id'));
 if(path==='problem/translate')return {markdown:'# 题面回归\n\n'+Array.from({length:70},(_,i)=>`第 ${i} 段：保留原题面的滚动位置。`).join('\n\n'),sourceLanguage:'en',targetLanguage:'zh-CN',kind:'fixture',cached:true};
 if(path==='initial-code')return {templates:[{id:'default',title:'默认',language:'cpp17',code:'int main(){return 0;}'}],selection:{cpp17:'default'}};
 if(path==='templates')return {templates:[]};
 if(path==='draft'){if(fixture.failDraft)throw new Error('Isolated draft save failed');fixture.draft=body.code;return {savedAt:new Date().toISOString()};}
 if(path==='workspace')return {training:[],summary:{total:0,attempts:0}};
 if(path==='official/close')return {closed:true};
 throw new Error('Unknown isolated API '+path);
}
function Fixture(){
 const [active,setActive]=useState(true),[modal,setModal]=useState(false),[search,setSearch]=useState(false),[overlay,setOverlay]=useState(null),[saved,setSaved]=useState({});
 fixture.active=setActive;fixture.modal=setModal;fixture.search=setSearch;fixture.overlay=setOverlay;
 const pane={key:'problem:A',scope:'',visible:active,focused:active,state:saved,remember:(key,value)=>setSaved(previous=>Object.is(previous[key],value)?previous:{...previous,[key]:value})};
 return <><div className="fixture" hidden={!active}><StudyPaneContext.Provider value={pane}><Workbench problemId="A" api={api} onExit={()=>setActive(false)} onNext={async()=>{fixture.nextCalls++;await new Promise(resolve=>setTimeout(resolve,180));}} onProgress={()=>{}} onNotice={()=>{}}/></StudyPaneContext.Provider></div>{modal&&<dialog open aria-label="隔离弹窗">Modal owns the screen</dialog>}{search&&<section className="workspace-search-results">Isolated search overlay</section>}{overlay&&<section role={overlay}>Isolated popup</section>}</>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
