import {useLayoutEffect,useState} from 'react';
import {createPortal} from 'react-dom';
import {useStudyPane} from '@/lib/StudyPane.jsx';

function PagePortal({children,id,fallbackClass}) {
  const pane=useStudyPane();
  const topbarSearch=id==='tb-page-search'&&pane?.topbarSearch===true,globalHost=!pane||topbarSearch;
  const [host,setHost]=useState(null);
  useLayoutEffect(()=>setHost(globalHost?document.getElementById(id):null),[id,globalHost]);
  if(topbarSearch&&(!pane.visible||!pane.focused))return null;
  if(pane&&!topbarSearch)return pane.pageHosts?.[id]?createPortal(children,pane.pageHosts[id]):null;
  if(pane&&!host)return null;
  return host ? createPortal(children,host) : <div className={fallbackClass}>{children}</div>;
}

export function PageLocation({children}) {
  return <PagePortal id="tb-page-location" fallbackClass="page-location-fallback">{children}</PagePortal>;
}

export default function PageSearch({children}) {
  return <PagePortal id="tb-page-search" fallbackClass="page-search-fallback"><div className="page-search-controls">{children}</div></PagePortal>;
}
