# 国内研究平台运行态验收（2026-08-23）

## 结论

当前 checkout 的本地服务已在 `127.0.0.1:8765` 启动，三条核心真实 HTTP 路径均返回 `200`。平台运行态可用，但内容状态仍为 `OPEN_PRIMARY_GAPS`，运行成功不等于国内一手证据已经闭环。

## 验收证据

| 路径 | HTTP | 响应大小 | 关键结果 |
|---|---:|---:|---|
| `/domestic/workbench` | 200 | 26,546 bytes | 国内研究入口可打开；显示 2 个待接收原件目标、0 个 incoming 文件、0 个映射、2 个 `WAITING_FOR_LOCAL_ORIGINAL` |
| `/research/parity` | 200 | 27,104 bytes | 国内问题路径 36/36、双侧专题路径 9/9；一手闭环 0/9；内容状态 `OPEN_PRIMARY_GAPS` |
| `/research/domestic-1941-formation/packet` | 200 | 60,254 bytes | 1941 成立专题研究包可打开；显示 `primary evidence partial`、原始宣言图像/档案 ID/版本仍待补，不复制正文或 OCR |

三条响应均未发现 `Traceback`、`Internal Server Error`、`/Users/`、`/private/` 或 `/tmp/` 路径泄露。

## 复现命令

```bash
curl -sS -o /tmp/domestic_workbench.html -w 'workbench HTTP %{http_code} bytes %{size_download}\n' \
  http://127.0.0.1:8765/domestic/workbench
curl -sS -o /tmp/research_parity.html -w 'parity HTTP %{http_code} bytes %{size_download}\n' \
  http://127.0.0.1:8765/research/parity
curl -sS -o /tmp/research_packet.html -w 'packet HTTP %{http_code} bytes %{size_download}\n' \
  http://127.0.0.1:8765/research/domestic-1941-formation/packet
```

本次检查只执行 GET 请求，没有写入数据库、修改正文或改变证据等级；服务仅绑定本机回环地址，不代表已公开上网。

## 当前边界

- 国内九专题仍为 `9/9 research_usable_with_boundaries`、`0/9 research_ready`，9 个主证据目标保持开放。
- 1941-10-10 成立宣言原刊、1947-10-27 政府公函和 1947-11-06 民盟总部原始公告仍须通过授权原件接收流程进入 `data/domestic/raw/authorized_originals/incoming/`，不能用报刊、汇编、转录或学术文章替代。
- 当前授权原件接收审计为 `incoming_file_count=0`、`mapping_count=0`；浏览器内资料库仍受本机客户端拦截，未绕过访问控制。
