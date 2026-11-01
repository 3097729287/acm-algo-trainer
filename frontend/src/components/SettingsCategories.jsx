import {ChevronRight} from 'lucide-react';
import {useContext,useLayoutEffect,useRef} from 'react';
import SettingsBackContext from './SettingsBackContext.jsx';
import './SettingsCategories.css';

export default function SettingsCategories({groups,selected,onSelect,label,children}) {
  const current=groups.find(group=>group.id===selected);
  const registerBack=useContext(SettingsBackContext),select=useRef(onSelect);select.current=onSelect;
  useLayoutEffect(()=>current&&registerBack?registerBack(()=>select.current(''),label):undefined,[current?.id,registerBack,label]);
  return <div className="settings-categories">
    {current?<div className="settings-category-content" key={current.id}>{children(current)}</div>:<div className="settings-category-grid" aria-label={label}>{groups.map(({id,label:caption,icon:Icon})=><button type="button" key={id} onClick={()=>onSelect(id)}><Icon size={23}/><strong>{caption}</strong><ChevronRight className="settings-category-arrow" size={16}/></button>)}</div>}
  </div>;
}
