# Cheer 一键执行：港大缩微（1941 光明报）

日期：2026-07-19  
接力：cheer-only queue §1.接力 1（P0）  
完整模板：`work/domestic/hku_guangmingbao_1941_request_template_20260719.md`  
边界：mavis 不发邮件；cheer 自行发送 / 预约 / 现场

---

## 0. 30 秒摘要

| 项 | 值 |
|---|---|
| 收件 | `libspeco@hku.hk` |
| 索书号 | `HKC 951 G91 M` |
| 书目号 | `HKU_IZ21440249790003414` |
| 目标期 | **1941-09-18** / **1941-10-10** / **1941-10-16** |
| 馆藏范围 | 1941-09-18 — 12-12，Microform，官方称无缺期 |
| 候选 | `domestic:HKU:guangmingbao-1941-microform-holdings`（L2，**勿升**） |
| Primo | https://julac.hosted.exlibrisgroup.com/primo-explore/fulldisplay?docid=HKU_IZ21440249790003414&vid=HKU&lang=en_US |
| 规则页 | https://lib.hku.hk/hkspc/requesting_materials.html |

---

## 1. cheer 填空位（发送前填齐）

```
姓名：________________
机构 / 研究项目：mingmeng-history-research
拟访问日期：YYYY-MM-DD ~ YYYY-MM-DD
证件 / 读者卡：________________
邮箱：________________
电话：________________
访问方式勾选：□ 远程问询  □ 现场阅览  □ 付费复制
Circle of Friends / 日票：□ 已办  □ 待办  □ 不适用
```

---

## 2. 发送前 checklist（全勾再发）

- [ ] 收件邮箱确认为 **`libspeco@hku.hk`**（不是 `specoll@…`）
- [ ] 主题含索书号与三日期：`HKC 951 G91 M` + 09-18 / 10-10 / 10-16
- [ ] 正文含书目记录号 `HKU_IZ21440249790003414`
- [ ] 正文列已负向公开入口（避免馆方重提）：
  - [ ] NLC 民国期刊库 — 无 1941 香港《光明報》
  - [ ] 香港公共图书馆旧报库 — 无
  - [ ] CADAL — 无
  - [ ] Commons NLC 民国报纸清单 / Category:光明報 — 仅 1946–1949，无 1941
  - [ ] 维基文库 — 仅转录（LX），非原刊
  - [ ] 岭南大学 1941 剪报索引 — 13 条工运剪报，未覆盖 10-10 / 10-16
- [ ] 明确四问：① 三期是否在胶卷 / 缺期 ② 校外预约流程 ③ 拍照/复制许可与费用 ④ 成立宣言/纲领的版次页码题名
- [ ] 权利声明：学术用途、不公网放原扫、遵守馆方版权
- [ ] 申请人信息已填（无空白占位符）
- [ ] 若现场：至少提前 **3 工作日**，材料清单 ≤ **10 件**
- [ ] **未**宣称已有原刊影像；仅请求调取/确认

邮件正文：直接复制模板 §11 英文稿，填入 §1 填空位。

---

## 3. 发送后 → 回传入库步骤

| 步 | 谁 | 动作 |
|---:|---|---|
| 1 | cheer | 发送邮件 / 电话跟进；保存发送时间与 Message-ID |
| 2 | cheer | 馆方回执原文 → 转 mavis（附件原样） |
| 3 | mavis | 写入 `work/domestic/hku_guangmingbao_1941_reply_YYYYMMDD.md` |
| 4 | cheer | 现场：抄录/许可拍摄；复制件标注索书号、记录号、版次、页码、日期 |
| 5 | cheer | 回传字段（见下表）+ 文件（PDF/TIFF/照片） |
| 6 | mavis | 登记 `evidence_locator` / `evidence_note` / `rights_basis`；**仅**在「原刊影像 + 馆方授权」齐备后评估升 L1 |
| 7 | — | 在此之前候选保持 **L2 / needs_human_review** |

### 回传字段（cheer 填）

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

### 禁止

- ❌ 把目录记录 / 维基转录写成「原刊已得」
- ❌ 改 `candidates.jsonl` 证据等级（升 L1 须影像+授权齐）
- ❌ mavis 代发邮件或登录港大账号

---

## 4. 关联

- 模板 v2：`work/domestic/hku_guangmingbao_1941_request_template_20260719.md`
- 访问规则审核：`work/domestic/hku_guangmingbao_1941_access_review_20260719.md`
- 队列：`work/domestic/cheer_only_queue_20260719.md` §1.接力 1
- P0 双路径总册：`work/domestic/cheer_P0_dual_launch_20260719.md`
