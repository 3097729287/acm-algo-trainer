import { useState } from 'react';
import { Download, GraduationCap, Heart, LoaderCircle } from 'lucide-react';
import Tooltip from '../components/Tooltip.jsx';
import PersonalStatistics from './PersonalStatistics.jsx';

export default function DataHelpSettings({ api, onTutorial, onError, insights, account, onTrain }) {
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
  return <><PersonalStatistics api={api} insights={insights} account={account} onTrain={onTrain}/><section className="settings-data-help" aria-label="数据与帮助">
    <h2>数据与帮助</h2>
    <div className="help-action-grid">
      <Tooltip text="导出当前账号的训练、代码、记录、目标和偏好为 JSON；不含密码、Cookie 或 API 密钥。"><button className="help-action" aria-label="导出数据 · JSON" onClick={download} disabled={busy}>
        {busy ? <LoaderCircle size={22} className="spin"/> : <Download size={22}/>}<span><strong>导出我的数据</strong><small>训练、代码、目标与偏好 · JSON</small></span>
      </button></Tooltip>
      <Tooltip text="新手指引：入门总览与各页操作指南。"><button className="help-action" aria-label="新手指引" onClick={onTutorial}><GraduationCap size={22}/><span><strong>新手指引</strong><small>入门总览与各页面操作说明</small></span></button></Tooltip>
    </div>
  </section></>;
}
