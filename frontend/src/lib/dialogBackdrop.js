const starts=new WeakMap();
const outside=(event,node)=>{const box=node.getBoundingClientRect();return event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom;};
export function dialogPointerDown(event){starts.set(event.currentTarget,outside(event,event.currentTarget));}
export function dialogBackdropClick(event){const node=event.currentTarget,started=starts.get(node);starts.delete(node);if(started&&outside(event,node)){const canceled=!node.dispatchEvent(new Event('cancel',{cancelable:true}));if(!canceled)node.close();}}
