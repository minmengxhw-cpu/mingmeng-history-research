# 续作：既有原刊文章级页界拆分

日期：2026-07-19  
基线起点：Sprint38 收口后 348 候选 / 160 accepted  
本轮终点：见校验输出  

## 原则

- 只拆题名、作者、日期、页界可目视确认的文章  
- 不自动 `accepted`  
- 不把 OCR 当正式引文  
- 不触碰 cheer-only 硬缺口原件虚报  

## 新增 4 条 L1 / needs_human_review

| candidate_id | 题名 | 作者 | 日期 | 页界 | 事件 |
|---|---|---|---|---|---|
| `...v1n1-refute-hu-shi-gaoji` | 駁胡適《國際形勢裏的兩個問題》 | 高集 | 1948-03-01 | PDF 6—8 | 1948 |
| `...v1n12-three-premises-li-xiangfu` | 三個前提與五項原則 | 李相符 | 1948-08-16 | PDF 3—5 | 1948 |
| `...1947-12-congratulate-second-plenum-editorial` | 祝民盟二中全會 | 《光明報》社 | 1947-08-08 | PDF 第2页 | 1947（机关报语境） |
| `...1947-issue22-fight-for-human-rights-editorial` | 為爭取人權而奮鬥 | 《光明報》社 | 1947-08-01 | PDF 第2页 | 李闻特辑 |

### 本地页图

- `work/domestic/guangmingbao_1948_1949/v1n1_pages/page-06.png`—`08.png`（+09 边界）  
- `work/domestic/guangmingbao_1948_1949/v1n12_pages/page-03.png`—`05.png`  
- `work/domestic/continue_pages/1947_12/`（整期 16 页）  
- `work/domestic/continue_pages/1947_22/page-01.png`—`02.png`  

### 备注

- 《祝民盟二中全會》：报面 1947-08-08；一届二中全会会期为 1947-01，本稿不作会期臆测，仅登记社论。  
- 封面目录另有胡愈之《民盟二中全會與國內局勢》等，**正文页界未在本轮锁定**，不新建卡。  
- 新二十二號特辑内多篇纪念文仍可继续拆，本轮仅锁社论。  

## 仍不拆

- 1946 新六號首面社论（题名仍不清）  
- 五项原件硬缺口（仍 OPEN / cheer-only）  

## 校验

见阶段命令输出；预期候选 **352**，accepted **160**，来源 **88**。
