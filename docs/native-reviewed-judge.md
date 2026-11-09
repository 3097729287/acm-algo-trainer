# Rust 本地审核套件

`reviewed_judge::build` 只接受 `backend/resources/native-reviewed-profiles.json` 中的十五个准确 ID，其他输入返回 `Ok(None)`。不会按题名、知识点、URL 或相似题号猜测。返回的 `ReviewedSuite` 含额外审核用例、具体覆盖范围、原 oracle 摘要、判定器与有界输出预算；原始公开样例由服务接线方加入，不重复打包。

数据来自现有 `backend/reviewed_cases.py` 的固定种子 `20261008`，规范 UTF-8/LF 摘要为 `20fd6a302157ff9b9cefb757a5bda9d287fde6d23aed37a83a07a8e8fb3b7741`。Python 只在作者导出时运行这份准确来源，生产 Rust 不执行 Python 后端、题解脚本或旧 HTTP。原 oracle 没有被冒称为全部用 Rust 重写。

十五份 gzip 共 4,724,975 B，解压数据合计 63,804,044 B；只按请求解压一份，最大一份为 32,454,996 B。每次核对压缩摘要、准确解压长度、gzip 完整性、原始摘要、题号、来源、种子、用例数和实际输入输出体积，随后释放原始解析缓冲。不常驻全部解压用例。

最大单用例输入为 32,170,013 B，保留了 `Div.4 993::H` 的 2000×2000 矩阵；它仍低于现有进程模块 32 MiB 上限。最大精确预期输出为 1,400,000 B。`ABC 478::E` 的合法大赋值按真实整数个数和位数计算，不能用预期中的 `Yes` 三字节估算。

`max_output_bytes` 是整套审核运行的累计预算：保留原样例 1 MiB 余量，再加全部额外用例的规范输出上界并按 64 KiB 向上取整，仍不超过旧 Python 运行器每用例 32 MiB 的既有上限。478D 为 2,883,584 B，478E 为 3,866,624 B，993H 为 1,310,720 B，其余为 1,114,112 B。普通样例 1 MiB、自测输入 64 KiB 的既有规则不由本模块修改。

`Checker::Exact` 沿用按空白分词比较；`Inequality` 核对 Yes/No、赋值个数、范围与每条差分不等式；`Gcd` 核对两数个数、正数范围、乘积与能达到的最大公约数。后两者均接受不同的合法构造，解析失败返回 false。乘积计算使用 u128，不把大数输出截断后再判定。

重新计算作者数据：

```powershell
python scripts/export_native_reviewed_cases_20261109.py --check
cargo test -p tobe-core --test reviewed_judge --offline
cargo test -p tobe-core --lib reviewed_judge::source_guards --offline
```

已通过 5 项公开入口/判定器测试、3 项压缩来源反例和 2 项显式执行的真实用户程序测试。十五份现有归档 C++ 程序及独立实现的 Python 用户程序，分别通过全部 314 个额外用例，共 628 次真实 Windows Job 执行；没有删除大输入或只测预期文本。C++ 接受 18 份不同于冻结输出的合法构造，Python 接受 21 份，完整输出由 Rust 判定器核对。测试源代码不导入旧生成器或后端。

完整回执见 [validation](verification/native-reviewed-judge-20261109/validation.json)、[C++](verification/native-reviewed-judge-20261109/cpp17.json) 与 [Python](verification/native-reviewed-judge-20261109/python3.json)。实际功能测试的每次子进程上限为 60 秒、1024 MB，不能把此证明当成每种语言在原站时限下通过或整套应用已经达到性能目标。测试源码及可执行文件所在临时目录均已回收。

```powershell
$env:TB_NATIVE_TEST_CPP17 = '完整的 g++.exe 路径'
$env:TB_NATIVE_TEST_PYTHON = '完整的 python.exe 路径'
cargo test -p tobe-core --test reviewed_user_programs --offline -- --ignored --test-threads=1 --nocapture
```

生产服务的队列、运行限额和结果接线由 Rust 主分支完成，本提交不更改它们，也不发放通过、经验、掌握或奖励。

新增前的检查见 [cleanup](verification/native-reviewed-judge-20261109/cleanup.json)。独立工作区中没有旧审核包、旧模块或临时编译产物可清理；原 Python oracle、原身份策略及必要历史仍有实际引用，继续保留。
