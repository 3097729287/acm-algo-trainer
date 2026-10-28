import './CatalogCard.css';
export default function CatalogCard({title,icon,onOpen,label,children}) {
 return <section className="lab-panel catalog-card" aria-label={title}>
  <button type="button" className="catalog-card-open" aria-label={label||title} onClick={onOpen}/>
  <h3 className="catalog-card-heading">{icon}<span>{title}</span></h3>
  {children&&<div className="catalog-card-actions">{children}</div>}
 </section>;
}
