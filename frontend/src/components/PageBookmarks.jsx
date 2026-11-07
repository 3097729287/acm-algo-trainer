import {useLayoutEffect,useState} from 'react';
import {createPortal} from 'react-dom';

export default function PageBookmarks({children,enabled=true}){
 const [host,setHost]=useState(null);
 useLayoutEffect(()=>setHost(document.getElementById('tb-page-bookmarks')),[]);
 return enabled&&host?createPortal(children,host):children;
}
