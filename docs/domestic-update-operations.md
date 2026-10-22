# 国内更新运行记录

1.3.5 从自有 HTTPS 地址读取版本与两项用户资产，不依赖 GitHub。发布使用 `scripts/publish_domestic_update.py`，先验证和上传资产，最后原子替换清单；管理员文件禁止公开。Caddy 使用原配置持久卷，账号 API、MySQL 和协议不改动。

2026-10-22 本机到服务器的 64 KiB 范围下载实测：CUBIC 约 12.08 秒，Caddy 网络命名空间使用 BBR 后约 4.04 秒。单次对照不代表所有地区、时段的持续速率。宿主 SSH、其他容器、队列与防火墙未更改。

生产主机已有 `tcp_bbr` 模块；确认模块可用后，可在私有部署 `.env` 设置 `TB_TCP_CONGESTION_CONTROL=bbr`。`compose.yaml` 默认仍为 cubic，避免给不支持 BBR 的机器引入启动要求。服务器模块加载配置只加入 tcp_bbr，不重建数据库或 API。运行中的 Caddy 通过其网络命名空间应用同值，无需为此重启容器。原值与部署文件均保留在服务器 updates 下。

[Linux 参数语义](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html) · [Google BBR 启用与 pacing 说明](https://github.com/google/bbr/blob/master/Documentation/bbr-quick-start.md)。

登录补充修复 `00f8cb9` 在远端版本未变时不重复下载大型快照；有本机修改时仍先成功上传，再开放登录。远端版本变化继续执行完整合并。
