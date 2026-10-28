import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import HistoricalCode from '../src/components/HistoricalCode.jsx';
const pending=new Map(),calls=[];
const api=path=>new Promise((resolve,reject)=>{calls.push(path);pending.set(path.split('=')[1],{resolve,reject});});
function Fixture(){
 const [submission,setSubmission]=useState(null);
 window.fixture={show:setSubmission,calls,resolve:(id,code)=>pending.get(id).resolve({submission:{id,code,codePending:false}}),reject:id=>pending.get(id).reject(new Error('临时网络错误'))};
 return submission?<HistoricalCode submission={submission} api={api}/>:null;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
