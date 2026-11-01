import React from 'react';
import {createRoot} from 'react-dom/client';
import InitialCodeSettings from '../src/pages/InitialCodeSettings.jsx';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/revision.css';
const state={templates:[{id:'default',title:'默认',language:'cpp17',code:'int main() {}',builtin:true},{id:'one',title:'模板1',language:'cpp17',code:'int main() { return 0; }',revision:1,builtin:false},{id:'default',title:'默认',language:'python3',code:'print(1)',builtin:true}],selection:{cpp17:'one',python3:'default'},revisions:{cpp17:1,python3:1}};
window.templateFixture={state,calls:[]};
const api=async(path,body)=>{
 window.templateFixture.calls.push({path,body});await new Promise(resolve=>setTimeout(resolve,20));let item;
 if(path==='initial-code/save'){
  item=body.id?state.templates.find(row=>row.id===body.id&&row.language===body.language):{id:'new-'+state.templates.length,builtin:false};
  if(!body.id)state.templates.push(item);Object.assign(item,body,{revision:(item.revision||0)+1});state.revisions[body.language]++;
 }else if(path==='initial-code/select'){state.selection[body.language]=body.id;state.revisions[body.language]++;}
 else if(path!=='initial-code')throw Error(path);
 return structuredClone({...state,...(item?{template:item}:{})});
};
document.documentElement.dataset.theme='dark';document.documentElement.style.setProperty('--ui-font-size','18px');
createRoot(document.getElementById('root')).render(<React.StrictMode><div className="settings-page" style={{height:'100dvh'}}><InitialCodeSettings api={api}/></div></React.StrictMode>);
