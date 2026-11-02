import {useLayoutEffect,useState} from 'react';
import {createPortal} from 'react-dom';
import {useStudyPane} from '@/lib/StudyPane.jsx';

function PagePortal({children,id,fallbackClass}) {
  const pane=useStudyPane();
  const [host,setHost]=useState(null);
  useLayoutEffect(()=>setHost(pane?null:document.getElementById(id)),[id,Boolean(pane)]);
  if(pane)return null;
  return host ? createPortal(children,host) : <div className={fallbackClass}>{children}</div>;
}

export function PageLocation({children}) {
  return <PagePortal id="tb-page-location" fallbackClass="page-location-fallback">{children}</PagePortal>;
}

export default function PageSearch({children}) {
  return <PagePortal id="tb-page-search" fallbackClass="page-search-fallback"><div className="page-search-controls">{children}</div></PagePortal>;
}
