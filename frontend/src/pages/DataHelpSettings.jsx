import { useState } from 'react';
import { Download, GraduationCap, Heart, LoaderCircle } from 'lucide-react';
import Tooltip from '../components/Tooltip.jsx';

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
      <Tooltip text="导出当前账号的训练、代码、记录、目标和偏好为 JSON；不含密码、Cookie 或 API 密钥。"><button className="help-action" aria-label="导出数据 · JSON" onClick={download} disabled={busy}>
        {busy ? <LoaderCircle size={22} className="spin"/> : <Download size={22}/>}
      </button></Tooltip>
      <Tooltip text="新手指引：从选题到原站提交。"><button className="help-action" aria-label="新手指引" onClick={onTutorial}><GraduationCap size={22}/></button></Tooltip>
    </div>
  </section>;
}
