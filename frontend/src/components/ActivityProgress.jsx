import '../pages/ActivityPage.css';
export default function ActivityProgress({count=0,step=3,label='当天首次 AC'}) {
 const amount=Math.max(0,Number(count)||0),capacity=step*7;
 return <span className="activity-progress" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={capacity} aria-valuenow={Math.min(capacity,amount)} aria-valuetext={`${amount} 题，${capacity} 题满格${amount>capacity?`，超额 ${amount-capacity} 题`:''}`} title={`${amount} 题 · ${capacity} 题满格`}>
  {Array.from({length:7},(_,index)=><span className="activity-progress-segment" data-band={index+1} key={index}><i style={{width:`${Math.min(1,Math.max(0,(amount-index*step)/step))*100}%`}}/></span>)}
 </span>;
}
