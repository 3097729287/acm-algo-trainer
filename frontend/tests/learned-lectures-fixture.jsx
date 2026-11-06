import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {LecturesPanel} from '../src/pages/LecturesPanel.jsx';
import {FOUNDATION_LESSONS} from '../src/lib/learningCurriculum.js';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
const lessons=FOUNDATION_LESSONS.slice(0,3).map(item=>({...item,markdown:'# '+item.title+'\n\n基础内容。'}));
const api=async path=>lessons.find(item=>item.id===new URL(path,'http://fixture/').searchParams.get('id'));
document.documentElement.dataset.theme='dark';
document.documentElement.dataset.panelStyle='wireframe';
function Fixture(){
 const [prefs,setPrefs]=useState(()=>JSON.parse(localStorage.getItem('learned-lectures-fixture')||'{}')),[key,reset]=useState(0);
 useEffect(()=>localStorage.setItem('learned-lectures-fixture',JSON.stringify(prefs)),[prefs]);
 window.learnedLectureFixture={reset:()=>reset(value=>value+1),prefs};
 return <div className="workspace-area" style={{height:'100vh',padding:16}}><div id="tb-page-search"/><LecturesPanel key={key} lectures={lessons} api={api} prefs={prefs} setPrefs={setPrefs}/></div>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
