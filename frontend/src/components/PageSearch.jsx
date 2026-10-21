import {useLayoutEffect,useState} from 'react';
import {createPortal} from 'react-dom';

function PagePortal({children,id,fallbackClass}) {
  const [host,setHost]=useState(null);
  useLayoutEffect(()=>setHost(document.getElementById(id)),[id]);
  return host ? createPortal(children,host) : <div className={fallbackClass}>{children}</div>;
}

export function PageLocation({children}) {
  return <PagePortal id="tb-page-location" fallbackClass="page-location-fallback">{children}</PagePortal>;
}

export default function PageSearch({children}) {
  return <PagePortal id="tb-page-search" fallbackClass="page-search-fallback"><div className="page-search-controls">{children}</div></PagePortal>;
}
