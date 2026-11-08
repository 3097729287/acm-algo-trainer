import React from 'react';
import {createRoot} from 'react-dom/client';
import SolutionMarkdown from '../src/components/SolutionMarkdown.jsx';
import '../src/styles/workspace.css';
import '../src/components/SolutionReader.css';

document.documentElement.dataset.theme='dark';
window.__tbAccountUserId='reference-fixture';
const original='#include <bits/stdc++.h>\nusing namespace std;\nint main(){for(int i=0;i<10;++i){cout<<i;}}\n';
const expected='#include <bits/stdc++.h>\nusing namespace std;\nint main() {\n    for (int i = 0; i < 10; i++) {\n        cout << i;\n    }\n}\n';
window.referenceFixture={original,expected,calls:[],copied:null};
async function api(path,body){
 window.referenceFixture.calls.push({path,body});
 if(path!=='code/format')throw Error('Unexpected fixture API');
 const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body.code));
 await new Promise(resolve=>setTimeout(resolve,30));
 return {code:expected,inputSha256:[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('')};
}
createRoot(document.getElementById('root')).render(<div className="reader-content" style={{maxWidth:680,margin:30}}><SolutionMarkdown text={(location.search.includes('legacy')?'```cxx\n':'```cpp\n')+original+'```'} api={api} problemId="fixture:reference" onCopy={value=>{window.referenceFixture.copied=value;}}/></div>);
