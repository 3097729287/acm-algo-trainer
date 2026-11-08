import SectionWorkspace from './SectionWorkspace.jsx';
import {lazy,Suspense} from 'react';
import RankingsPage from '@/pages/CommunityPanel.jsx';
import DuelCommunity from './DuelCommunity.jsx';
import {UsersRound} from 'lucide-react';
import './RankingsWorkspace.css';

const BOOKMARKS=[{id:'ranked',title:'排位分'},{id:'accepted',title:'过题数'},{id:'team',title:'团队训练'}];
const TeamTraining=lazy(()=>import('./TeamTraining.jsx'));
export function TeamStandings({snapshot}){
 const entries=(snapshot?.entries||[]).filter(item=>item.teamId&&Number.isFinite(item.totalScore)).slice().sort((a,b)=>b.totalScore-a.totalScore||String(a.teamId).localeCompare(String(b.teamId)));
 return <section className="team-standings" aria-label="团队训练排行榜"><header><h2><UsersRound size={18}/>团队训练排行榜</h2><span>团队总分</span></header>{entries.length?<table><thead><tr><th>名次</th><th>团队</th><th>总分</th></tr></thead><tbody>{entries.map((item,index)=><tr key={item.teamId}><td>{index&&entries[index-1].totalScore===item.totalScore?entries.findIndex(row=>row.totalScore===item.totalScore)+1:index+1}</td><td>{item.name}</td><td>{item.totalScore.toLocaleString('zh-CN')}</td></tr>)}</tbody></table>:<p className="progress-muted" role="status">{snapshot?'暂无团队训练成绩':'尚未接入团队训练成绩。'}</p>}</section>;
}
export default function RankingsWorkspace({prefs,setPrefs,owner,teamTraining,...props}){
 return <SectionWorkspace id="rankings" entries={BOOKMARKS} activeId={prefs.learningPaths?.sectionWorkspaces?.rankings?.focused?undefined:'accepted'} prefs={prefs} setPrefs={setPrefs} owner={owner} render={id=>id==='accepted'?<RankingsPage {...props}/>:id==='ranked'?<DuelCommunity api={props.api} owner={owner} mode="ranked" standingsOnly/>:teamTraining?<Suspense fallback={<p role="status">正在读取团队训练…</p>}><TeamTraining controller={teamTraining} owner={owner}/></Suspense>:<TeamStandings snapshot={teamTraining}/>}/>;
}
