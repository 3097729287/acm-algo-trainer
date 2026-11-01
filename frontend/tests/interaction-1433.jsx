import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import PreferencesPage from '../src/pages/PreferencesPage.jsx';
import ProblemFilters from '../src/components/ProblemFilters.jsx';
import {DailyTasks} from '../src/pages/ProgressPanels.jsx';
import MockProblemPicker from '../src/app/MockProblemPicker.jsx';
import {OPACITY_KEYS,SURFACE_DEFAULTS,opacityStyle} from '../src/lib/surfaceOpacity.js';
import {applyEditorTheme} from '../src/lib/editorThemes.js';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';

const initial={selection:{cpp17:'default',python3:'default'},revisions:{cpp17:'r1',python3:'r1'},templates:[{id:'default',title:'默认',builtin:true,language:'cpp17',code:'int main() { return 0; }'},{id:'own',title:'我的模板',builtin:false,language:'cpp17',revision:'r1',code:Array.from({length:120},(_,i)=>`// line ${i+1}`).join('\n')}]};
const calls=[];
const api=async(path,body)=>{calls.push({path,body});if(path==='initial-code/select'){initial.selection[body.language]=body.id;return structuredClone(initial);}if(path==='initial-code')return structuredClone(initial);return {};};
function Fixture(){
 const [tab,setTab]=useState('home'),[prefs,setPrefs]=useState({panelOpacity:0,pageOpacities:{},panelStyle:'outlined',backdrop:'grid',fontSize:18,theme:'dark',accent:'teal',shortcuts:{}}),[mode,setMode]=useState('preferences'),[filter,setFilter]=useState({sort:'contestDate',shelf:'all',min:800,max:3900,result:''});
 useEffect(()=>{const root=document.documentElement;Object.assign(root.dataset,{theme:prefs.theme,accent:prefs.accent,panelStyle:prefs.panelStyle,editorTheme:prefs.editorTheme||'auto'});root.style.setProperty('--ui-font-size','18px');root.style.setProperty('--panel-opacity',prefs.panelOpacity+'%');for(const key of OPACITY_KEYS){const value=prefs.pageOpacities[key]??SURFACE_DEFAULTS[key];if(value!=null)root.style.setProperty('--opacity-'+key,value+'%');else root.style.removeProperty('--opacity-'+key);}applyEditorTheme(root,prefs.editorTheme);},[prefs]);
 window.fixture={prefs,calls,tab,filter,screen:(tab,mode='preferences')=>{setTab(tab);setMode(mode);},setPrefs:value=>setPrefs(previous=>({...previous,...value}))};
 return <main className="workspace-area" style={{height:'100dvh',padding:20,boxSizing:'border-box'}}><div id="tb-page-search"/>{mode==='preferences'?<PreferencesPage tab={tab} onTab={setTab} prefs={prefs} setPrefs={setPrefs} api={api} commands={{pages:[],items:[]}} display={{available:false}} onTutorial={()=>{}}/>:mode==='filter'?<ProblemFilters value={filter} onChange={next=>setFilter(previous=>({...previous,...next}))} onReset={()=>{}} onSave={()=>{}}/>:mode==='picker'?<MockProblemPicker contest={{id:'test',name:'测试',total:2,accepted:0,slots:[{id:'a',title:'A',letter:'A'},{id:'b',title:'B',letter:'B'}]}} currentId="a" onSelect={()=>{}} onHistory={()=>{}}/>:<section className="modal" style={opacityStyle('daily-tasks')}><DailyTasks dailyTasks={{date:'2026-11-01',tasks:Array.from({length:6},(_,index)=>({id:String(index),lane:index<3?'fixed':'rotation',title:`任务 ${index}`,description:'完成练习',target:1,progress:0,xp:10,completed:false}))}}/></section>}</main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
