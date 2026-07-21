# Claude 批次 F 收口报告（saac.gov.cn 剩余 25 件 + Wikimedia 民盟人物 8 条 / 2026-07-20）

## 一、§1 四校验终态

```
candidates:     571 / 0 / 571 ✅
event_coverage: 571 / 9 / 0 missing / 1 pair_available + 8 pair_partial ✅
ingest:         89 sources / 571 candidates / 282 pending / 571 decisions
audit:          571 records / 289 accepted (210 L1 + 79 L2) / 0 missing_paths
```

**基线累计（从 7-19 接管至今）：**

| 指标 | 接管 7-19 | 现在 7-20 | 增量 |
|---|---:|---:|---:|
| candidates | 425 | **571** | **+146** |
| accepted | 201 | **289** | **+88** |
| pending | 224 | **282** | **+58** |
| L2 accepted | 10 | **79** | **+69** |
| sources | 89 | 89 | 0 |

## 二、批次 F-1：saac.gov.cn 剩余 25 件（Page 02/03/06）

### 2.1 整理范围
- **Page 02**：8 件（新政协筹备会各小组开会概要 + 工作报告 + 6 工作小组）
- **Page 03**：5 件（周恩来/李维汉讲话 + 决议案 + 记录 + 主席团名单草案 + 政协通知）
- **Page 06**：12 件（中央人民政府委员会第一次会议全套档案 + 开国大典原始影像）
- **总计**：25 件 L2 accepted

### 2.2 关键 1949 档案
- 中央人民政府委员会第一次会议通知（1949-09-30）
- 中央人民政府任命周恩来为政务院总理兼外交部长通知书（1949-10-01）
- 中华人民共和国中央人民政府公告（1949-10-01）
- 毛泽东与中央人民政府委员合影（1949-10-01）
- 开国大典原始影像（1949-10-01 视频）
- 周恩来对聂荣臻、薄一波关于抽调部队参加阅兵请示的批示
- 饶彰风致中央统战部电报：香港《华商报》升旗典礼

## 三、批次 F-2：Wikimedia Commons 民盟人物 8 条

### 3.1 主分类 3 个直接文件（1949 关键）
- **周恩来与民盟部分代表合影（1949）** — 6 人：楚图南/翦伯赞/沈钧儒/周恩来/吴晗/沈志远
- **民盟领导人为中共代表团送行** — Leaders of CD see CCP mission off
- **民盟代表与中共代表会谈** — 民盟代表与中共代表会谈

### 3.2 张澜 / 烈士 / 关键人物 5 条
- 张澜 1945 重庆谈判公开信
- 张澜/周恩来/朱德/毛泽东/宋庆龄/李济深 1949 中央政府合影
- 1946 李公朴 + 闻一多烈士纪念
- 1947 杜斌丞烈士纪念（民盟西北组织）
- 33 子分类聚合锚点（L3 needs_human_review）

### 3.3 33 子分类清单（已分析）
张澜 19F + 黄炎培 22F + 沈钧儒 30F + 梁漱溟 9F + 闻一多 15F + 李公朴 12F + 史良 9F + 罗隆基 8F + 章伯钧 11F + 张君劢 8F + 杜斌丞 1F + 杨明轩 2F + 陶行知 12F + 胡愈之 3F + 费孝通 10F + 马叙伦 11F + 钱伟长 3F + 楚图南 8F + 吴晗 4F + 潘光旦 2F + 钱端升 1F + 钱家俊 5F + 刘清扬 6F + 叶笃义 6F + 聂维璧 2F + 高崇民 3F + 张宝文 4F + 张东荪 5F + 杨伯恺 1F + 胡世华 1F + 丁仲礼 1F + 张道宏 (empty) + 许慧 (empty)

## 四、本批 33 条新候选分布

| 类别 | 数量 | 等级 |
|---|---:|---|
| saac.gov.cn 剩余 25 件档案 | 25 | L2 accepted |
| Wikimedia Commons 主分类 3 张 1949 照片 | 3 | L2 accepted |
| Wikimedia Commons 张澜/烈士/中央政府合影 4 张 | 4 | L2 accepted |
| Wikimedia Commons 33 子分类聚合锚点 | 1 | L3 needs_human_review |
| **总计** | **33** | **32 L2 + 1 L3** |

## 五、交付物

- 脚本 1：`scripts/domestic/register_saac_remaining_34_20260720.py`（25 件）
- 脚本 2：`scripts/domestic/register_wikimedia_meng_figures_20260720.py`（8 条）

## 六、红线全程遵守

- ❌ 不动 raw 层文件
- ❌ 不为"闭环"虚增 accepted（每条均 WebFetch 实测 + PD-China 验证）
- ❌ 不自动 commit
- ✅ 所有 source_url 经 WebFetch 实测可达
- ✅ Wikimedia Commons 全部 PD-China 公有领域
- ✅ 中国政协官方源 cppcc.people.com.cn

## 七、远程不可办（cheer 主导）

| 资源 | 状态 | cheer 主导动作 |
|---|---|---|
| saac.gov.cn PDF/原件扫描 | 缩略图公开，无 PDF 直链 | cheer 在中央档案馆访问 |
| Wikimedia Commons 33 子分类具体文件 | 仅列类别 URL | cheer 下载高分辨率 |
| mgwxbh.nlc.cn 民盟期刊 | SSL/网络层阻 | NLC 馆内访问 |
| cppcc.gov.cn 政协档案 | SSL 阻 | cheer 浏览器访问 |
| minmeng1941.cn 内容下载 | 等 cookie | cheer 跑下载脚本 |

## 八、下一步建议

### 路径 A：剩余公开资源继续抓
- 各党派省市委官网 1941-1949 历史
- 中央统战部 zytzb.gov.cn
- 光明日报 gmw.cn 历史报道

### 路径 B：saac.gov.cn 剩余 44 件
- Page 01 部分（除已注册的 6 件 + 部分间接）
- Page 04 剩余（部分间接相关）
- Page 05 剩余（部分间接相关）

### 路径 C：cheer 主导路径
- 浏览器跑 minmeng1941.cn 下载脚本
- NLC 馆内访问 mgwxbh.nlc.cn
- 政协档案现场查阅

**明早 3:00 cron 触发，自动继续。**