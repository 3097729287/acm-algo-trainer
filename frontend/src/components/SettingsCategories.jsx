import {ArrowLeft, ChevronRight} from 'lucide-react';
import './SettingsCategories.css';

export default function SettingsCategories({groups,selected,onSelect,label,children}) {
  const current=groups.find(group=>group.id===selected);
  return <div className="settings-categories">
    {current?<><header className="settings-category-heading"><button type="button" className="icon-button" aria-label={`返回${label}`} title={`返回${label}`} onClick={()=>onSelect('')}><ArrowLeft size={18}/></button><h3>{current.label}</h3></header><div className="settings-category-content" key={current.id}>{children(current)}</div></>:<div className="settings-category-grid" aria-label={label}>{groups.map(({id,label:caption,icon:Icon})=><button type="button" key={id} onClick={()=>onSelect(id)}><Icon size={23}/><strong>{caption}</strong><ChevronRight className="settings-category-arrow" size={16}/></button>)}</div>}
  </div>;
}
