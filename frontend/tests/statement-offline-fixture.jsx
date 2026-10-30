import React from 'react';
import {createRoot} from 'react-dom/client';
import {StatementMarkdown} from '../src/app/Workbench.jsx';
const image='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
const pdf='JVBERi0xLjcKJSBvZmZsaW5lIGZpeHR1cmUK';
createRoot(document.getElementById('root')).render(<StatementMarkdown
  title="Offline original" markdown={'# Offline original\n\n| Judge | Program |\n| --- | --- |\n| `2`<br />`1 2`<br />`3 4` | query<br />reply |\n\n![Original animation](https://img.atcoder.jp/fixture.gif)\n\n[PDF](https://qoj.ac/original.pdf)\n\n[GIF](https://img.atcoder.jp/download.gif)\n\n<script>window.untrustedScript=true</script>'}
  samples={[{input:'2\n1 2\n3 4',output:'7\n8'}]}
  images={{'https://img.atcoder.jp/fixture.gif':image}}
  attachments={{'https://qoj.ac/original.pdf':{data:'data:application/pdf;base64,'+pdf,fileName:'original.pdf'},
    'https://img.atcoder.jp/download.gif':{data:image,fileName:'original.gif'}}}
/>);
