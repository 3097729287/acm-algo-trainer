import {useEffect,useState} from 'react';
import {Copy,LoaderCircle,RotateCcw} from 'lucide-react';

export default function HistoricalCode({submission,api}) {
 const [record,setRecord]=useState(submission),[error,setError]=useState(''),[attempt,setAttempt]=useState(0);
 const shown=record.id===submission.id?record:submission;
 const pending=Boolean(shown.codePending);
 useEffect(()=>{
  let live=true;setRecord(submission);setError('');
  if(submission.codePending)api(`submission?id=${encodeURIComponent(submission.id)}`).then(value=>{if(live)setRecord(value.submission);}).catch(issue=>{if(live)setError(issue.message);});
  return()=>{live=false;};
 },[submission,api,attempt]);
 return <><div className="submission-code-tools"><button className="secondary" disabled={pending||!shown.code} onClick={()=>navigator.clipboard.writeText(shown.code).catch(()=>setError('复制未完成，请选中代码后复制'))}><Copy size={14}/>复制本次代码</button></div>{error?<div role="alert">{error}<button className="icon-button" aria-label="重新读取提交代码" onClick={()=>setAttempt(n=>n+1)}><RotateCcw size={16}/></button></div>:pending?<div role="status" aria-label="正在读取历史代码"><LoaderCircle className="spin" size={20}/></div>:<pre className="submission-source"><code>{shown.code||'这条记录没有保存代码。'}</code></pre>}</>;
}
