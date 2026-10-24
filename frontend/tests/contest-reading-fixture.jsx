import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {CompetitionPage} from '../src/pages/ProgressPanels.jsx';
import {progressRows} from '../src/models/workspaceModel.js';
import '../src/styles/workspace.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';

const events=['CCPC 2026 福建邀请赛','CCPC 2026 秦皇岛邀请赛','ICPC 2026 广西邀请赛',
  'ICPC 2026 广西邀请赛（热身赛）','ICPC 2026 武汉邀请赛','周赛 166','蓝桥杯 2026 省赛'];
const source=events.flatMap((contest,event)=>Array.from({length:event===0?13:3},(_,i)=>({
  id:`event-${event}-${i}`,contest,title:`第 ${i+1} 道完整题目`,problem:String.fromCharCode(65+i),
  platform:event<5?'Codeforces':'洛谷',series:event<5?'XCPC':event===5?'周赛':'蓝桥杯',tags:[],
  difficulty:1400+i*100,difficultyBand:[1300+i*100,1500+i*100],difficultySource:'fixture rating',
  solutionAvailable:false,collectionNotice:'按 Codeforces Gym 公开题单核对；题面打开时联网读取。',
  contestDifficulty:4,eventYear:2026,
})));
window.contestActions=[];
function Fixture(){
  const [workspace,setWorkspace]=useState({training:[],contests:[]});
  window.setContestWorkspace=setWorkspace;
  const rows=progressRows(source,workspace);
  window.contestProgressRows=rows;
  window.contestRows=rows;
  return <main className="workspace-area" style={{display:'flex',height:'100vh',boxSizing:'border-box',overflow:'hidden'}}>
    <CompetitionPage rows={rows} workspace={workspace} onTrain={id=>window.contestActions.push(['practice',id])}
      onJoin={name=>window.contestActions.push(['join',name])} onStartReproduction={name=>window.contestActions.push(['replay',name])}/>
  </main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
