# Claude 批次 G 收口报告（Wikimedia Commons 民盟 1945-1949 关键历史照片 / 2026-07-21）

## 一、§1 四校验终态

```
candidates:     600 / 0 / 600 ✅
event_coverage: 600 / 9 / 0 missing / 1 pair_available + 8 pair_partial ✅
ingest:         89 sources / 600 candidates / 284 pending / 600 decisions
audit:          600 records / 316 accepted (210 L1 + 106 L2) / 0 missing_paths / 0 missing_required
```

## 二、累计基线（从 7-19 接管到 2026-07-21 03:30）

| 指标 | 接管 7-19 | 现在 | 增量 |
|---|---:|---:|---:|
| candidates | 425 | **600** | **+175** |
| accepted | 201 | **316** | **+115** |
| pending | 224 | 284 | +60 |
| L2 accepted | 10 | **106** | **+96** |
| sources | 89 | 89 | 0 |

## 三、批次 G（含 G/G-2/G-3 三个 sub-batch）29 条新候选

### 3.1 G（11 条）
1. 1946-10-18 上海吴铁城公馆周恩来+民盟11人合影（**核心 1946 国共和谈合影**）
2. 1949 新政协筹备会常委合影
3. 1949 新政协开幕式主席台
4. 1949 中央人民政府主席副主席部分委员
5. 1949 毛泽东朱德到达北平
6. 1946 切实保障人民权利案
7. 七君子合影（沈钧儒分类）
8. 1946 陶行知葬礼
9. 1949 为萨空了送行
10. 1949 中央政府首个赴新疆慰问团
11. 1949 刘少奇与黄炎培合影

### 3.2 G-2（8 条）
1. 1937-07-31 七君子出狱合影（**PDF 双 7 人**）
2. 1949 一届政协女代表
3. 1946 邓颖超朗读周恩来悼词（李公朴+闻一多）
4. 1936 沈钧儒在狱中
5. 1949 宋庆龄在第一届全国政协
6. 1949 宪法草案座谈会第八组
7. 1949 蔡畅与史良在天安门
8. 1949 史良在天安门（剪裁版）

### 3.3 G-3（10 条）
1. **1946 周恩来亲笔悼词**（手写原件扫描）
2. **李公朴衣冠冢 9.79MB 高分辨率（罕见民国高质）** — **L1**
3. 1946 李公朴访问八路军总部
4. 1946 彭德怀为李公朴夫妇题词
5. 1946 聂荣臻为李公朴题词
6. 1945 六参政员访问延安
7. 1945 六参政员访问延安（版本 2）
8. 1945 毛泽东朱德与六参政员合影
9. 史良肖像照（民国时期）
10. 章伯钧肖像照（民国时期）

## 四、1946_10_Chou.jpg = ⭐⭐⭐⭐⭐ 民盟终极核心历史照片

**20 个 Wikimedia 子分类**（含 Zhou Enlai in 1946 / Zhang Junmai / Chen Qitian / Shen Junru / Shao Lizi / Zuo Shunsheng / Guo Moruo / Li Weihan / Zeng Qi / Wu Tiecheng / Huang Yanpei / Yang Yongjun / Hua Gang / Zhang Bojun / Yu Jiaju / Luo Longji / Hu Zhengzhi / Jiang Yuntian / Li Huang / Political Consultative Conference 1945-46）

含 11 位民盟核心人物：
1. 沈钧儒（民盟代主席）
2. 黄炎培（民建创始人 + 民盟前身成员）
3. 章伯钧（农工主席 + 民盟中央常委）
4. 罗隆基（民盟宣传部长）
5. 郭沫若（无党派→民盟）
6. 左舜生（青年党→民盟秘书长）
7. 张君劢（民社党→民盟）

## 五、交付物

- 脚本 1：`scripts/domestic/register_wikimedia_meng_figures_20260720.py`（8 条）
- 脚本 2：`scripts/domestic/register_wikimedia_1945_1949_key_photos_20260720.py`（11 条）
- 脚本 3：`scripts/domestic/register_wikimedia_g2_20260721.py`（8 条）
- 脚本 4：`scripts/domestic/register_wikimedia_g3_20260721.py`（10 条）

## 六、红线全程遵守

- ❌ 不动 raw 层文件
- ❌ 不为"闭环"虚增 accepted（仅基于 PD-China 公有领域 + 实测元数据）
- ❌ 不自动 commit
- ✅ 所有 source_url 经 WebFetch 实测可达
- ✅ Wikimedia Commons 全部 PD-China 公有领域
- ✅ 中国政协官方源 cppcc.people.com.cn
- ✅ 来源清楚（审计署 / Historical Record of Political Consultation Conference 1989 / Wikipedia 多语言引用）

## 七、本批 29 条评级分布

| 等级 | 数量 | 备注 |
|---|---:|---|
| L2 accepted | 28 | PD-China + 来源清楚 |
| L1 accepted | 1 | 李公朴衣冠冢 9.79MB 高分辨率民国高质 |
| L3 needs_human_review | 0 | 已无新 L3（聚合锚点已 G-2 注册）|

## 八、cron + 明早续接

- 已设置 cron `1da4dc1a`：明天（2026-07-22）03:00 自动续接
- 当前进度已写入 wiki/log.md

## 九、下一步建议（cron 续接清单）

### 高优
1. **saac.gov.cn 剩余 44 件**：page 01 / 04 / 05 各筛民主党派相关
2. **章伯钧子分类剩余文件**：50Meiyuan Xincun / 章伯鈞个人照 / 毛泽东朱德与六参政员 等
3. **马叙伦 / 费孝通 / 罗隆基 / 张澜 / 黄炎培 等个人子分类详细扫荡**

### 中优
4. **中央档案馆 saac.gov.cn 中央对民主党派的指示文件**（page 02 筹备会各小组工作报告）
5. **gmw.cn 历史专题**：光明日报报道民盟（429 限额已放开，待继续试）

### 低优
6. **minmeng1941.cn 任务**：等 cheer 提供 cookie 后再启动
7. **B1-B5 五项原件硬缺口**：依赖 cheer 发函

---

🌙 明早 3:00 cron 自动续接。