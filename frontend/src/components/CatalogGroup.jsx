export default function CatalogGroup({title,children}){
 return <div className="catalog-group"><h2 className="lab-catalog-group">{title}</h2><div className="catalog-group-cards">{children}</div></div>;
}
