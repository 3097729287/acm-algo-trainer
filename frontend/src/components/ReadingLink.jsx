// Original attachments are embedded by the public importer. Download exact
// bytes through a short-lived Blob; never allow arbitrary data: navigation.
export default function ReadingLink({ href, children, attachments = {}, ...props }) {
  const variants = [href];
  try { variants.push(decodeURI(href), decodeURIComponent(href)); } catch { /* Keep the original destination. */ }
  const key = variants.find(value => Object.hasOwn(attachments, value));
  const attachment = key && attachments[key];
  const match = attachment?.data?.match(/^data:(application\/(?:pdf|zip|octet-stream)|text\/plain|image\/(?:png|jpeg|gif|webp|avif|bmp|svg\+xml));base64,([a-z\d+/=\s]+)$/i);
  if (!match) return <a {...props} href={href} target="_blank" rel="noreferrer">{children}</a>;
  const download = event => {
    event.preventDefault();
    const bytes = Uint8Array.from(atob(match[2]), char => char.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], { type: match[1] }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = String(attachment.fileName || 'attachment').split(/[\\/]/).pop();
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <a {...props} href={href} download={attachment.fileName || 'attachment'} onClick={download}>{children}</a>;
}
