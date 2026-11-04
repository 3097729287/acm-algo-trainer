// Emitted only after a user operation succeeds; no code or account data.
export function guideAction(name){window.dispatchEvent(new CustomEvent('tb:guide-action',{detail:{name}}));}
