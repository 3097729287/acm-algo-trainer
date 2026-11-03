import {createRoot} from 'react-dom/client';
import {useMemo,useState} from 'react';
import DuelPage from '../src/pages/DuelPage.jsx';
import useThoughtDuel from '../src/lib/useThoughtDuel.js';
import useDuel from '../src/lib/useDuel.js';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
function Fixture(){
 const [owner,setOwner]=useState(new URLSearchParams(location.search).get('owner')||'A');
 window.selectPkOwner=setOwner;
 const api=useMemo(()=>async(path,body)=>{
  const response=await fetch('/__pk_proxy/'+owner+'/'+path,{...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
  const value=await response.json();if(!response.ok){const error=new Error(value.error);error.status=response.status;throw error;}return value;
 },[owner]);
 const [identity,setIdentity]=useState(null);window.pkFixtureIdentity=value=>setIdentity(value);
 const id=identity?.[owner]||owner;
 const thought=useThoughtDuel(api,id),duel=useDuel(api,id);
 return <main style={{height:'100dvh',padding:16,boxSizing:'border-box',display:'flex'}}><DuelPage duel={duel} thought={thought} rows={[]} account={{userId:id,nickname:'选手 '+owner}} growth={{level:14,currentLevelXp:50,nextLevelXp:100}}/></main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
