// Navigation can be newer than the debounced SQLite preference write.
// Keep a small, owner-scoped local copy so an immediate refresh is safe.
function read(owner,section){try{const value=JSON.parse(localStorage.getItem(`tb.bookmarks.v1.${owner}.${section}`));return value?.owner===owner?value.value:null;}catch{return null;}}
function write(owner,section,value){if(!owner)return;try{localStorage.setItem(`tb.bookmarks.v1.${owner}.${section}`,JSON.stringify({owner,value}));}catch{/* The normal preference path still persists the same navigation. */}}
export const readSectionBookmark=(owner,id)=>read(owner,'section:'+id);
export const rememberSectionBookmark=(owner,id,value)=>write(owner,'section:'+id,value);
export const readPageBookmark=(owner,group)=>read(owner,'group:'+group);
export const rememberPageBookmark=(owner,group,id)=>write(owner,'group:'+group,id);
