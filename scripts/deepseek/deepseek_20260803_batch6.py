#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · Batch 6：二手学术 bibliography
======================================================
从 metadata_normalized（二手/待定）中提取正式出版物 → 书目表
字段：题名 / 编者作者 / 出版机构 / 年份 / 出版地或期刊 / ISBN / DOI / 证据等级 / 来源 / 备注

输出（02_analysis/）：
  bibliography_secondary.csv
  batch6_bibliography_report.md
"""
import csv
import re
from pathlib import Path

from _guard import guard

BASE = Path(__file__).resolve().parents[2]
IN = BASE / "work" / "deepseek-20260803" / "01_inputs"
OUT = BASE / "work" / "deepseek-20260803" / "02_analysis"

# (candidate_id 前缀, 题名, 作者/编者, 机构, 年份, 出版机构, ISBN, 备注)
ENTRIES = [
    ("domestic:HE:zhongguo-minmengtongmeng-shijiazhuang-shi-zhi-2013",
     "中国民主同盟石家庄市志", "中国民主同盟石家庄市委员会（编著）", "民盟石家庄市委员会", "2013",
     "河北人民出版社", "", "市级民盟组织志"),
    ("domestic:SN:shaanxi-minmengshi-chenxitao",
     "陕西民盟史", "陈希滔", "民盟陕西省委", "", "陕西人民出版社", "", ""),
    ("domestic:AH:anhui-minzhudangpai-shi-meng-zhangjie-2009",
     "安徽民主党派史（民盟章节）", "", "时代出版传媒股份有限公司、安徽教育出版社", "2009",
     "安徽教育出版社", "", "省级民主党派史"),
    ("domestic:ZJ:zhejiang-sheng-minzhudangpai-zhi-2002",
     "浙江省民主党派志", "浙江省民主党派志编纂委员会", "浙江省民主党派志编纂委员会", "2002",
     "浙江人民出版社", "", "851 页 1215 千字；民盟篇为第二篇"),
    ("domestic:HB:hubei-minmengshi-2014-xiangbiwu",
     "湖北民盟史", "向必武", "民盟湖北省委", "2014", "湖北人民出版社", "", "1946—2013"),
    ("domestic:FJ:zhongguo-minmengtongmeng-fujian-jianshi-2018",
     "中国民主同盟福建简史", "苏增添（主编）", "民盟福建省委", "2018", "线装书局",
     "978-7-5120-2896-2", "1946—2018 简史"),
    ("domestic:HN:hunan-minmengrenwu-2020",
     "湖南民盟人物", "杨君武（编）；民盟湖南省委员会", "民盟湖南省委员会", "2020",
     "群言出版社", "9787519306090", "湖南盟史丛书；352 页"),
    ("domestic:JS:zhongguo-minmengtongmeng-jiangsu-jianshi-2012",
     "中国民主同盟江苏简史", "民盟江苏省委员会、江苏省中共党史资料征集协作小组（编）", "民盟江苏省委",
     "2012", "中央党史出版社", "", ""),
    ("domestic:GD:guangdong-minmengshi-2012-lijingxian",
     "广东民盟史", "李竟先（主编）", "民盟广东省委", "2012", "广东人民出版社", "", ""),
    ("domestic:SC:sichuan-minmengshi-sichuan-renmin",
     "四川民盟史", "民盟四川省委（编）", "民盟四川省委", "", "四川人民出版社", "", ""),
    ("domestic:JS:jiangsu-minmengshi-gao-2004",
     "江苏民盟史稿", "民盟江苏省委员会、江苏省政协文史资料委员会（编）", "民盟江苏省委", "2004",
     "江苏人民出版社", "", ""),
    ("domestic:GZ:guizhou-minmengshi-2013",
     "贵州民盟史", "民盟贵州省委（编）", "民盟贵州省委", "2013", "贵州人民出版社", "", ""),
    ("domestic:YN:yunan-minmengshi-2021-chenguang",
     "云南民盟史", "（云南出版集团晨光出版社）", "民盟云南省委", "2021",
     "云南出版集团晨光出版社", "", "约 48 万字"),
]


def main():
    guard()
    rows = []
    for cid, title, author, inst, year, pub, isbn, note in ENTRIES:
        rows.append({
            "candidate_id": cid,
            "title": title,
            "author_editor": author,
            "institution": inst,
            "year": year,
            "publisher_journal": pub,
            "isbn": isbn,
            "doi": "",
            "evidence_level": "L4",
            "material_class": "二手",
            "note": note,
        })

    with open(OUT / "bibliography_secondary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  [ok] bibliography_secondary.csv ({len(rows)} rows)")

    md = f"""# Batch 6 · 二手学术 Bibliography（正式出版物）

- 来源：metadata_normalized 二手/待定 类中带正式出版信息的条目（出版社/ISBN/编委会），共 {len(rows)} 部
- 性质：民盟各级组织志书、省级民主党派史、组织简史/人物集，均为后出二手学术出版物（L4）
- 用法：作背景/互证书目；不作 citation 直接证据（citation gate G3 已排除二手）
- DOI 字段全部为空：国内出版书目普遍无 DOI，需人工补录（CNKI/读秀链接或书号）
- 缺作者年份条目（四川民盟史/陕西民盟史）需购书核实出版年

## 书目清单
| 题名 | 作者/编者 | 机构 | 年份 | 出版社 | ISBN |
|---|---|---|---|---|---|
"""
    for r in rows:
        md += f"| {r['title']} | {r['author_editor']} | {r['institution']} | {r['year']} | {r['publisher_journal']} | {r['isbn']} |\n"
    md += "\n## 输出\n- bibliography_secondary.csv\n"
    (OUT / "batch6_bibliography_report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
