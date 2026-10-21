import { useEffect, useRef, useState } from 'react';
import { ImagePlus, LoaderCircle, Trash2, UserRound } from 'lucide-react';
import { SettingRow } from './SettingsControls.jsx';
import Tooltip from './Tooltip.jsx';
import { isAvatarData, MAX_AVATAR_DATA_LENGTH } from './ProfileBadge.jsx';
import './ProfileBadge.css';

async function avatarFromFile(file) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 12 * 1024 * 1024) {
    throw new Error('请选择 12 MB 以内的 PNG、JPEG 或 WebP 图片');
  }
  const bitmap = await createImageBitmap(file);
  try {
    const ratio = Math.min(1, 96 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * ratio));
    canvas.height = Math.max(1, Math.round(bitmap.height * ratio));
    const context = canvas.getContext('2d');
    if (!context) throw new Error('暂时无法处理这张头像图片');
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const original = canvas.toDataURL('image/png');
    if (original.length <= MAX_AVATAR_DATA_LENGTH) return original;
    for (const quality of [.9, .8, .65, .5]) {
      const result = canvas.toDataURL('image/webp', quality);
      if (result.length <= MAX_AVATAR_DATA_LENGTH) return result;
    }
    throw new Error('头像压缩后仍然过大，请选择另一张图片');
  } finally {
    bitmap.close();
  }
}

export default function AvatarSettings({ prefs, setPrefs, onError }) {
  const input = useRef(null), revision = useRef(0);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [status, setStatus] = useState('');
  const image = isAvatarData(prefs?.avatarData) ? prefs.avatarData : null;
  useEffect(() => () => { revision.current++; }, []);

  async function selected(event) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    if (!file) return;
    const currentRevision = ++revision.current;
    setBusy(true); setError(''); setStatus('正在处理头像');
    try {
      const result = await avatarFromFile(file);
      if (revision.current !== currentRevision) return;
      setPrefs(previous => ({ ...previous, avatarData: result }));
      setStatus('头像已保存');
    } catch (issue) {
      if (revision.current !== currentRevision) return;
      const message = issue.message || '这张图片无法用作头像';
      setError(message); setStatus(''); onError?.(message);
    } finally {
      if (revision.current === currentRevision) setBusy(false);
    }
  }

  function clear() {
    revision.current++; setBusy(false); setError(''); setStatus('已恢复默认头像');
    setPrefs(previous => ({ ...previous, avatarData: '' }));
  }

  return <section className="avatar-settings" aria-label="头像设置">
    <h2>头像</h2>
    <SettingRow title="头像" hint="头像显示在等级经验环内。PNG、JPEG 或 WebP，最大 12 MB；自动缩小至 96 像素以内并压缩。">
      <span className="avatar-settings-preview" role="img" aria-label={image ? '当前头像' : '默认头像'}>{image ? <img src={image} alt="" /> : <UserRound size={28} aria-hidden="true" />}</span>
      <div className="avatar-settings-actions">
        <input ref={input} type="file" hidden accept="image/png,image/jpeg,image/webp" aria-label="头像图片文件" onChange={selected} />
        <Tooltip text="选择头像图片"><button type="button" aria-label="选择头像图片" aria-busy={busy} disabled={busy} onClick={() => input.current?.click()}>{busy ? <LoaderCircle size={18} className="spin" /> : <ImagePlus size={18} />}</button></Tooltip>
        <Tooltip text="恢复默认头像"><button type="button" aria-label="恢复默认头像" disabled={!image || busy} onClick={clear}><Trash2 size={17} /></button></Tooltip>
      </div>
    </SettingRow>
    {error && <p role="alert" className="avatar-settings-error">{error}</p>}
    <span role="status" className="avatar-settings-status">{status}</span>
  </section>;
}
