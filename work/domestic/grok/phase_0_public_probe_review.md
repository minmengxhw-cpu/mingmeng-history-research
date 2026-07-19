# Grok 阶段 0 脱敏契约审查

日期：2026-07-18  
模型：grok-4.5-build  
输入边界：仅通用字段、公开的 L0—LX 定义和模拟测试要求；临时目录运行，未读取项目仓库或私有数据。

## 结论

`contract_ok: false`

Grok 将阻塞问题归纳为五类：

1. 候选状态与验收状态没有分离；
2. 访问条件与再利用权利没有分离；
3. 在线/线下、原件/替代件、目录页/内容页没有分离；
4. 证据与研究推断仅靠自由文本，无法机器校验；
5. 只有 `*_proposed`，缺少复核后的冻结等级。

## 建议字段

- `candidate_status`
- `authenticity_level_accepted`
- `relevance_grade_accepted`
- `medium`
- `online_availability`
- `reuse_rights`
- `rights_basis`
- `sensitivity_class`
- `evidence_basis`
- `field_provenance`
- `inference_flag`
- `source_url_role`
- `check_outcome`

## 关键条件规则

- 在线存在内容、替代件或目录时，URL 必须标明角色；
- L0 必须具备权威机构和馆藏层级定位，并明确证据来自原件或目录；
- L2 必须包含汇编书目信息与页码；
- L3 必须包含报刊日期及卷期或版页定位；
- 推断字段必须有不确定性说明和字段级来源；
- 只有验收状态为 accepted 且复核结果为 pass 时，才允许写入最终等级。

## 运行结果

任务正常结束，返回 10 条完整模拟测试用例；未授予写入项目或读取项目文件的权限。
