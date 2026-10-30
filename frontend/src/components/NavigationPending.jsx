import './NavigationPending.css';

export default function NavigationPending() {
  return <div className="navigation-pending" aria-hidden="true">{Array.from({length:12},(_,index)=><span key={index}><i/><b/></span>)}</div>;
}
