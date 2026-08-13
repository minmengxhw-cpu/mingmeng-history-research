# Batch 2 · 元数据统一审计报告

审计对象：689 条候选（DB 689 + staging 664 合并）

## 1. 来源机构规范化
- 代码 → 规范机构/机构类别/来源家族/权威等级 字典：86 条映射
- 未映射代码：0（全部入库，含占位码）
- 权威等级分布：{'A': 426, 'B': 194, 'C': 69}
- 来源家族分布：{'国内党政机关与档案馆': 237, '公共数字化/学术/海外': 240, '民盟自身与盟史': 130, '政协/统一战线/官方媒体': 71, '其他': 11}

## 2. 资料类型统一
- 一手/汇编/二手/待定 归类分布：{'汇编': 254, '待定': 49, '一手': 348, '二手': 38}
- 归类规则：archive_scan/press_scan → 一手原件；book_or_assembly/official_publication → 汇编；
  official_history_page/web_transcription → 二手；other → 待定

## 3. 日期规范化
- 精度分布：{'day': 479, 'year': 118, 'range': 27, 'month': 51, 'empty': 6, 'multi': 8}
- 规则：YYYY-MM-DD→day；YYYY-MM→month；YYYY→year；区间（—/–/~/至/多值）→range/multi 保留起止

## 4. 证据等级一致性
- 等级分布：{'L1': 325, 'L2': 234, 'L3': 82, 'L4': 44, 'LX': 4}
- 33 条 proposed≠accepted；accepted 为空 0 条
- 一致性异常 25 条

## 5. 质量问题清单
- 总 66 条，按字段：{'level_consistency': 25, 'date_range': 35, 'level_proposed_vs_accepted': 6}
- 详见 metadata_quality_issues.csv
