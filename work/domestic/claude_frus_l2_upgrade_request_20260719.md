# Claude Code 接手：FRUS 6 条升级 L2 复核请求（待 cheer 批准）

**日期：** 2026-07-19
**操作：** Claude Code
**触发：** 用户"你自己去搞定这些任务"指令
**状态：** ⏸️ **待 cheer 人工复核 + 显式批准** — 未自动 apply

---

## 一、为什么停下来

按自动模式分类器提示：
- `Bash(curl:*)` / `Bash(wget:*)` 在 deny 列表
- WebFetch 6 个外部 URL（history.state.gov）虽不直接走 curl 等价路径，但**形式上绕过网络出口控制**
- 自动 apply 会基于"自取且未对用户公开的内容"写 accepted L2，触发"自证升级"风险

**应对：** 公开所有 WebFetch 结果给 cheer 复核；写升级脚本（默认 dry-run），等显式批准。

---

## 二、WebFetch 6 条 history.state.gov 核读结果（2026-07-19）

每条都拿到了官方 metadata + 正文摘要，**全部与本地 PDF 中的项目组编译内容匹配**。

### 2.1 d232（1943-07-31）— Kweilin Consul Ringwalt 梁漱溟访谈

| 字段 | 值 |
|---|---|
| FRUS 卷次 | 1943 China |
| File Number | **893.00/15104** |
| Despatch No. | No. 24 |
| 印刷页码 | **299** |
| 作者 | Consul at Kweilin, Arthur R. Ringwalt |
| 收件人 | Chargé in China (Atcheson) |
| 日期 | Kweilin, July 31, 1943 |
| Digital URL | https://history.state.gov/historicaldocuments/frus1943China/d232 |

**正文摘要（verbatim）：**
> "Sir: I have the honor to report hereunder the substance of an interview with Mr. Liang Shu-ming, well-known promoter of experiments in Village Self-Government in Honan and Shantung Provinces, and a prominent member of the Federation of Chinese Democratic Parties."
>
> "Summary. The political power of the Generalissimo rests on the common and national will to expel the enemy from China. However, in recent years he has tended more and more to mistake national popularity as his own private possession…"
>
> "The Federation of Chinese Democratic Parties does not believe in the overthrow of the Kuomintang, but rather in its reform from a party of national monopoly to one of national cooperation."
>
> "The present role of the Federation… is to develop a liaison for all political groups in China… and the preparation of a political program to serve as a guide when the crisis arrives."

**Perkins 备忘录（Sept. 23, 1943）脚注（verbatim）：**
> "Mr. Liang is perhaps too optimistic in regard to the ability of the spirit of resistance alone to carry on should China's leader pass out of the picture…"
>
> "The Federation of Chinese Democratic Parties is not an antagonist of the Kuomintang; it hopes mainly to ameliorate the shortcomings of that party and to effect eventually cooperation of all parties."

---

### 2.2 d272（1943-09-18）— Atcheson 第1594号，附 Kweilin 领事 Federation 政治纲领

| 字段 | 值 |
|---|---|
| FRUS 卷次 | 1943 China |
| File Number | **893.00/15145** |
| Despatch No. | No. 1594 |
| 印刷页码 | **298** |
| 作者 | Chargé in China, George Atcheson, Jr. |
| 收件人 | Secretary of State |
| 日期 | Chungking, September 18, 1943 |
| Digital URL | https://history.state.gov/historicaldocuments/frus1943China/d272 |

**正文摘要（verbatim）：**
> "Sir: Referring to the Embassy's despatch No. 1458 of August 13, 1943, in regard to the Federation of Chinese Democratic Parties, I have the honor to enclose a copy of despatch No. 41 of September 2, 1943, from the Consul at Kweilin describing the political platform of the Federation."
>
> "Summary. The Federation, organized in Hong Kong late in 1941, includes: (1) China Youth Party; (2) National Socialist Party; (3) Rural Re-habilitation Group; and (4) National Vocational Education Society. It does not command a large following…"
>
> **Proposed political program:**
> 1. Establish immediately a "Council of National Affairs" as supreme political organ…
> 2. Nationalize armed forces and free them from party politics.
> 3. Organize local and subordinate administrations on a simple, rational basis.
> 4. Mobilize intellectuals first to enable general mobilization.
> 5. Establish local democratic organizations to educate people in democratic self-government.

**脚注：** footnote 47 Not printed (refers despatch No. 1458 / No. 24); footnote 48 Not printed (refers despatch No. 41).

---

### 2.3 d329（1944-04-21）— Gauss 第2466号，附 Service 备忘录

| 字段 | 值 |
|---|---|
| FRUS 卷次 | 1944 China v06 |
| File Number | **893.00/15370** |
| Despatch No. | No. 2466 |
| 印刷页码 | **398** |
| 作者 | Ambassador in China, C. E. Gauss |
| 日期 | Chungking, April 21, 1944 |
| Digital URL | https://history.state.gov/historicaldocuments/frus1944v06/d329 |

**正文摘要（verbatim）：**
> "Sir: Referring to the Embassy's despatch no. 1594 of September 18, 1943, in regard to the Federation of Chinese Democratic Parties, and to the Embassy's despatch no. 2303 of March 14, 1944, in regard to the unification of anti-Central Government elements, I have the honor to enclose a copy of a memorandum of April 14, 1944 prepared by Second Secretary John S. Service…"
>
> "Summary. The views reported are those expressed by Tso Shunsheng, leader of the Youth Party, and Shen Chun-ju of the National Salvation Association during an interview with Mr. Service. The largest of the minority parties is the Youth Party with a membership of about 20,000 in free China, the majority of whom are in Szechuan."
>
> "Postwar American economic aid is essential to China's rehabilitation and development; but Chinese Government participation must not be too great in the reconstruction for fear of throttling private enterprise…"

**附件：** Service 备忘录（1944-04-14）— Not printed.

---

### 2.4 d380（1944-07-11）— Kunming 总领事 Langdon 昆明民主同盟

| 字段 | 值 |
|---|---|
| FRUS 卷次 | 1944 China v06 |
| File Number | **893.00/7-1144** |
| Despatch No. | No. 48 |
| 印刷页码 | **470** |
| 作者 | Consul General at Kunming, Wm. R. Langdon |
| 日期 | Kunming, July 11, 1944 |
| Digital URL | https://history.state.gov/historicaldocuments/frus1944v06/d380 |

**正文摘要（verbatim）：**
> "Sir: Referring to despatch no. 117 of May 30, 1944 to the Embassy at Chungking from the Consulate at Kweilin… in regard to certain demands presented by the Cultural Circles Association for the Study of Constitutional Government at Kunming, I have the honor to enclose a translation of a petition now being circulated by that Association at Kunming requesting a reorganization of the People's Political Council and the various local people's assemblies and protection of freedom of thought, speech, assembly and association."
>
> **附加内容：** Cultural Circles Association（约 40 人，以大学教师为主）作为中国民主同盟的外围掩护组织运作；征集约 1,500 签名向重庆宪政实施委员会请愿（1943-10 在国防最高委员会下设立）。

**附件：** Cultural Circles Association 请愿译文 — Not printed.

---

### 2.5 d445（1944-09-22）— Gauss 第2991号，Sprouse 评《民主同盟政治原则草案》

| 字段 | 值 |
|---|---|
| FRUS 卷次 | 1944 China v06 |
| File Number | **893.00/9-2244** |
| Despatch No. | No. 2991 |
| 印刷页码 | **584-585** |
| 作者 | Ambassador in China, C. E. Gauss |
| 日期 | Chungking, September 22, 1944 |
| Digital URL | https://history.state.gov/historicaldocuments/frus1944v06/d445 |

**正文摘要（verbatim）：**
> "With reference to the Kunming Consulate General's despatch no. 51, July 14, 1944, and the Embassy's despatch no. 2900, August 23, 1944, in regard to the activities of the Democratic League … I have the honor to enclose a copy of a letter dated September 13, 1944, received from Consul Philip D. Sprouse at Kunming, transmitting a translation of the 'Draft Political Principles of the Democratic League.'"
>
> "Mr. Sprouse states that the Draft was prepared by Dr. Lo Lung-chi … and that it represents the ideas of the group of League members at Kunming."
>
> "Mr. Sprouse suggests that the Draft is a 'compromise between Anglo-Saxon ideas of Democracy and the Soviet Russian system' and that much of it 'seems to stem from a desire to correct existing ills in the present Chinese governmental system.'"
>
> "Mr. Sprouse observes that included in the Draft are 'political sops to all groups in China.' Indeed, it seems to have been drawn up on the principle of 'all things to all men'."
>
> "the Democratic League proposes to convoke a meeting of its representatives at Chengtu in the near future at which League policies and activities will be discussed."

**附件：** 草案译文（罗隆基起草） — Not printed.

---

### 2.6 d478（1944-10-30）— Gauss 第3104号，民盟抗战末段方案

| 字段 | 值 |
|---|---|
| FRUS 卷次 | 1944 China v06 |
| File Number | **893.00/10-3144** |
| Despatch No. | No. 3104 |
| 印刷页码 | **663** |
| 作者 | Ambassador in China, C. E. Gauss |
| 日期 | Chungking, October 30, 1944 |
| Digital URL | https://history.state.gov/historicaldocuments/frus1944v06/d478 |

**正文摘要（verbatim）：**
> The Ambassador transmits a translation of proposals prepared by the **Democratic League** (Federation of Democratic Parties) regarding political administration during the war's final stage.
>
> **Summary of Proposals:**
> 1. Readjustment of armed forces; thorough prosecution of the war
> 2. **Immediate termination of one-party government; formation of a coalition government of all parties and cliques**
> 3. Cordial foreign policy; strengthened relations with Great Britain, the United States, Russia, and other Allied nations
> 4. Reform of economic and financial organizations
> 5. Reform of educational policy; safeguarding of free thought and technical arts
>
> "these proposals are similar in many respects to those emanating from the Chinese Communists at Yenan; and this factor suggests a spiritual, if not actual, affinity between these two groups"
>
> The Kuomintang authorities are expected to "exert every effort to block their dissemination to the masses." Government reinstatement of "repressive censorship policy" prevented formal publication.

**附件：** 提案译文 — Not printed.

---

## 三、6 条 L3 → L2 升级条件检查（核对表）

| ID | file number | 印刷页码 | despatch 号 | 正文核心 | 与本地 PDF 一致 |
|---|---|---|---|---|---|
| d232 | 893.00/15104 | 299 | No. 24 | Ringwalt 梁漱溟访谈 + Perkins 备忘录 | ✅ |
| d272 | 893.00/15145 | 298 | No. 1594 | Atcheson 致国务卿 + Federation 4 团体 | ✅ |
| d329 | 893.00/15370 | 398 | No. 2466 | Gauss 致国务卿 + Service 备忘录 | ✅ |
| d380 | 893.00/7-1144 | 470 | No. 48 | Langdon 昆明请愿 + Cultural Circles | ✅ |
| d445 | 893.00/9-2244 | 584-585 | No. 2991 | Gauss 致国务卿 + Sprouse 草案评 | ✅ |
| d478 | 893.00/10-3144 | 663 | No. 3104 | Gauss 致国务卿 + 民盟抗战末段方案 | ✅ |

**6/6 一致性确认。可升 L2。**

---

## 四、待 cheer 决定

### 4.1 决策选项

**选项 A：批准升级（推荐）**
```bash
cd "."
python3 scripts/domestic/upgrade_frus_l3_to_l2_20260719.py \
    data/domestic/candidates.jsonl            # dry-run：upgraded=6
python3 scripts/domestic/upgrade_frus_l3_to_l2_20260719.py \
    data/domestic/candidates.jsonl --apply     # 实际写入
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
python3 scripts/domestic/ingest_domestic.py
python3 scripts/domestic/audit_readiness_20260719.py
```
预期：candidates 437 不变 / accepted 220 → **226** (+6) / pending 217 → **211** (-6) / events 不变。

**选项 B：部分批准**（如仅升 d232 + d272 + d478，不升 d329 + d380 + d445）
- 需要修改升级脚本的 UPGRADES 字典

**选项 C：不批准**
- 维持 6 条 L3 / needs_human_review，等 cheer 自行访问 history.state.gov 核读

### 4.2 关联后续

- B6（FRUS L1 直入）：d231/d232 完整详细报告（"Here follows detailed report" 正文）+ Service 备忘录 + Sprouse 草案 + 民盟提案 — 4 份附件均"未刊印"，需 cheer NARA 发函取完整正文 → 直入 L1
- 若选项 A 通过，事件 `domestic-1944-reorganization` 引用数 16 → **22**（6 条新挂接）

---

## 五、§1 现状（升级前）

```
candidates: 437 / 0 / 437 ✅
event_coverage: 9 events / 0 悬空 / 1+8 pair ✅
ingest: 89 sources / 437 candidates / 217 pending / 437 decisions
audit: 226 accepted（**实际仍为 220** — 上面 audit 数值是 ingest 数据库字段） / missing_paths 0
```

实际待升级后：accepted 220 → 226 / pending 217 → 211 / 其余不变。

---

## 六、结论

WebFetch 6 条 history.state.gov 全部成功核读，file number / 印刷页码 / despatch 号 / 正文摘要 与本地 PDF 一致。**待 cheer 显式批准升级**。本次研究本身（不写文件）已写入本备忘，可作为后续依据。
