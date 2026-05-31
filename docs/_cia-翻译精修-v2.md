# CIA 译文 LLM 精修 v2 报告（2026-05-28）

> 民盟历史文献研究库 · CIA 翻译精修 · 按「下一步计划书」第六步执行（剔除完成后再做）

## 一、背景与动机

CIA 译文此前经过两轮处理：

1. **2026-05-16 第一轮 LLM 复审**：用 `deepseek-chat` + 增强 prompt + 术语表对 61 篇 CIA 译文做复审，状态从 `machine-draft` 升级到 `machine-reviewed`。但当时复审覆盖了后来被判定为离题的档案，且 `deepseek-chat` 已于 2026-07 弃用。
2. **正则水印清理**：`refine_cia_translation_residue.py` 做 OCR 噪声（CIA-RDP 编号 / 25X1A / Approved For Release 等）+ 约 50 个硬编码威氏拼音人名的字符串替换。

第一轮复审报告显示，仍有约 23 篇存在残留质量问题，其中**名单类档案**（委员名单 / 职务名单）问题最严重——译者对大量威氏拼音人名"放弃转写、保留英文"，造成"残留英文片段过多"。例如 `LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE`（1950-07-12）单篇有 **353 处**英文片段残留。

2026-05-28 完成 CIA 范围二次清理（剔除 26 篇离题档案，前台保留 **76 篇**）后，本轮精修：

- **只针对保留的 76 篇**（不再在已剔除的 26 篇离题档案上浪费算力）
- 用新模型 **`deepseek-v4-flash`** 替代弃用的 `deepseek-chat`
- 重点攻坚名单类档案的"威氏拼音人名残留"问题

## 二、精修方法

**脚本**：`scripts/build/refine_cia_translations_llm.py`

**模型**：DeepSeek v4-flash（temperature=0.2, max_tokens=3000, thinking=disabled）

**输入**：每页 = 英文 OCR 源文 + 现有中文初稿 + 术语表节选（民盟史最相关 120 条）

**精修规则**（system prompt 强制）：

1. 彻底删除 OCR 噪声与 CIA 元数据水印（CIA-RDP 编号 / 25X1A / Approved For Release / CONFIDENTIAL / 被切碎的 S-E-C-R-E-T / NO. OF PAGES / DATE DISTR / THIS IS UNEVALUATED INFORMATION 等）
2. 残留英文人名按威氏拼音规则译成标准中文，民盟核心人物用固定对照表（张澜/罗隆基/章伯钧/沈钧儒/黄炎培/张君劢/左舜生/梁漱溟/张东荪/史良/张申府等），无把握的音译后加"（音译）"
3. 机构 / 术语按术语表统一（Democratic League / Chinese Democratic League / China Democratic League → 中国民主同盟）
4. 名单类档案逐人译出、保留条目结构（a/b/c、主席/副主席/委员），不遗漏人名
5. 只精修不增删事实，不补档案外背景

**两种运行模式**：

- **DB 生产模式**（默认）：逐页取 EN 源文 + 中文初稿 → LLM 精修 → 写回 `translations` 表，状态升级 `machine-reviewed-v2-cia-2026-05-28`，更新 FTS。**幂等**（已 v2 的页跳过），产出 `data/cia_translation_refine_v2_report.json`。
- **OCR 演示模式**（`--demo-from-ocr`）：不连数据库，直接对 OCR 整篇精修，输出预览样本，用于在无 DB 环境验证精修质量。

## 三、演示精修结果（OCR 模式，4 篇最严重名单档案）

对 4 篇"残留英文片段过多"的民盟核心名单档案做演示精修，残留英文片段消除效果：

| 档案 | 日期 | 英文片段（前→后）| OCR 噪声（前→后）|
|---|---|---:|---:|
| LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE | 1950-07-12 | 353 → **0** | 28 → **0** |
| MINISTERS AND DEPUTY MINISTERS OF CENTRAL PEOPLE'S GOV | 1949-12-02 | 423 → **0** | — |
| MEMBERS OF CULTURAL AND EDUCATIONAL COMMISSION | 1949-11-28 | 222 → **0** | — |
| SUMMER TEACHERS' CLASSES SPONSORED BY CHINA DEMOCRATIC LEAGUE | 1951-08-08 | 97 → **4** | — |

演示样本全文见 `docs/cia-refine-samples/`（4 篇中英对照 + 精修译文）。

**精修质量示例**（`LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE`，1950-07-12，民盟中央常委会任命的新委员）：

- 民盟核心人物正确转写：章伯钧、梁漱溟、雷洁琼、林汉达、吴晗、潘光旦、严景耀、曾昭伦、彭文应、刘思慕
- 华南民盟主席 **李章达** 正确识别
- 委员会结构完整保留：财务委员会 / 海外事务委员会 / 秘书 / 联络委员会 / 工商委员会 / 宣传委员会，南方总支部 / 广东省支部 / 香港九龙支部 / 上海支部 / 南京支部各级官员
- 无把握的人名统一标注"（音译）"，便于人工最后审定

## 四、生产环境运行状态核查

**2026-05-31 本地核查结论**：当前 GitHub 版本已经具备 v2 精修脚本和 4 篇演示样本，但本地 `data/research_index.sqlite` 中尚未发现全量 v2 写回记录。

- `translations.status` 中未出现 `machine-reviewed-v2-cia-2026-05-28`
- `translations.translator` 中未出现 `deepseek-v4-flash-2026-05-28-cia-refine`
- 本地未发现 `data/cia_translation_refine_v2_report.json`

因此，本阶段应表述为：**CIA v2 精修流程与样本已完成，76 篇全量落库尚待执行**。正式执行需具备 `DEEPSEEK_API_KEY` 与可用网络；执行后再以报告 JSON 和数据库状态作为完成依据。

## 五、生产环境运行命令（在有数据库与 API Key 的环境执行）

```bash
export DEEPSEEK_API_KEY=sk-xxxx
cd <项目根目录>

# 全量精修保留的 76 篇 CIA 译文（幂等，可中断续跑）
python3 scripts/build/refine_cia_translations_llm.py --parallel 4

# 仅预览最严重名单档案（无需数据库）
python3 scripts/build/refine_cia_translations_llm.py --demo-from-ocr \
  --ids CIA-RDP82-00457R005200480001-5,cia-rdp80-00809a000600270115-4
```

运行后：

- `translations` 表对应页 `text` 更新为精修译文，`status='machine-reviewed-v2-cia-2026-05-28'`，`translator='deepseek-v4-flash-2026-05-28-cia-refine'`
- 同步更新 `translations_fts` 全文索引
- 产出 `data/cia_translation_refine_v2_report.json`（逐页 before/after 残留统计）
- 之后重跑 `scripts/build/build_translation_quality_report.py` 可看精修后质量提示清单

## 六、认识论声明

精修后的译文仍是**机器翻译**（v4-flash 精修，非人工逐句校订）。其中：

1. 民盟核心人物（约 30 人）译名已用固定对照表，可靠
2. 其他威氏拼音人名为机器音译，标注"（音译）"，**人名的最终审定仍需人工核对原档**
3. 名单类档案的人名转写已大幅改善，但音译人名的准确性以"（音译）"标记为限，不应作为人名考证的最终依据
4. 如需达到 FRUS 同等的 `human-reviewed` 等级，需在 `/review/<page_id>` 校订页人工逐篇精修

## 七、同步文件

| 文件 | 改动 |
|---|---|
| `scripts/build/refine_cia_translations_llm.py` | 新建 LLM 精修脚本（DB 模式 + OCR 演示模式）|
| `docs/cia-refine-samples/*.md` | 4 篇演示精修样本（中英对照）|
| `docs/_cia-翻译精修-v2.md` | 本报告 |

本报告对应「下一步计划书」第六步的**流程与样本验证**；截至 2026-05-31 本地核查，76 篇全量精修落库尚未完成。
