# 浏览器提交准备

适用于 TB 0.10.11。本机版本是否已打包、GitHub 是否已发布，以当前更新记录为准。

TB 账号和竞赛平台账号分别登录。原站提交需要在同一个 Edge 或 Chrome 用户配置中安装“TB 浏览器连接”，并登录要使用的平台。不要使用无痕窗口。工作台缺少准备条件时会显示提示；点“查看准备说明”即可打开同一份内置指引。四个平台准备完成后，这条提示自动隐藏。

## 1. 安装并启用扩展

在内置说明选择浏览器，点击“打开扩展管理”。也可以在 Edge 地址栏输入 `edge://extensions`，Chrome 输入 `chrome://extensions`。开启开发人员/开发者模式，点击“加载解压缩的扩展程序”，选择 TB 显示的扩展文件夹。可以点击“打开扩展文件夹”或复制路径；选择包含 `manifest.json` 的目录。

确认“TB 浏览器连接”已启用。安装过旧版本时，点击它的“重新加载”，再刷新原站页面。步骤参考 [Microsoft Edge 官方说明](https://learn.microsoft.com/en-us/microsoft-edge/extensions/getting-started/extension-sideloading)、[Chrome 官方说明](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked)。

## 2. 登录原站

使用内置说明的登录按钮，可在所选浏览器打开原站。先登录要提交的平台即可。

| 平台 | 登录入口 |
| --- | --- |
| Codeforces（CF） | https://codeforces.com/enter |
| AtCoder | https://atcoder.jp/login |
| 牛客 | https://ac.nowcoder.com/login |
| 洛谷 | https://www.luogu.com.cn/auth/login |

在原站完成密码、验证码和安全验证。TB 不填写原站密码。“登录状态待确认”表示当前信息不足；它不等同于退出登录。遇到提交页验证时，在题目工作台点“在浏览器查看”，完成验证后再回 TB。

## 3. 回到 TB 检测

保持浏览器打开，登录后状态会自动更新；也可以点击“重新检测浏览器准备”。该平台显示“已登录”后，再回题目点击“提交”；检测和登录不会自动发送代码。

使用 CF、AtCoder 时保持 Edge 或 Chrome 打开，TB 优先复用该浏览器的原站会话。浏览器已经登录时，TB 不会仅因旧同步状态或缓存为空就要求再次登录。提交时仍以原站账号、语言和验证状态为准。

AtCoder 同一道题已经打开且没有代码草稿的提交页可直接复用，已完成的验证也会保留。原站仍要求验证时，“在浏览器查看”会打开本次提交使用的同一页；完成后回到 TB 点击提交即可，不必退出题目再进入。浏览器提交页中已有的代码草稿不会被覆盖。

其他平台完成登录同步后可以关闭浏览器，TB 使用已缓存的登录继续提交。浏览器关闭和扩展未安装分别显示；缓存过期、退出原站或登录失效时，按本说明重新登录并检测。
