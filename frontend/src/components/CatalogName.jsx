import './CatalogName.css';

// Keep equal-length Latin identifiers equal in width without changing CJK text.
export default function CatalogName({children}) {
 const text=String(children??'');
 return <>{text.split(/([A-Za-z][A-Za-z0-9.+/_-]*)/).map((part,index)=>/^[A-Za-z]/.test(part)?<span className="catalog-latin-name" key={index}>{part}</span>:part)}</>;
}
