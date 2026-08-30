# 国内—海外研究平台运行态验收（2026-08-24）

## 结论

本机已运行的研究服务在不重启、不写数据库的条件下通过核心页面 HTTP 验收。国内专题、海外来源和国内—海外对读入口均可访问；内容证据状态仍按门禁真实显示为 `OPEN_PRIMARY_GAPS`，不因页面可用而提前宣称一手原件闭环。

## 实测结果

测试地址：`http://127.0.0.1:8765`。响应体均为 HTML，未执行写操作。

| 路径 | HTTP | 响应大小 | 实测耗时 | 用途 |
|---|---:|---:|---:|---|
| `/` | 200 | 15,878 bytes | 0.265 s | 项目首页 |
| `/domestic` | 200 | 51,216 bytes | 0.951 s | 国内资料总览 |
| `/domestic/workbench` | 200 | 26,546 bytes | 3.617 s | 国内专题工作台 |
| `/research/parity` | 200 | 27,104 bytes | 2.069 s | 国内—海外能力对齐 |
| `/research` | 200 | 27,838 bytes | 1.573 s | 研究入口 |
| `/sources/frus` | 200 | 31,297 bytes | 0.004 s | 海外 FRUS 来源页 |

页面内容信号同时包含国内/海外入口；`/research/parity` 渲染出的回归状态为：国内问题路径 `36/36`、专题路径 `9/9`、一手闭环 `0/9`、内容状态 `OPEN_PRIMARY_GAPS`。

## 解释与边界

- 三个较重页面在 2 秒短超时下可能未完成，但在 30 秒只读验收窗口内均返回 200；当前实测不是路由失败。
- 运行态通过只证明本机服务能展示已登记的研究包和证据边界，不证明 1941/1947 等专题的一手原件已经取得。
- `data/domestic/raw/authorized_originals/incoming` 当前仍为空，P0 接收报告为 `WAITING_FOR_LOCAL_ORIGINAL: 2`。
- 下一次内容收口仍必须遵循：文件 SHA256 → 显式目标/页映射 → 页身份复核 → 必要时定向 OCR → dry-run → 备份 → 正式入库 → 全门禁。

## 可复现命令

启动本地服务后，用以下只读脚本复验核心路径：

```bash
python3 - <<'PY'
from time import perf_counter
from urllib.request import urlopen

base = "http://127.0.0.1:8765"
paths = ["/", "/domestic", "/domestic/workbench", "/research/parity", "/research", "/sources/frus"]
for path in paths:
    started = perf_counter()
    with urlopen(base + path, timeout=45) as response:
        size = len(response.read())
    print(path, response.status, size, f"{perf_counter() - started:.3f}s")
PY
```
