# 国内研究平台研究工作流验收（2026-08-24）

## 结论

本地服务 `127.0.0.1:8765` 已完成一次从研究问题到页级证据和研究包的只读回归。问题入口、国内检索、统一检索、专题页和研究包五条路径均返回 HTTP 200，页面保留国内外对读、页级引用入口和开放证据边界。

这证明平台工作流可用；不代表九个专题的一手原件已经全部闭环。

## 路径证据

| 工作步骤 | 路径 | HTTP | 验收标志 |
|---|---|---:|---|
| 研究问题入口 | `/research/questions` | 200 | 页面包含国内研究入口、国内—海外对读和 36 个专题研究包回链 |
| 国内限定检索 | `/domestic/search?scope=documents&q=民盟` | 200 | 页面可从国内研究平台进入，未出现服务错误或本机路径泄露 |
| 国内核心可阅库 | `/domestic/library?layer=core&q=民盟` | 200 | 文档结果可直接跳转“首张引用卡”；仅对已有 `citation_ready` 页显示该入口 |
| 统一检索 | `/search?q=民盟&platform=domestic` | 200 | 返回国内检索结果，并生成页级 citation 入口 |
| 专题页 | `/research/domestic-1945-first-congress` | 200 | 同时显示国内资料、海外对位、页级引用和研究包入口 |
| 研究包 | `/research/domestic-1945-first-congress/packet` | 200 | 研究包可打开，保留页级引用和主证据开放边界 |

上述响应均未发现 `Traceback`、`Internal Server Error`、`No such file`、`/Users/`、`/private/` 或 `/tmp/` 路径。

新增的核心可阅库入口在临时本机验证端口 `127.0.0.1:8766` 上返回 `200`，响应包含 `首张引用卡` 和 `/cite/`；临时服务已关闭，不影响默认 `8765` 服务。

2026-08-24 重新运行 36 条研究问题回归：`path_ready=36/36`、`strict_page_query=25/36`、`strict_support=36/36`、`failed_path=0`。这里的 `strict_support` 表示问题可以通过专题事件索引找到严格页级入口，不表示对应专题的主证据缺口已经关闭。

## 验收方式

```bash
for path in \
  /research/questions \
  '/domestic/search?scope=documents&q=民盟' \
  '/search?q=民盟&platform=domestic' \
  /research/domestic-1945-first-congress \
  /research/domestic-1945-first-congress/packet
do
  curl -sS -o /tmp/research-flow.html \
    -w '%{http_code} %{size_download} %{url_effective}\n' \
    "http://127.0.0.1:8765${path}"
done
```

本轮只执行 GET 请求，没有写入 SQLite、修改正文、启动 OCR 或提升证据等级；服务只绑定本机回环地址，不代表已公开上网。

## 1947 年解散前背景候选扩展

本轮从台湾国史馆公开目录核对并登记三条元数据候选，作为“解散前政治活动”时间轴的补充，而不是把国内史压缩成 1947 年 10—11 月的解散事件：

| 档号 | 日期 | 用途 | 状态 |
|---|---|---|---|
| `002-080200-00541-008` | 1947-01-09 | 民盟二中全会及 1947 年初政治活动背景 | `L2 / needs_human_review` |
| `002-080200-00536-014` | 1947-05-07 | 各党派活动及相关人物的政治环境交叉材料 | `L2 / needs_human_review` |
| `002-080200-00537-008` | 1947-09-05 | 广西民盟成员与地方政治关系背景 | `L2 / needs_human_review` |

官方目录入口：[00541-008](https://ahonline.drnh.gov.tw/index.php?act=Archive%2Fsearch%2FeyJxdWVyeSI6W3siZmllbGQiOiJfYWxsIiwidmFsdWUiOiIwMDItMDgwMjAwLTAwNTQxLTAwOCJ9XX0%3D)、[00536-014](https://ahonline.drnh.gov.tw/index.php?act=Archive%2Fsearch%2FeyJxdWVyeSI6W3siZmllbGQiOiJfYWxsIiwidmFsdWUiOiIwMDItMDgwMjAwLTAwNTM2LTAxNCJ9XX0%3D)、[00537-008](https://ahonline.drnh.gov.tw/index.php?act=Archive%2Fsearch%2FeyJxdWVyeSI6W3siZmllbGQiOiJfYWxsIiwidmFsdWUiOiIwMDItMDgwMjAwLTAwNTM3LTAwOCJ9XX0%3D)。

三条记录只保存档号、题名、日期、官方 URL 和不确定性说明；没有读取正文、下载影像、执行 OCR 或写入正式页表。同步后本地候选表为 693 条，正式数据库验收仍通过，且 `body_read=false`、`formal_db_written=false` 的检索队列边界保持不变。

## 当前边界

- 统一门禁仍为 `PASS / OPEN_PRIMARY_GAPS`。
- 国内九专题仍为 `9/9 research_usable_with_boundaries`、`0/9 research_ready`。
- 1941 成立宣言、1947 政府公函和 1947 民盟总部公告等关键原件，仍必须通过授权原件接收、页身份复核和正式入库流程关闭缺口。
