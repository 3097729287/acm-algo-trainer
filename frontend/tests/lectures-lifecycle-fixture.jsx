import React,{useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {LecturesPanel} from '../src/pages/LecturesPanel.jsx';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
import 'katex/dist/katex.min.css';
const lecture={id:'one',concept:'位运算：$v \\oplus (v-1)$',title:'数学标题',tags:['位运算'],markdown:'## 位运算\n\n一个可手算的例子：$4 \\oplus 3 = 7$。\n\n```cpp\nint value = 4 ^ 3;\n```',images:{}};
const api=async path=>path==='lectures'?{lectures:[lecture]}:lecture;
function Fixture(){const [full,setFull]=useState(false),[prefs,setPrefs]=useState({}),visit=useRef({});return <div className={full?'lecture-focus':''} style={{height:'100%',padding:20}}><LecturesPanel api={api} visit={visit.current} prefs={prefs} setPrefs={setPrefs} onFullscreenChange={setFull}/></div>;}
createRoot(document.getElementById('root')).render(<Fixture/>);
