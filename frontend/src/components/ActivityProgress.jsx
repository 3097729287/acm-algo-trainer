import '../pages/ActivityPage.css';
export default function ActivityProgress({count=0,step=5,label='当天首次 AC'}) {
 const amount=Math.max(0,Number(count)||0),capacity=step*5;
 return <span className="activity-progress" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={Math.max(capacity,amount)} aria-valuenow={amount} aria-valuetext={`${amount} 题，每段 ${step} 题`} title={`${amount} 题 · 每段 ${step} 题`}>
  {Array.from({length:5},(_,index)=><span className="activity-progress-segment" data-band={index+1} key={index}><i style={{width:`${Math.min(1,Math.max(0,(amount-index*step)/step))*100}%`}}/></span>)}
 </span>;
}
