import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Target,Library,Flag,History} from 'lucide-react';
import ReorderableNavigation from '../src/components/ReorderableNavigation.jsx';
import NavigationSettings from '../src/pages/NavigationSettings.jsx';
import '../src/styles/workspace.css';
import '../src/components/SettingsControls.css';
const pages=[{id:'mine',label:'我的训练',icon:Target},{id:'library',label:'题库',icon:Library},{id:'competitions',label:'比赛',icon:Flag},{id:'records',label:'提交记录',icon:History}];
function Fixture(){
 const [entries,setEntries]=useState(pages),[prefs,setPrefs]=useState({hiddenNavPages:[]}),[page,setPage]=useState('mine');
 window.dragFixture={entries:entries.map(x=>x.id),page,prefs};
 return <div className="app-shell"><aside className="sidebar"><div className="brand">ToBe</div><ReorderableNavigation entries={entries} onReorder={value=>{setEntries(value);window.reorderSaves=(window.reorderSaves||0)+1;}}>{item=><button className="nav-item" aria-label={item.label} onClick={()=>setPage(item.id)}><item.icon size={18}/><span>{item.label}</span></button>}</ReorderableNavigation></aside><main className="main-area" style={{padding:20}}><NavigationSettings pages={pages} prefs={prefs} setPrefs={setPrefs} level={20}/></main></div>;
}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<Fixture/>);
