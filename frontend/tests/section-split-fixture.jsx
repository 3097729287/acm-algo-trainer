import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Library,FolderOpen,Target} from 'lucide-react';
import SectionWorkspace from '../src/components/SectionWorkspace.jsx';
import {emptyStudyBrowser,openStudyTab,splitStudyTab,studySnapshot} from '../src/lib/learningBrowser.js';
import {ProblemCells,ProblemTableHead} from '../src/components/ProblemTableParts.jsx';
import PagePagination from '../src/components/PagePagination.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-160.css';

const entries=[{id:'mine',title:'我的训练',icon:Target,minWidth:620},{id:'library',title:'题库',icon:Library,minWidth:620},{id:'training-lists',title:'题单',icon:FolderOpen,minWidth:420}];
const rows=Array.from({length:12},(_,index)=>({id:'fixture-'+index,title:['Numbers on the Board','Rhythmic String','Big XOR','Black, Gray and White','Partition of a Binary String'][index%5],contest:'教育赛 196',problem:String.fromCharCode(65+index),tags:['组合计数','字符串','构造'],platform:'Codeforces',difficulty:1300,lastActivityAt:'2026-11-05T01:00:00+08:00',active:true,verdict:index%2?'WA':'AC'}));
function initial(){
 try{const saved=localStorage.getItem('split-fixture');if(saved)return JSON.parse(saved);}catch{}
 let state=entries.reduce((value,entry)=>openStudyTab(value,{kind:'panel',id:entry.id,title:entry.title}),emptyStudyBrowser());
 state=splitStudyTab(state,'panel:library');
 const query=new URLSearchParams(location.search);if(query.has('three'))state=splitStudyTab(state,'panel:training-lists',{targetGroupId:state.groups[0].id});
 if(query.has('skew'))state.groups=state.groups.map((group,index)=>({...group,weight:index?10:90}));
 return {fontSize:15,learningPaths:{sectionWorkspaces:{training:studySnapshot(state)}}};
}
function Fixture(){
 const [prefs,setPrefs]=useState(initial),[active,setActive]=useState('mine'),[page,setPage]=useState(1);
 window.splitFixture={prefs,setPrefs};
 document.documentElement.dataset.theme=new URLSearchParams(location.search).get('theme')||'dark';
 document.documentElement.style.setProperty('--ui-font-size',prefs.fontSize+'px');document.documentElement.style.fontSize=prefs.fontSize+'px';
 localStorage.setItem('split-fixture',JSON.stringify(prefs));
 const render=id=>id==='training-lists'?<div className="training-lists-page" style={{minWidth:0,padding:14}}><p>我的收藏</p></div>:<div className="list-page"><div className="table-scroll"><table className="problem-table"><ProblemTableHead/><tbody>{id==='mine'&&<tr className="queue-heading accent"><td colSpan={6}>待攻克</td></tr>}{rows.map(row=><tr key={row.id} data-id={row.id}><ProblemCells row={row} onTrain={()=>{}} onAddToList={()=>{}} onFavorite={()=>{}} onRemove={id==='mine'?()=>{}:undefined}/></tr>)}</tbody></table></div>{id==='library'?<PagePagination label="题库分页" count="共 13061 题" page={page} pages={1307} onPageChange={setPage} onPrevious={()=>setPage(value=>value-1)} onNext={()=>setPage(value=>value+1)}/>:<div className="list-footer">共 18 题</div>}</div>;
 return <main className="workspace-area" style={{width:'100%',height:'100dvh',background:'var(--bg)'}}><SectionWorkspace id="training" entries={entries} activeId={active} onActivate={setActive} render={render} prefs={prefs} setPrefs={setPrefs} owner="local"/></main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
