import { useState } from 'react';
import { Download, GraduationCap, Heart, LoaderCircle } from 'lucide-react';

export default function DataHelpSettings({ api, onTutorial, onError }) {
  const [busy, setBusy] = useState(false);
  async function download() {
    if (busy) return;
    setBusy(true);
    try {
      const value = await api('data/export');
      const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2) + '\n'], { type: 'application/json;charset=utf-8' }));
      const link = document.createElement('a');
      link.href = url; link.download = `TB-data-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (error) { onError(error.message); }
    finally { setBusy(false); }
  }
  return <section className="settings-data-help" aria-label="数据与帮助">
    <h2>数据与帮助</h2>
    <div className="help-action-grid">
      <button className="help-action" onClick={download} disabled={busy}>
        {busy ? <LoaderCircle size={22} className="spin"/> : <Download size={22}/>}
        <span><strong>{busy ? '正在导出' : '导出数据 · JSON'}</strong><small>训练、代码、记录、目标与偏好</small></span>
      </button>
      <button className="help-action" onClick={onTutorial}><GraduationCap size={22}/><span><strong>新手指引</strong><small>从选题到原站提交</small></span></button>
    </div>
    <p className="export-note">仅导出当前账号，不含密码、Cookie 和 API 密钥。JSON 是数据备份，暂不支持在界面导入。</p>
    <div className="acknowledgements"><Heart size={16}/><span>鸣谢</span><strong>InkStarry</strong><strong>猫猫头教主</strong><strong>蒟蒻</strong></div>
  </section>;
}
