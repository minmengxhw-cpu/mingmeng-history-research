# CIA 范围清理报告（2026-05-28）

> 民盟历史文献研究库 · CIA 范围二次清理 · 按用户「下一步计划书」第一步执行

## 背景

本报告记录本研究平台对 CIA 解密档案（archive.org/ciareadingroom 镜像）涉民盟范围的**二次清理**。之前已剔除 24 篇（A 朝鲜 4 / B 日本 1 / C 东南亚 10 / D 1956+ 9）。本次按用户新增的「收录边界」规则补充识别 2 篇**台湾系列名称相似但与中国民盟无关**的档案，作为 E 组剔除。

## 用户「收录边界」规则

### 保留范围

- 明确指向 **China Democratic League / Chinese Democratic League / 中国民主同盟 / 中国民主政团同盟**
- 民盟中央、民盟人物、民盟在港 / 沪 / 北平组织活动

### 谨慎保留

- South China Democratic League（华南民盟，民盟海外/南方系统）
- China Democratic League Selangor Branch（雪兰莪分支，民盟马来亚海外分支）

### 剔除前台

- **Taiwan Democratic League / New Democratic League on Taiwan**（台湾新民盟）
- **Formosan League for Re-Emancipation**（台湾再解放联盟）
- **Democratic League for Taiwan Autonomy / 台湾民主自治同盟**（与中国民盟分立的台籍政治组织）
- 朝鲜民主同盟、东南亚 / 印尼 / 马来亚名称相似但无中国民盟组织关系的材料

## 本次新剔除清单（E 组 · 台湾系列 · 2 篇）

| identifier | 英文标题 | 中译 | 剔除理由 |
|---|---|---|---|
| `cia-rdp82-00457r003500280004-3` | ARREST OF MEMBERS OF NEW DEMOCRATIC LEAGUE ON TAIWAN AND QUIESCANCE OF THE FORMOSAN LEAGUE FOR RE-EMANCIPATION | 台湾新民盟成员被捕及台湾再解放联盟的沉寂 | "台湾新民盟"与"台湾再解放联盟"均为台籍政治组织，与中国民盟（China Democratic League）分立。按收录边界剔除。 |
| `cia-rdp82-00457r009900020008-7` | CONTROL OF TAIWAN COMMUNIST PARTY AND DEMOCRATIC LEAGUE FOR TAIWAN AUTONOMY | 对台湾共产党及台湾民主自治同盟的控制 | "台湾民主自治同盟"（Democratic League for Taiwan Autonomy）是与中国民盟分立的台籍政治组织。按收录边界剔除。 |

**注**：之前的 v1 论文与 platforms.py CIA 综述误将这 2 篇列入"民盟核心活动直接情报 8 篇"，本次清理已同步删除该错误引用，并把"8 篇核心"更正为"6 篇核心"。

## 历次清理累计

| 组 | 类型 | 篇数 | 累计 |
|---|---|---:|---:|
| A | 朝鲜（"朝鲜民主同盟"名称巧合）| 4 | 4 |
| B | 日本（1948 日本共产势力）| 1 | 5 |
| C | 东南亚（缅甸 / 越南 / 印尼 / 马来亚 / 泰国共产党与华人，非民盟组织）| 10 | 15 |
| D | 1956+ 远离民盟史时段（CIA 中央情报简报系列 / 1957 亚非团结会议 / FACTBOOK 1982）| 9 | 24 |
| **E** | **台湾系列名称相似（台湾新民盟 / 台湾再解放联盟 / 台湾民主自治同盟）** | **2** | **26** |

**CIA 入库 102 篇 → 剔除 26 篇 → 前台展示 76 篇真正与中国民主同盟相关**

### 2026-05-31 本地 SQLite 兼容修正

本地数据库中部分 CIA 档案号保存为 `cia-readingroom-document-...` 形式，原脚本只按短编号匹配，导致台湾系列等记录在部分本地库中未被实际隐藏。本次已修正脚本，使其同时兼容短编号、`cia-readingroom-document-` 编号和 canonical `CIA-RDP...` 编号。

同时补充两类本地前台校准：

- **G 组重复记录**：4 条 archive.org readingroom 重复行已隐藏，保留同一 RDP 号的 canonical 核心记录。
- **F 组低相关记录**：`cia-rdp82-00457r006100040009-5`（为台湾及香港印刷共产党宣传品）当前本地无 OCR，题名也不能证明与中国民盟有实质关系，先移出前台，保留供后续重审。

执行后本地 `document_classifications` 统计为：`前台不展示 26 篇 / 前台展示 76 篇`。

## 谨慎保留清单（已审定为中国民盟海外/南方分支）

下列档案虽含"Democratic League"在异地（华南 / 香港 / 雪兰莪），但已审定为中国民盟海外/南方系统，**保留前台 + 标注海外分支**：

| identifier | 中译 | 标注 |
|---|---|---|
| `cia-rdp82-00457r000300360006-7` | 翁士良 WENG Shih-liang（华南民盟主席）赴港行程 | 华南民盟（中国民盟南方系统）|
| `cia-rdp82-00457r000300170001-3` | 华南民盟反美活动（李章达 + 丘哲签署，命令来自上海民盟总部）| 华南民盟（命令来源明确为上海中国民盟总部）|
| `cia-rdp82-00457r000100470002-1` | 马来亚陈嘉庚 + 民盟雪兰莪分支共同签署 | 民盟雪兰莪分支（中国民盟海外华侨分支）|
| `cia-rdp82-00457r000200030007-3` | 雪兰莪集会 + China Democratic League 雪兰莪分支 | 民盟雪兰莪分支 |

## 技术处理方式

不删除原始数据，仅在 `document_classifications` 表把 `grade` 改为 `'前台不展示'`：

- app.py 中所有前台路由（搜索、栏目页、列表、年表、人物索引等 20+ 处）会自动过滤
- 数据保留在 SQLite + `data/cia_meng/documents/` 子目录的 OCR 文件
- 内部检索 / 学术回溯 / 后续重审仍可访问

执行脚本：

```bash
python3 scripts/build/exclude_cia_off_topic.py
```

脚本幂等，已剔除的会跳过。本次更新含 E 组 2 篇新增。

## 同步更新

| 文件 | 改动 |
|---|---|
| `scripts/build/exclude_cia_off_topic.py` | EXCLUDE_IDENTIFIERS 加 2 条 E 组；2026-05-31 追加编号兼容、重复行隐藏、低相关条目隐藏 |
| `docs/_cia-paper.md` | 78→76，8→6（核心），2 条台湾系列加删除线 + 剔除原因标注 |
| `platforms.py` CIA highlights | 删除对 r003500280004-3 与 r009900020008-7 的引用；规模数字 78→76 |
| `docs/_cia-scope-cleanup-report.md` | 本报告（新建）|

## 你 Mac 上执行

```bash
git pull origin main
python3 scripts/build/exclude_cia_off_topic.py
```

预期输出含 2 行新剔除：

```
  ✓ [E_台湾] cia-meng:cia-rdp82-00457r003500280004-3 - ...台湾新民盟...
  ✓ [E_台湾] cia-meng:cia-rdp82-00457r009900020008-7 - ...台湾民主自治同盟...
```

## 后续

按用户「下一步计划书」的剩余 5 步：

- **第二步**：重做 CIA 研究论文（用 FRUS v3 同样的 LLM 精读方法对剩余 76 篇做精读，按"CIA 视野下的中国民盟"叙事）
- **第三步**：Wilson / HathiTrust / DRNH / Hoover 各做一篇同规格论文（优先顺序：DRNH > HathiTrust > Wilson > Hoover）
- **第四步**：新增固定页面《本库收录标准与排除标准》
- **第五步**：优化前台检索和标签（核心 / 相关 / 背景 / 前台不展示 / 误收已剔除）
- **第六步**：CIA 翻译精修（剔除完后再做）

本报告对应「第一步」完成。
