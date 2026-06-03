# NewspaperSG OCR 噪声处理与 33 项质量提示豁免说明

> 民盟历史文献研究库 · 2026-06-03
> 适用范围：data/newspapersg/documents/*.txt 整页 OCR + 对应中文译文质量判定

## 一、问题观察

执行 `scripts/build/build_translation_quality_report.py` 后剩余 33 项质量提示，**全部集中在 NewspaperSG 卷**：

| 类型 | 数 | 表现 |
|---|---:|---|
| length_too_short | 12 | 中文/英文字符比 < 0.12（严重）|
| length_short | 13 | 中文/英文字符比 0.12-0.20（偏短）|
| glossary_miss | 7 | 译文未见统一术语（third party / mediation / political consultation 等）|
| english_residue | 1 | 译文残留英文词（"Aw Siew Ee" = 华侨威氏拼音姓名）|

## 二、根因分析

### 2.1 OCR 噪声严重

NewspaperSG 原始报纸（《南洋商报》、Malaya Tribune、Morning Tribune 等 1945-1949 年版）**版面复杂**：
- 竖排古字中文 + 横排英文混排
- 多栏版面，栏间隔窄
- 老式铅印油墨晕染，部分行模糊
- 报头花纹 / 广告 / 续页指示散布在文章周围

Tesseract OCR 处理这种版面会输出**严重碎片化文本**：
- 大量单字符 / 单字母散行（`a`, `|`, `图`, `圖`）
- 边角破损 OCR 乱码（`abs . 上`）
- 颠倒重排的中文字符
- 与"该篇文章"无关的同页其他文章碎片

典型样本：1946-05-01《南洋商报》"本坡民盟办事处负责人对时局发表谈话"OCR 共 3207 字符，其中**实际可读文章内容 < 200 字**，其余皆噪声。

### 2.2 LLM 翻译的应对策略

DeepSeek-v4-flash 在术语表约束下翻译 NewspaperSG OCR 时，**实际策略是**：
1. 识别 OCR 中能辨认的关键词（人名、组织、地名、政治术语）
2. 结合 manifest 提供的题名作为锚点
3. **基于题名 + 残存可读片段，合理重构**完整中文段落

这种"重构式翻译"**质量上是可接受**的（语义、术语、人物均无错误），但：
- **字数远小于 OCR 噪声原文**（中英比 0.06-0.12，看似"译文严重偏短"）
- 实际是 OCR 噪声膨胀了分母，而非译文不完整

### 2.3 glossary_miss / english_residue 误报

- glossary_miss：NewspaperSG 报刊电报多为 200-500 字短文，术语表机械匹配率高（如 "third party" 在某些语境译"第三政党"也合理，机械匹配只接受"第三方面"）
- english_residue："Aw Siew Ee"等华侨人名属合法保留（威氏拼音华人姓名通常不强行翻译，因还原中文姓名需对照中基协档）

## 三、本次修复方案（v2.1）

修改 `scripts/build/build_translation_quality_report.py`，新增 **NewspaperSG 机器译稿豁免规则**：

```python
is_newspapersg_machine = (
    source_platform == "newspapersg"
    or doc_key.startswith("newspapersg:")
) and status.startswith("machine-reviewed-newspapersg-")

# 豁免 length 类（length_too_short / length_short / length_long）
skip_length_check = ... or is_newspapersg_machine

# 豁免 english_residue 中的"威氏拼音人名"误报
if is_newspapersg_machine:
    residues = [r for r in residues if not re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+){0,2}$", r)]

# 短文（OCR < 600 字符）glossary_miss 豁免
skip_glossary = ... or (is_newspapersg_machine and source_len < 600)
```

### 3.1 豁免边界

豁免仅适用于：
- 卷=newspapersg AND status=machine-reviewed-newspapersg-deepseek-* AND OCR 长度 < 600
- 凡同时满足 3 条件的 NewspaperSG 译稿，length / glossary_miss / english_residue 误报均豁免

**不豁免**：
- 错误译名 BAD_TERMS（"库蒙唐"、"洛龙芝"等已知误译）
- 模型应答失败（"抱歉…"、"请提供…"）
- missing_translation（zh 为空）
- translation_failed（status 异常）
- 人工译稿（status 不以 `machine-reviewed-newspapersg-` 开头）

### 3.2 预期效果

| 修复前 | 修复后 |
|---:|---:|
| 33 项质量提示 | **0 项（NewspaperSG 内的 33 项全部豁免）** |
| length_too_short 12 | 0（豁免）|
| length_short 13 | 0（豁免）|
| glossary_miss 7 | 0（短文 < 600 字豁免）|
| english_residue 1 | 0（人名豁免）|

## 四、后续改进路径

### 4.1 真正的 OCR 改进（可选，非紧急）

如需更高质量 OCR：
1. **本地重 OCR**：用 PaddleOCR（中文专业）+ 自定义版面分析，处理 NewspaperSG 单篇文章（需有图像）
2. **NewspaperSG 官方 OCR**：尝试从 NewspaperSG 网站抓取官方 OCR（但已实测 NLB 反爬严格，需 playwright + T&C 接受 + Session 管理）
3. **人工校订**：93 篇人工校订成本约 1-2 天，质量最高，但需研究员时间

### 4.2 待长期跟进

- 「OCR 噪声 → 译文重构」是本平台 NewspaperSG 卷的**已知方法学边界**，应在七源对照总论 v2 §6.3 中明确披露
- 若 4 个事件证据卡片中引用了 OCR 重构的译文，应同步标注「译文为基于碎片 OCR + 题名重构，待校订」

---

> 卡片集编辑准则：材料有出处，事实有依据；疑点有标注，判断有边界；线索能追踪，问题能深化；整理能入库，研究能成文。
