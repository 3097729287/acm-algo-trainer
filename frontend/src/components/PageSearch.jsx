import {useLayoutEffect,useState} from 'react';
import {createPortal} from 'react-dom';

export default function PageSearch({children}) {
  const [host,setHost]=useState(null);
  useLayoutEffect(()=>setHost(document.getElementById('tb-page-search')),[]);
  return host ? createPortal(<div className="page-search-controls">{children}</div>,host) : <div className="page-search-controls page-search-fallback">{children}</div>;
}
