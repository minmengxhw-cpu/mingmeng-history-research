# 阶段 0：国内一手史料数据契约本地审查

日期：2026-07-18

## 结论

当前契约可以作为候选目录的初始交换格式，但暂不应直接作为公开入库格式。主要阻塞点是“在线来源”和“线下馆藏”被同一组必填字段处理，以及 L0—L3 的证据要求没有在 Schema 中形成可校验约束。

外部 Grok / MiniMax 不读取工作区文档。随后已用公开字段定义和合成记录在隔离临时目录完成两次独立脱敏审查；两边都判定 `contract_ok: false`，且与本地审查的主要阻塞项一致。外部意见分别记录在 `work/domestic/grok/` 和 `work/domestic/minimax/reviews/`，不冒充对仓库代码或真实数据的审查。

## 通过项

- `candidate_id` 使用来源代码和稳定标识的组合，适合去重和后续重审。
- `repository_code`、`repository_name`、馆藏层级字段能够表达档案馆、全宗、系列和案卷的基本溯源路径。
- `access_mode`、`rights_status`、`uncertainty_note` 已覆盖登录、阅览室、线下调档、版权未知和不确定性等重要状态。
- `authenticity_level_proposed` 与 `relevance_grade_proposed` 分开，避免把“是一手材料”和“对民盟研究重要”混为一个分值。
- `checked_at` 使用日期格式，便于重查和失效提醒；`checked_by` 能区分研究、工程和人工审查来源。
- `additionalProperties: false` 有利于阻止未定义字段悄悄进入候选数据。

## 必须修订

1. **允许无 URL 的线下记录**

   当前 `source_url` 是必填且只要求非空字符串，与 `reading_room`、`offline`、`unknown` 冲突。应改为条件规则：在线或登录来源必须是合法 URL；线下或目录未公开时允许为空，但必须填写 `access_note` 和 `catalog_reference`。

2. **增加稳定馆藏标识**

   `archive_file` / `archive_item` 都是可选字段，无法保证候选能回到具体目录项。应增加 `catalog_reference`（馆藏号、目录号、索引号或“尚未公开”）及 `catalog_reference_status`，明确“已核实 / 目录中未见 / 待馆方确认”。

3. **把日期精度和未知状态分开**

   `document_date` 当前是任意字符串，无法区分精确日、月份、年份、约数和日期范围。应增加 `document_date_precision`（day/month/year/approximate/range/unknown），并禁止把推断日期写进精确日期字段。

4. **把来源证据和研究判断分开**

   `evidence_note` 目前可能同时承载目录原文、搜索摘要和研究者判断。应增加 `evidence_type`（catalogue/official_description/digital_image/printed_finding_aid/secondary_lead/unknown）及 `evidence_quote_or_locator`。二手线索只能作为线索，不能支撑 L0—L3。

5. **增加审查状态和拒收理由**

   `relevance_grade_proposed` 不能替代工作流状态。应增加 `review_status`（candidate/needs_human_review/accepted/rejected/duplicate）和 `review_note`；`exclude` 必须有排除理由，duplicate 必须指向 canonical candidate。

6. **细化权利与访问依据**

   `rights_status` 过于粗略。至少增加 `rights_basis`、`access_checked_at`、`copy_allowed`（yes/no/unknown）和 `access_note`，避免把“可看到目录”误写成“可复制或可公开”。

7. **限制 `source_url` 为 URL**

   增加 `format: uri`，同时保留单独的 `landing_page_url` / `record_url` 关系，防止把搜索页、机构首页和具体记录页混在一个字段中。

## 高风险歧义

- `L0`—`L3` 的定义在协作计划中存在，但当前 Schema 只检查枚举，不检查证据组合，因此错误分级不会被机器拦截。
- `L4` 和 `LX` 的含义没有写入 Schema 的 description；导入器可能把它们当作低等级一手材料，而不是未验证或不可用线索。
- `repository_code` 没有枚举或命名规范，可能产生同一机构多个代码，去重会失效。
- `document_type`、标签和人物字段没有规范化方案，中文异写、旧式拼音、简称和繁简体会造成检索漏召回。
- `checked_by` 只有单值，但真实记录需要“研究候选人 + 工程校验 + 人工复核”三个角色的审计链。
- `rights_status: public` 只说明权利状态候选，不等于允许下载、转载或公开展示，应避免直接映射为前台按钮。

## 阶段 1 放行条件

- 先补齐上述线下来源、日期精度、证据类型、审查状态和权利依据字段。
- 用 10 条脱敏模拟记录覆盖：在线开放、登录、馆内阅览、线下目录、日期未知、重复、二手线索、L0、L1、拒收。
- 所有模拟记录通过 Schema；L0—L3 的证据门槛由独立校验器检查，而不是仅靠模型提示。
- 任何没有稳定馆藏标识或官方来源 URL 的记录只能进入 `candidate` / `needs_human_review`，不能进入 `accepted`。
- 不修改 `data/research_index.sqlite`，不把压缩包、扫描件、PDF、图片和 OCR 原始缓存加入 Git。
- 先产出 `source_registry` 与事件覆盖表，再生成候选记录；候选记录必须能反向指向来源卡和检索路径。

## 建议的最小下一步

1. Codex 在 Schema 中补字段与条件约束。
2. 写一个只读 JSONL 校验器，输出逐条错误和分级门禁，不触碰 SQLite。
3. 先用公开机构目录建立 12—20 张来源卡，再由人工确认其中至少 3 个来源的真实访问状态。
4. 只有来源卡通过验收后，才开始生成 200 条候选；候选先落在 `work/domestic/minimax/candidates/`，不直接入库。
