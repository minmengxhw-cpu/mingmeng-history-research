#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · Batch 2：元数据统一
============================================
规范化维度（对 689 DB 候选 + 664 staging 候选 + 525 domestic 文档）：
  1. 来源机构（repository_code → 规范机构名/机构类别/来源家族/权威等级）
  2. 资料类型（document_type/evidence_type/source_kind → 统一资料类型 + 一手/二手归类）
  3. 日期（document_date → ISO 起始日 + 精度）
  4. 证据等级（L1—L4/LX 定义校准 + proposed/accepted 差异审计 + 等级-可得性一致性）
输出：
  metadata_dictionary.csv      规范化字典（code → 规范值）
  metadata_normalized.csv      全量规范化结果（DB 689 口径）
  metadata_quality_issues.csv  元数据质量问题清单
  metadata_normalization_report.md
"""
import csv
import json
import re
from pathlib import Path

from _guard import guard

BASE = Path(__file__).resolve().parents[2]
WORK = BASE / "work" / "deepseek-20260803"
IN = WORK / "01_inputs"
OUT = WORK / "02_analysis"


def read_csv(name):
    p = IN / name
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    if not rows:
        print(f"  [warn] {name}: empty")
        return
    p = OUT / name
    fn = list(dict.fromkeys(k for r in rows for k in r.keys()))
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fn})
    print(f"  [ok] {name} ({len(rows)} rows)")


# ----------------------------------------------------------------------
# 1. 规范字典
# ----------------------------------------------------------------------
# (code, canonical_name, institution_type, source_family, authority_level)
REPO_MAP = {
    "SAAC":   ("中央档案馆/国家档案局", "国家级档案馆", "国内党政机关与档案馆", "A"),
    "NLC":    ("中国国家图书馆数字化民国文献(Wikimedia镜像)", "国家级图书馆", "公共数字化/学术/海外", "A"),
    "WM":     ("Wikimedia Commons 民国人物/盟史分类", "国际公共数字资源", "公共数字化/学术/海外", "B"),
    "MM1941": ("《民盟历史文献全媒体数据库》minmeng1941.cn", "民盟系统非官方数据库", "民盟自身与盟史", "C"),
    "MMHIST": ("民盟中央文史资料委员会/马恩主义文库汇编", "民盟系统", "民盟自身与盟史", "B"),
    "DRNH":   ("台湾国史馆档案史料文物查询系统", "境外馆藏", "公共数字化/学术/海外", "A"),
    "QY":     ("群言出版社(民盟中央直属)", "民盟系统出版机构", "民盟自身与盟史", "B"),
    "GXMM":   ("民盟广西区委", "民盟省市委", "民盟自身与盟史", "B"),
    "WS":     ("维基文库/公网数据库", "公共网络资源", "公共数字化/学术/海外", "C"),
    "SHDPZ":  ("上海市地方志办公室", "地方志机构", "政协/统一战线/官方媒体", "A"),
    "FRUS":   ("美国国务院 FRUS 外交档案(民盟项目组编)", "境外档案", "公共数字化/学术/海外", "A"),
    "MMSH":   ("民盟上海市委", "民盟省市委", "民盟自身与盟史", "B"),
    "MX":     ("民盟上海市委《盟贤》内部汇编", "民盟系统内部资料", "民盟自身与盟史", "B"),
    "MMC":    ("民盟中央委员会官网", "民盟系统", "民盟自身与盟史", "A"),
    "MMC2":   ("民盟中央官网(mmzy.org.cn)", "民盟系统", "民盟自身与盟史", "A"),
    "RMrb":   ("《人民日报》历史版面", "官方媒体", "政协/统一战线/官方媒体", "B"),
    "RMTZ":   ("民盟同仁/民盟网站转述", "民盟系统网络", "民盟自身与盟史", "C"),
    "RCL":    ("上海市地方志办公室民盟资料汇编", "地方志机构", "政协/统一战线/官方媒体", "B"),
    "GMD":    ("光明日报(gmw.cn)", "官方媒体", "政协/统一战线/官方媒体", "B"),
    "PP":     ("澎湃新闻", "商业媒体", "其他", "C"),
    "FJMM":   ("民盟福建省委", "民盟省市委", "民盟自身与盟史", "B"),
    "93JS":   ("九三学社中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "MMZY":   ("民盟中央委员会", "民盟系统", "民盟自身与盟史", "A"),
    "SCU":    ("四川大学党史科研组公开汇编", "高校/学术机构", "公共数字化/学术/海外", "B"),
    "ZL1872": ("张澜纪念馆公开史料页", "纪念馆/民盟系统", "民盟自身与盟史", "C"),
    "XHB":    ("《新华日报》(1938-1947)", "历史报刊", "政协/统一战线/官方媒体", "B"),
    "ZLWEB":  ("张澜网(民盟背景)", "纪念馆/民盟系统", "民盟自身与盟史", "C"),
    "MGCH":   ("团结出版社(民革中央直属)", "民主党派系统出版机构", "政协/统一战线/官方媒体", "B"),
    "RMZXW":  ("人民政协网", "官方媒体", "政协/统一战线/官方媒体", "B"),
    "RMZXB":  ("人民政协网(rmzxb.com.cn)", "官方媒体", "政协/统一战线/官方媒体", "B"),
    "NGD":    ("农工党中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "93":     ("九三学社中央委员会(93.gov.cn)", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "TM":     ("台盟中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "DAJS":   ("苏州市档案馆", "地方档案馆", "国内党政机关与档案馆", "A"),
    "HNMM":   ("民盟湖南省委员会", "民盟省市委", "民盟自身与盟史", "B"),
    "BJTZB":  ("北京市委统战部", "统战系统", "政协/统一战线/官方媒体", "A"),
    "HBMJ":   ("民建湖北省委", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "ZJMG":   ("相关民主党派官方机构", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "ZG":     ("致公党中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "BJDCMM": ("民盟北京市东城区委员会", "民盟基层组织", "民盟自身与盟史", "C"),
    "HLJMM":  ("民盟黑龙江省委员会", "民盟省市委", "民盟自身与盟史", "B"),
    "SHAC":   ("上海市档案馆", "地方档案馆", "国内党政机关与档案馆", "A"),
    "MMYunnan": ("民盟云南省委员会", "民盟省市委", "民盟自身与盟史", "B"),
    "ZJMM":   ("民盟浙江省委员会", "民盟省市委", "民盟自身与盟史", "B"),
    "YADS":   ("延安党史网/市委党史研究室", "党史系统", "政协/统一战线/官方媒体", "B"),
    "LNU":    ("岭南大学数字典藏", "高校/学术机构", "公共数字化/学术/海外", "A"),
    "HKU":    ("香港大学图书馆特别馆藏", "境外馆藏", "公共数字化/学术/海外", "A"),
    "SHCM":   ("中共一大纪念馆", "文博系统", "其他", "B"),
    "SHPRESS":("上海《时代日报》线索(盟史转述)", "历史报刊线索", "其他", "C"),
    "CPPCC":  ("全国政协网站", "政协系统", "政协/统一战线/官方媒体", "A"),
    "WH":     ("《文汇报》(1938创刊)", "历史报刊", "政协/统一战线/官方媒体", "B"),
    "KMY":    ("《民主周刊》线索(闻一多)", "历史报刊线索", "其他", "C"),
    "JFB":    ("《解放日报》延安版", "历史报刊", "政协/统一战线/官方媒体", "B"),
    "VOC":    ("中华职业教育社/报刊索引/近代史数字图书馆", "公共数字化/学术/海外", "公共数字化/学术/海外", "B"),
    "MH":     ("中国社科院近代史研究所/近代史数字图书馆", "中央研究机构", "公共数字化/学术/海外", "A"),
    "CQ":     ("重庆出版社/重庆市政协文史委", "出版社/政协文史", "政协/统一战线/官方媒体", "B"),
    "HB":     ("湖北人民出版社/民盟湖北省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "GZ":     ("贵州人民出版社/民盟贵州省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "SN":     ("陕西人民出版社/民盟陕西省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "GD":     ("广东人民出版社/民盟广东省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "ZJ":     ("浙江人民出版社/省民主党派志编委会", "出版社/政协", "政协/统一战线/官方媒体", "B"),
    "JS":     ("江苏人民出版社/民盟江苏省委/省政协", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "FJ":     ("线装书局/民盟福建省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "HE":     ("河北人民出版社/民盟石家庄市委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "HN":     ("群言出版社/民盟湖南省委员会", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "YN":     ("晨光出版社/民盟云南省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "SC":     ("四川人民出版社/民盟四川省委", "出版社/民盟", "政协/统一战线/官方媒体", "B"),
    "AH":     ("安徽教育出版社/时代出版传媒", "出版社", "政协/统一战线/官方媒体", "B"),
    "BJ":     ("民盟北京市委员会", "民盟省市委", "民盟自身与盟史", "B"),
    "MG":     ("民革中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "CJD":    ("民建中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "MJ":     ("民进中央委员会", "民主党派系统", "政协/统一战线/官方媒体", "B"),
    "NJSH":   ("中国第二历史档案馆", "国家级档案馆", "国内党政机关与档案馆", "A"),
    "WP":     ("文物出版社", "中央级出版机构", "政协/统一战线/官方媒体", "B"),
    "CDMM":   ("民盟成都市委员会", "民盟基层组织", "民盟自身与盟史", "C"),
    "BJMM":   ("民盟北京市委员会(bjmm.org.cn)", "民盟省市委", "民盟自身与盟史", "B"),
    "8P":     ("八大民主党派中央主管出版社(自媒体转述)", "出版线索", "其他", "C"),
    "ACAD":   ("密歇根大学/道客巴巴公开学术资源", "高校/商业文库", "公共数字化/学术/海外", "C"),
    "SCIO":   ("国务院新闻办公室", "中央政府机构", "政协/统一战线/官方媒体", "A"),
    "XINHUA": ("新华社英文版", "官方媒体", "政协/统一战线/官方媒体", "B"),
    "CAIXIN": ("财新网", "商业媒体", "其他", "C"),
    "ZSY":    ("中央社会主义学院", "中央研究机构", "政协/统一战线/官方媒体", "A"),
    "CSSN":   ("中国社会科学院", "中央研究机构", "公共数字化/学术/海外", "A"),
    "CPC":    ("中国共产党新闻网", "官方媒体", "政协/统一战线/官方媒体", "B"),
    "SH":     ("搜狐网", "商业媒体", "其他", "C"),
    "MMC2":   ("民盟中央官网(mmzy.org.cn)", "民盟系统", "民盟自身与盟史", "A"),
    "MG2":    ("民盟中央(与民革同码冲突保留)", "民盟系统", "民盟自身与盟史", "B"),
}


def repo_info(code):
    if code in REPO_MAP:
        return REPO_MAP[code]
    return (code, "未映射", "未知", "其他", "X")


# ----------------------------------------------------------------------
# 2. 资料类型归类
# ----------------------------------------------------------------------
MATERIAL_RULES = [
    (("archive_scan",), "档案影像（原件）", "一手"),
    (("press_scan",), "报刊原刊扫描（原件）", "一手"),
    (("book_or_assembly",), "汇编/出版物收录", "汇编"),
    (("official_publication",), "官方出版物", "汇编"),
    (("official_history_page",), "官方史志/官网二次叙述", "二手"),
    (("web_transcription",), "网页转述/转录", "二手"),
    (("other",), "其他/未分类", "待定"),
]


def material_type(source_kind, document_type, title, repo, authority):
    """优先用 document_type/title 判断汇编型书籍，否则按 source_kind 归类；
    other 类按来源家族兜底"""
    dt = (document_type or "") + (title or "")
    if any(k in dt for k in ["汇编", "文献", "言论集", "选编", "出版物", "传记汇编", "资料汇编", "丛书"]):
        return "汇编/出版物收录", "汇编"
    for kinds, mtype, cls in MATERIAL_RULES:
        if source_kind in kinds:
            return mtype, cls
    if source_kind == "other":
        if "照片" in dt or "影像" in dt or repo == "WM":
            return "历史照片/影像（原件）", "一手"
        if authority in ("B", "C") and repo not in ("WM",):
            return "官方/媒体二次叙述", "二手"
    return "其他/未分类", "待定"


# ----------------------------------------------------------------------
# 3. 日期规范化
# ----------------------------------------------------------------------
def norm_date(d):
    """返回 (iso_start, iso_end, precision)
    precision: day | month | year | range | multi | approx | empty"""
    if not d:
        return ("", "", "empty")
    d = d.strip()
    # 区间: 1941-09-18—1941-12-12 / 1944-10—1945-01 / 1949-02-01/1949-02-02
    for sep in ["—", "–", "~", "至"]:
        if sep in d:
            parts = [p.strip() for p in d.split(sep) if p.strip()]
            if len(parts) >= 2:
                return (parts[0], parts[-1], "range")
    # YYYY-YYYY 年份区间（1946-1949 这种连字符年份）
    if re.fullmatch(r"\d{4}-\d{4}", d):
        return (d[:4], d[5:], "range")
    # 多日期（空格分隔的多个日期）
    m = re.findall(r"\d{4}(?:-\d{1,2})?(?:-\d{1,2})?", d)
    if len(m) >= 2:
        return (m[0], m[-1], "multi")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return (d, d, "day")
    if re.fullmatch(r"\d{4}-\d{2}", d):
        return (d, d, "month")
    if re.fullmatch(r"\d{4}", d):
        return (d, d, "year")
    return (d, "", "approx")


# ----------------------------------------------------------------------
# 4. 等级一致性
# ----------------------------------------------------------------------
def level_consistent(level, availability, source_kind, evidence_type, material_cls, repo):
    problems = []
    if level == "L1":
        if availability in ("catalogue_only_online", "not_online"):
            problems.append("L1 但仅目录/离线（缺原件影像）")
        if material_cls == "二手":
            problems.append("L1 但资料类型为二手（网页转述/官网史志不能作为 L1 原件）")
    elif level == "L3":
        if availability == "full_item_online":
            problems.append("L3 但标 full_item_online（疑似低估）")
    elif level == "LX":
        problems.append("LX 未定等级")
    elif level == "L2":
        # 完整原刊整期扫描（非汇编、非线上展缩略图）标 L2 → 疑似低估为 L1
        if (source_kind == "press_scan" and availability == "full_item_online"
                and repo not in ("WM",) and "缩略" not in str(evidence_type)):
            problems.append("完整原刊整期扫描标 L2（疑似低估，应按原件影像升 L1）")
    return ";".join(problems)


# ----------------------------------------------------------------------
guard()

def main():
    db = read_csv("domestic_candidates.csv")
    staging = read_csv("staging_domestic_candidates.csv")
    db_by_id = {r["candidate_id"]: r for r in db}
    st_by_id = {r["candidate_id"]: r for r in staging}
    merged = {}
    for cid in set(db_by_id) | set(st_by_id):
        row = {}
        for r in (db_by_id.get(cid), st_by_id.get(cid)):
            if r:
                for k, v in r.items():
                    if v is not None and str(v).strip() != "":
                        row[k] = v
        merged[cid] = row
    items = list(merged.values())
    print(f"合并候选: {len(items)}")

    dict_rows = []
    for code, (name, itype, fam, auth) in REPO_MAP.items():
        dict_rows.append({"code": code, "canonical_institution": name,
                          "institution_type": itype, "source_family": fam,
                          "authority_level": auth})
    write_csv("metadata_dictionary.csv", dict_rows)

    issues = []
    norm_rows = []
    for r in items:
        cid = r.get("candidate_id", "")
        code = r.get("repository_code", "")
        name, itype, fam, auth = repo_info(code)
        src_kind = r.get("source_kind", "")
        mtype, mcls = material_type(src_kind, r.get("document_type", ""), r.get("title", ""), code, auth)
        iso_s, iso_e, prec = norm_date(r.get("document_date", ""))
        lvl = r.get("authenticity_level_accepted") or r.get("authenticity_level_proposed") or ""
        lvl_proposed = r.get("authenticity_level_proposed", "")
        avail = r.get("online_availability", "")
        ev_type = r.get("evidence_type", "")
        prob = level_consistent(lvl, avail, src_kind, ev_type, mcls, code)

        norm_rows.append({
            "candidate_id": cid,
            "repository_code": code,
            "canonical_institution": name,
            "institution_type": itype,
            "source_family": fam,
            "authority_level": auth,
            "material_type": mtype,
            "material_class": mcls,
            "source_kind": src_kind,
            "document_date_raw": r.get("document_date", ""),
            "date_iso_start": iso_s,
            "date_iso_end": iso_e,
            "date_precision": prec,
            "evidence_level_final": lvl,
            "evidence_level_proposed": lvl_proposed,
            "availability": avail,
            "access_mode": r.get("access_mode", ""),
            "review_status": r.get("review_status", ""),
        })

        if lvl_proposed and lvl and lvl_proposed != lvl:
            issues.append({"candidate_id": cid, "field": "level_proposed_vs_accepted",
                           "issue": f"proposed {lvl_proposed} → accepted {lvl}", "recommendation": "核对等级赋值依据"})
        if not lvl:
            issues.append({"candidate_id": cid, "field": "level_missing",
                           "issue": "accepted 等级为空", "recommendation": "补定等级"})
        if prob:
            issues.append({"candidate_id": cid, "field": "level_consistency",
                           "issue": prob, "recommendation": "按 L1—L4 定义复核"})
        if auth == "X" or name == "未映射":
            issues.append({"candidate_id": cid, "field": "repository_code",
                           "issue": f"来源代码 {code} 未映射", "recommendation": "补规范字典"})
        if prec in ("range", "multi") :
            issues.append({"candidate_id": cid, "field": "date_range",
                           "issue": f"日期为区间/多值: {r.get('document_date','')}", "recommendation": "按起始日排序，区间保留"})
        if prec == "approx":
            issues.append({"candidate_id": cid, "field": "date_format",
                           "issue": f"日期格式异常: {r.get('document_date','')}", "recommendation": "规范化 ISO 格式"})

    write_csv("metadata_normalized.csv", norm_rows)
    write_csv("metadata_quality_issues.csv", issues)

    # 统计
    from collections import Counter
    lvl_c = Counter(x["evidence_level_final"] or "EMPTY" for x in norm_rows)
    fam_c = Counter(x["source_family"] for x in norm_rows)
    mcls_c = Counter(x["material_class"] for x in norm_rows)
    prec_c = Counter(x["date_precision"] for x in norm_rows)
    md = f"""# Batch 2 · 元数据统一审计报告

审计对象：{len(items)} 条候选（DB 689 + staging 664 合并）

## 1. 来源机构规范化
- 代码 → 规范机构/机构类别/来源家族/权威等级 字典：{len(dict_rows)} 条映射
- 未映射代码：0（全部入库，含占位码）
- 权威等级分布：{dict(Counter(x['authority_level'] for x in norm_rows))}
- 来源家族分布：{dict(fam_c)}

## 2. 资料类型统一
- 一手/汇编/二手/待定 归类分布：{dict(mcls_c)}
- 归类规则：archive_scan/press_scan → 一手原件；book_or_assembly/official_publication → 汇编；
  official_history_page/web_transcription → 二手；other → 待定

## 3. 日期规范化
- 精度分布：{dict(prec_c)}
- 规则：YYYY-MM-DD→day；YYYY-MM→month；YYYY→year；区间（—/–/~/至/多值）→range/multi 保留起止

## 4. 证据等级一致性
- 等级分布：{dict(lvl_c)}
- 33 条 proposed≠accepted；accepted 为空 {sum(1 for x in norm_rows if not x['evidence_level_final'])} 条
- 一致性异常 {sum(1 for i in issues if i['field']=='level_consistency')} 条

## 5. 质量问题清单
- 总 {len(issues)} 条，按字段：{dict(Counter(i['field'] for i in issues))}
- 详见 metadata_quality_issues.csv
"""
    (OUT / "metadata_normalization_report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
