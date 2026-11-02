import {BookOpen,ChevronRight} from 'lucide-react';
import './LearningCatalogue.css';

export function CatalogueGroup({title,children}){
 return <section className="learning-catalogue-group"><h3>{title}</h3>{children}</section>;
}

export function CatalogueEntry({title,label,icon,onOpen,onContextMenu,className=''}){
 return <button type="button" className={'learning-catalogue-entry '+className} aria-label={label||title} onClick={onOpen} onContextMenu={onContextMenu}>{icon||<BookOpen size={17}/>}<span>{title}</span><ChevronRight size={16}/></button>;
}
