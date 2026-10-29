import React from 'react';
import {createRoot} from 'react-dom/client';
import AbilityEvidence from '../src/components/AbilityEvidence.jsx';
import '../src/styles/workspace.css';
const rows=Array.from({length:6},(_,index)=>({id:`fixture-${index}`,contest:'公开合成证据',problem:String.fromCharCode(65+index),title:`训练证据 ${index+1}`}));
const evidence=rows.map((row,index)=>({id:row.id,problemId:row.id,difficulty:1000+index*100,solved:index!==5,weight:index<4?1:.25,difficultyKind:index<4?'official-cf':'cross-platform'}));
const rank={model:'rasch-v1',attemptedCount:6,ratedEvidenceCount:6,evidenceCount:5,effectiveEvidence:4.5,posteriorInterval:[960,1520],supportCeiling:1000,recentPerformance:{attempted:6,independentSolved:5,firstPass:4,timedAttempted:2,timedSolved:1},topicEvidence:{数据结构:{attempted:3,independentSolved:2}},evidence,rules:'同一原题只计一份学习证据；失败也参与估计。'};
document.documentElement.dataset.theme='dark';document.documentElement.style.setProperty('--ui-font-size','22px');
createRoot(document.getElementById('root')).render(<main style={{height:'100vh',padding:'40px',display:'flex',justifyContent:'center',alignItems:'center'}}><AbilityEvidence rank={rank} rows={rows}/><button type="button">其他操作</button></main>);
