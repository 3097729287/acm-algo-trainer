import {useEffect, useState} from 'react';

// Feed the original PDF bytes to the browser's PDF viewer. Its own zoom,
// scrolling and page selection stay inside the statement pane.
export default function StatementPdf({pdf, title}) {
  const [source, setSource] = useState('');
  const data = pdf?.data || '';
  useEffect(() => {
    if (!/^data:application\/pdf;base64,[a-z\d+/=\s]+$/i.test(data)) return;
    const bytes = Uint8Array.from(atob(data.split(',')[1]), char => char.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], {type:'application/pdf'}));
    setSource(url);
    return () => URL.revokeObjectURL(url);
  },[data]);
  return source ? <iframe className="wb-statement-pdf" title={title || '题面内容'} src={`${source}#view=FitH`} /> : null;
}
