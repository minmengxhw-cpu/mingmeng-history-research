# BibTeX 引用模板 (Phase 1 sprint 39 Fri 落地)

适用: 民盟历史研究平台所有 candidate 的学术引用导出
规范: BibLaTeX 格式 (兼容 BibTeX)，民国史常见类型
版本: v1.0 (2026-07-22)
关联: docs/domestic/domestic_candidate.schema.json (citation_key 字段)

---

## 1. Entry Types

| 类型 | BibLaTeX | 适用 |
|---|---|---|
| 报纸文章 | `@article` 或 `@misc` | 大公报 / 光明報 / 文汇报 / 新民报 等 |
| 期刊文章 | `@article` | 民主周刊 / 观察 / 民憲 等 |
| 官方汇编 | `@book` | 民盟文献 / 1983 历史文献 等 |
| 档案 | `@misc` (类型 archive) | NLC / 二史馆 / 港大缩微 等 |
| 网络资源 | `@online` (BibLaTeX) 或 `@misc` | saac.gov.cn / mmzy.org.cn / wikisource 等 |
| 演讲 | `@incollection` 或 `@misc` | 闻一多 最后一次讲演 等 |
| 内部文件 | `@unpublished` | 盟中央档案 / 内部传单 等 |

---

## 2. Field 标准

| 字段 | 必填 | 说明 | 例 |
|---|:---:|---|---|
| `author` | 视 | 机构 = `{corporate}`; 个人 = `{family, given}` | `{{中国共产党}}` / `{Zhang, Lan}` |
| `title` | ✓ | 题名 | `最后一次讲演` |
| `date` | 视 | ISO 8601: `1947-11-06` / `1946` / `1947-11` | `1947-11-06` |
| `journaltitle` | 视 | 报刊名 (报纸 = `journaltitle`, 期刊 = 同) | `大公报` |
| `issue` / `number` | 视 | 期号 | `新一號` / `vol. 3, no. 11` |
| `pages` | 视 | 页码 / 版次 | `2` (第 2 版) / `299-310` |
| `publisher` | 视 | 出版社 / 报社 | `群言出版社` / `大公报馆` |
| `location` | 视 | 出版地 | `北京` / `香港` |
| `url` | 视 | 在线 URL (如有) | `https://...` |
| `urldate` | 视 | URL 访问日期 | `2026-07-21` |
| `note` | 视 | 备注 (OCR 置信度 / 影印件说明) | `OCR partial, 人工校对` |
| `keywords` | 视 | 关键词 | `民盟, 1947, 解散` |

---

## 3. 5 个示例

### 3.1 报纸文章 (大公报 1947-11-06)

```bibtex
@misc{mm1947-dagongbao-1106-01,
  author       = {{大公报馆}},
  title        = {民盟宣布解散},
  date         = {1947-11-06},
  journaltitle = {大公报},
  series       = {天津版},
  number       = {第 2 版},
  url          = {https://www.gxmm.gov.cn/index/index/artical/id/7063.html},
  urldate      = {2026-07-21},
  note         = {转录自广西民盟官网转载, 影印件存 press\_scans/},
  keywords     = {民盟, 1947, 解散, 大公报, 天津},
}
```

### 3.2 期刊文章 (民宪 1944)

```bibtex
@article{mm1944-minxian-v1n9-01,
  author       = {{中国民主同盟}},
  title        = {民主与反民主的斗争},
  date         = {1944-11-20},
  journaltitle = {民宪},
  volume       = {1},
  number       = {9},
  pages        = {1--8},
  publisher    = {中国民主同盟},
  location     = {昆明},
  url          = {https://commons.wikimedia.org/wiki/File:NLC404-00J001436-85449\_民憲\_第一卷第九期.pdf},
  urldate      = {2026-07-21},
  note         = {Wikimedia Commons NLC 扫描 PDF, 第 1 卷第 9 期},
  keywords     = {民盟, 1944, 民宪, 民主, 改组},
}
```

### 3.3 官方汇编 (1983 历史文献)

```bibtex
@book{mm1983-historical-docs,
  author       = {{中国民主同盟中央委员会}},
  title        = {中国民主同盟历史文献},
  date         = {1983},
  publisher    = {文史资料出版社},
  location     = {北京},
  pages        = {1--480},
  note         = {1941-1949 全文文献汇编, 含 1941 成立宣言 / 1944 改组 / 1945 一大 / 1947 解散原始印本},
  keywords     = {民盟, 历史文献, 1941-1949, 汇编},
}
```

### 3.4 档案 (NLC 缩微 1941 光明報)

```bibtex
@misc{mm1941-gmbao-10-10-nlc-microform,
  author       = {{中国民主政团同盟}},
  title        = {中国民主政团同盟成立启事 (《光明報》1941-10-10 转载)},
  date         = {1941-10-10},
  howpublished = {NLC 缩微胶卷 HKC 951 G91 M},
  organization = {国家图书馆 (National Library of China)},
  location     = {北京},
  url          = {https://www.nlc.cn/},
  urldate      = {2026-07-21},
  note         = {1941-10-10 / 10-16 / 10-28 香港《光明報》原刊缩微; cheer-only 接力 1 待办 (港大 Special Collections)},
  keywords     = {民盟, 1941, 光明报, 成立, 香港, 缩微},
}
```

### 3.5 演讲 (闻一多 最后一次讲演)

```bibtex
@misc{mm1946-lst-speech-1946-07-15,
  author       = {{闻一多}},
  title        = {最后一次讲演},
  date         = {1946-07-15},
  howpublished = {李公朴先生死难经过报告会, 云南大学至公堂},
  location     = {昆明},
  url          = {https://baike.baidu.com/item/最后一次讲演/5722557},
  urldate      = {2026-07-21},
  note         = {何丽芳 1946-07-15 速记; 1946-07-21 《学生报》第三版首次刊发; 同年收录《闻一多全集·第二卷》(湖北人民出版社 1993 / 三联书店 1982)},
  keywords     = {闻一多, 1946, 李公朴, 追悼会, 演讲, 昆明, 民主},
}
```

---

## 4. citation_key 生成规则

格式: `<source_code>-<event_code>-<date>-<n>`

| 段 | 来源 | 例 |
|---|---|---|
| `source_code` | 资料源缩写 (小写) | `mm` (民盟史料) / `gmbao` (光明报) / `dagongbao` (大公报) |
| `event_code` | 事件年-月-编号 | `1947-11` (解散) / `1944-09` (改组) / `1941-10` (成立) |
| `date` | 资料形成日期 (短) | `1106` / `v1n9` (期刊卷期) |
| `n` | 同 source+event+date 下的编号 (2 位) | `01` `02` `03` |

**例**:
- `mm1947-11-1106-01` = 1947-11-06 大公报第 1 篇
- `mm1941-10-10-01` = 1941-10-10 光明报第 1 篇
- `mm1944-09-v1n9-01` = 1944-09 民宪 v1n9 第 1 篇

**冲突处理**:
- 如同 key 已被占用, 末尾 `_alt` `_alt2` 区分
- 严禁中文 / 空格 / 特殊字符
- 全小写

---

## 5. 自动化导出 (mavis 后续可写)

```python
# scripts/domestic/export_bibtex.py (Phase 1 sprint 40 待写)
# 输入: data/domestic/candidates.jsonl + schema v2 citation_key 字段
# 输出: data/domestic/citations.bib
# 命令: python3 scripts/domestic/export_bibtex.py > data/domestic/citations.bib
```

每个 candidate 1 个 entry，类型 + 字段按 §1/§2 自动映射。

---

## 6. 引用规范 (芝加哥/MLA 平行)

| 规范 | 简注 |
|---|---|
| **Chicago** | 见 `chicago_template_20260722.md` |
| **MLA** | MLA 9th, 报刊: 作者. "Title." *Newspaper*, Date, p. X. URL. |
| **APA** | APA 7th, 报刊: Author, A. (Year, Date). Title. *Newspaper*, p. X. URL |
| **民国引文** | 见 `minguo_quote_template_20260722.md` (民国史常见规范) |

---

## 7. 校验

每个 entry 必须满足:
- ✓ `citation_key` 全局唯一 (在 `data/domestic/citations.bib` 内)
- ✓ 必填字段齐全 (按 entry type)
- ✓ 日期 ISO 8601
- ✓ URL 协议 https (如有)
- ✓ 中文字符用 `{{...}}` (BibLaTeX 防止大小写转换)

---

版本: v1.0 (2026-07-22)
作者: mavis
下次更新: Phase 4 平台化时 (sprint 47-48)
