# Cheer P0 双路径一页总册（并行启动）

日期：2026-07-19  
适用：cheer 同日并行启动 **路径 A 港大缩微** + **路径 B 二史馆 1354**  
边界：**agent / mavis / codex 不代发邮件、不登录、不预约、不付费**；cheer 自行发送与到馆  
不改：`candidates.jsonl`（升 L1 须影像 + 授权齐备后再由 mavis/codex 评估）

---

## 0. 30 秒启动

| 路径 | 一键清单 | 完整模板 | 阻塞事件 |
|:---:|---|---|---|
| **A 港大** | [`cheer_action_hku_microform_20260719.md`](cheer_action_hku_microform_20260719.md) | [`hku_guangmingbao_1941_request_template_20260719.md`](hku_guangmingbao_1941_request_template_20260719.md) | `domestic-1941-formation` |
| **B 二史馆** | [`cheer_action_shac_1354_20260719.md`](cheer_action_shac_1354_20260719.md) | [`shac_1354_request_template_20260719.md`](shac_1354_request_template_20260719.md) | `domestic-1947-illegal-dissolution` |

**D0 动作（cheer）：**

1. 填 A 清单填空位 → 复制模板 §11 英文稿 → 发 `libspeco@hku.hk`
2. 填 B 清单填空位 → 复制模板 §11 中文稿 → 发 `esg@shac.net.cn` 和/或 `84800747@shac.net.cn`（或电话 `025-84800747`）
3. 两路径各自保存发送时间 / Message-ID / 电话记录 → 回执原样转 mavis

---

## 1. 路径 A × 路径 B 对照表

| 维 | **路径 A：港大缩微** | **路径 B：二史馆 1354** |
|---|---|---|
| **目标** | 1941-09-18 / **10-10** / **10-16** 香港《光明報》缩微原刊（成立宣言 / 纲领版次页码） | **1947-10-27** 内政部宣布民盟非法 **原始公函**（全宗 1354）；备选 11 月执行/备案、公报原稿档案 |
| **机构** | HKU Special Collections | 中国第二历史档案馆（南京）**≠** 上海档案馆 |
| **联系** | 邮箱 `libspeco@hku.hk`（**勿** `specoll@…`） | 邮箱 `esg@shac.net.cn`；预约 `84800747@shac.net.cn` / `a84800747@163.com`；电话 `025-84800747`；馆办 `025-84801996` |
| **馆址 / 入口** | Primo 书目 `HKU_IZ21440249790003414`；索书号 `HKC 951 G91 M`；规则页 lib.hku.hk/hkspc | 南京市中山东路 309 号；官网 shac.net.cn |
| **现有候选** | `domestic:HKU:guangmingbao-1941-microform-holdings`（L2，**勿升**） | `domestic:MMHIST:league-banned-1947-10-27`（L2 汇编，**≠** 公函原件） |
| **已负向（勿当原件）** | NLC 民国期刊库无 1941；港公图旧报无；CADAL 无；Commons/Category:光明報 仅 1946–1949；维基文库仅 LX 转录；岭南 1941 剪报索引 13 条未覆盖 10-10/10-16 | 国府公报 **2963–2966**（及 2967/2973/2974）未见目标公文；1983《历史文献》汇编 L2；1946《民主同盟文獻》无 1947；维基转录；上档 6-5-1216 = **另一馆** |
| **期望回传** | 三期是否在卷/缺期；版次页码题名；复制许可与费用；许可影像/抄录 + SHA256 | 全宗-案卷-件号；发文日期/机关/题名；载体与许可；复制件 + SHA256；缺卷/限制备注 |
| **预计周期** | 函询约 5–7 工作日；胶卷/复制到位约 2–4 周；现场须提前 ≥3 工作日 | 函调/预约约 7–10 工作日；现场 1–2 工作日；介绍信+身份证必备 |
| **现场门槛** | Circle of Friends / 日票；材料清单 ≤10 件 | 介绍信 + 身份证 + 预约回执 |
| **独立于** | — | 上档 6-5-1216（勿顺带启动） |

---

## 2. 并行甘特式 checklist

时间轴以 cheer **D0 = 双函发出日** 计。两路径互不阻塞。

### D0 — 发函（同日并行）

| # | 路径 | cheer 动作 | 勾选 |
|---:|:---:|---|:---:|
| 1 | A | 填 [`cheer_action_hku…`](cheer_action_hku_microform_20260719.md) §1 填空位 | ☐ |
| 2 | A | 发送前 checklist 全勾（邮箱、三日期、书目号、负向六条、四问、权利） | ☐ |
| 3 | A | 发英文邮件 → `libspeco@hku.hk`；记发送时间 + Message-ID | ☐ |
| 4 | B | 填 [`cheer_action_shac…`](cheer_action_shac_1354_20260719.md) §2 填空位（含身份证/介绍信单位） | ☐ |
| 5 | B | 发送前 checklist 全勾（二史馆非上档、1354、负向公报、期望交付排序） | ☐ |
| 6 | B | 发中文邮件 → `esg@shac.net.cn` 和/或 `84800747@…` **或** 电话 `025-84800747`；记回执 | ☐ |
| 7 | 双 | 两路回执/发送记录原样转 mavis（附件不改） | ☐ |

### D+3〜D+7 — 跟催窗口

| # | 路径 | cheer 动作 | 勾选 |
|---:|:---:|---|:---:|
| 8 | A | D+5〜7 无回音 → 礼貌跟催同一邮箱；主题加 `Follow-up:` + 原 Message-ID | ☐ |
| 9 | B | D+7〜10 无回音 → 电话 `025-84800747` 或邮件跟催；确认预约单号 | ☐ |
| 10 | 双 | 任一回执到 → 当日转 mavis；另一路继续等，**不串改候选** | ☐ |

### 回传日 — 入库字段（cheer 填齐再交 mavis）

**路径 A 回传字段**

```
回传日期：
馆方联系人 / 回执方式：
三期是否存在：09-18 ____  10-10 ____  10-16 ____
缺期说明：
版次 / 页码 / 题名（逐期）：
复制许可：□ 拍照  □ 扫描  □ 付费复制  □ 仅阅览
费用与票据号：
文件路径 / 文件名：
SHA256（每文件一行）：
权利范围备注：
```

**路径 B 回传字段**

```
回传日期：
预约单号 / 回执方式：
全宗号：1354（确认/修正：____）
案卷号：
件号：
发文日期：
发文机关：
题名 / 事由：
页码（起—止）：
载体：□ 原件阅览  □ 复制 PDF  □ 复制 TIFF  □ 抄录
文件路径 / 文件名：
SHA256（每文件一行）：
复制许可与权利范围：
费用与票据号：
馆员备注（缺卷/限制/不可复制）：
```

| # | 路径 | cheer 动作 | 勾选 |
|---:|:---:|---|:---:|
| 11 | A | 上表 A 字段 + 文件齐 → 交 mavis | ☐ |
| 12 | B | 上表 B 字段 + 文件齐 → 交 mavis | ☐ |
| 13 | 双 | 现场复制件已标注：A=索书号+记录号+版次页码日期；B=全宗-案卷-件号-页码-日期 | ☐ |

---

## 3. 回传后 mavis / codex 入库步骤

| 步 | 谁 | 路径 A | 路径 B |
|---:|---|---|---|
| 1 | cheer | 回执原文 + 回传字段 + 文件 | 同左 |
| 2 | mavis | 写 `work/domestic/hku_guangmingbao_1941_reply_YYYYMMDD.md` | 写 `work/domestic/shac_1354_reply_YYYYMMDD.md` |
| 3 | mavis | 挂既有候选 `domestic:HKU:guangmingbao-1941-microform-holdings`；更新 `evidence_locator` / `evidence_note` / `rights_basis` | 挂 `domestic:MMHIST:league-banned-1947-10-27`；同上字段 |
| 4 | mavis | 每文件算 **SHA256**；路径写入 reply 与候选 note | 同左 |
| 5 | mavis | **L2 保持** 直至「原刊影像 + 馆方授权」齐 | **L2 保持** 直至「公函影像 + 馆方授权」齐 |
| 6 | mavis | 齐备后评估 **升 L1** 草案（不擅自改 production 等级） | 同左；**不**与上档 6-5-1216 混写 |
| 7 | codex | 审核 reply + 影像边界 + rights → accept / 驳回补证 | 同左 |
| 8 | mavis | accept 后写 candidates / 事件挂接 / SQLite 同步 / 校验 | 同左 |

### 禁止（双路径共用）

- ❌ agent / mavis / codex **代发**邮件、代预约、登录馆方账号
- ❌ 目录命中 / 维基转录 / 1983 汇编 / 公报负向扫描 =「原件已得」
- ❌ 无影像+授权时改 `candidates.jsonl` 证据等级
- ❌ 公报 2963–2966 未见 =「公函不存在」（仅说明该期公报未载）
- ❌ 把港大与二史馆回传字段串写进同一候选

---

## 4. 关联索引

| 文档 | 用途 |
|---|---|
| [`cheer_only_queue_20260719.md`](cheer_only_queue_20260719.md) §1.接力 1–2、§2 | 总队列与优先级 |
| [`cheer_action_hku_microform_20260719.md`](cheer_action_hku_microform_20260719.md) | A 一键执行 |
| [`cheer_action_shac_1354_20260719.md`](cheer_action_shac_1354_20260719.md) | B 一键执行 |
| [`hku_guangmingbao_1941_request_template_20260719.md`](hku_guangmingbao_1941_request_template_20260719.md) | A 模板 v2.1 |
| [`shac_1354_request_template_20260719.md`](shac_1354_request_template_20260719.md) | B 模板 v1.1 |
| [`hku_guangmingbao_1941_access_review_20260719.md`](hku_guangmingbao_1941_access_review_20260719.md) | A 访问规则审核 |
| [`roc_gazette_2964_official_scan_review_20260719.md`](roc_gazette_2964_official_scan_review_20260719.md) | B 公报 2964 负向 |
| `docs/domestic/shac_6-5-1216_finding_aid.md` | 上档备选（独立接力，非本总册） |
