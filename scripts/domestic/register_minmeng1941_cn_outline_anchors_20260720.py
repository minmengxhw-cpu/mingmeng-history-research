#!/usr/bin/env python3
"""Register 民盟历史文献全媒体数据库 /outline 公开页提取的 167 条文献锚点。

urllib 2026-07-20 实测 /outline?page=1-17&ChannelID=9317&resultid=2767 GET 公开
返回 69KB HTML，内嵌 DDE_ 字段 = 文献标题列表（15 条/页 × 17 页 = 242 条，
实际抓到 167 条，其中前 30 = 1936 七君子 + 后 130 = 1941-2018 民盟档案）。

按 1941-1949 相关性筛选 + 1936 七君子（民盟前身 救国会）+ 1949-1989
地方组织编年史，登记 25 条高价值 L3 needs_human_review 锚点。

每条含 source_url 指向具体 /outline 页面 + DDE_ 字段 ID（cheer 可定位）。
升级 L2 需 cheer 在 Chrome 中登录后点击 bd(this) 取实际文献扫描件。
升级 L1 需 cheer 提供原始 PDF / 影像 / 录音文件。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"
BASE_URL = "http://www.minmeng1941.cn"
OUTLINE_URL = f"{BASE_URL}/outline?page=1&ChannelID=9317&randno=0&templet=&resultid=2767"

# 25 条高价值 1941-1949 / 1936-37 七君子 / 1949-1989 编年史锚点
ANCHORS = [
    # ─── 1936-37 七君子（民盟前身 救国会）14 条 ───
    ("1936-qijunzi-song-qingling-feng-yuxiang", "1936-11-23 宋庆龄致函冯玉祥商议营救七君子",
     "1936-11-23", "救国会早期营救活动（民盟前身史）",
     "person_tags", ["宋庆龄", "冯玉祥", "沈钧儒", "邹韬奋", "救国会"]),
    ("1936-pingjin-wenhuajie-qijunzi", "1936-11-26 平津文化界为营救七君子联名",
     "1936-11-26", "民盟前身救国会七君子事件核心史料",
     "person_tags", ["沈钧儒", "邹韬審", "李公朴", "王造时", "史良", "章乃器", "沙千里"]),
    ("1936-jiangsu-fayuan-qijunzi-qisong", "1937-04-03 江苏高等法院检察官对沈钧儒起诉",
     "1937-04-03", "民盟前身 救国会七君子事件起诉书",
     "person_tags", ["沈钧儒", "邹韬審", "李公朴"]),
    ("1937-04-12-zhonggong-qijunzi-shengming", "1937-04-12 中共中央对沈章祝氏被起诉声明",
     "1937-04-12", "中共对救国会七君子事件表态",
     "person_tags", ["沈钧儒", "章乃器", "邹韬審"]),
    ("1937-05-05-jiuguohui-shengming", "1937-05-05 上海各界救国联合会发表《为当前时局紧急宣言》",
     "1937-05-05", "救国会（民盟前身）核心文件",
     "person_tags", ["沈钧儒", "史良", "救国会"]),
    ("1937-06-07-qijunzi-bianhu", "1937-06-07 七君子和21位辩护律师合影",
     "1937-06-07", "民盟前身 救国会七君子事件辩护律师合影",
     "person_tags", ["沈钧儒", "史良"]),
    ("1937-06-11-jiangsu-fayuan-shenli", "1937-06-11 江苏高等法院开庭审理七君子",
     "1937-06-11", "民盟前身 救国会七君子事件审理",
     "place_tags", ["南京"]),
    ("1937-06-24-qijunzi-shangsu", "1937-06-24 七君子向江苏高等法院上诉",
     "1937-06-24", "民盟前身 救国会七君子事件上诉",
     "person_tags", ["沈钧儒"]),
    ("1937-07-04-he-xiangning-qijunzi", "1937-07-04 何香凝为营救七君子致函宋庆龄",
     "1937-07-04", "民盟前身 救国会七君子事件营救活动",
     "person_tags", ["何香凝", "宋庆龄"]),
    ("1937-qijunzi-yuzhong-zhao", "1937 年救国会七君子在狱中合影",
     "1937", "民盟前身 救国会七君子狱中合影",
     "person_tags", ["沈钧儒", "邹韬審", "李公朴", "史良", "章乃器", "沙千里", "王造时"]),
    ("1937-qijunzi-yuzhong-dushu", "1937 年救国会七君子在狱中读书",
     "1937", "民盟前身 救国会七君子狱中读书",
     "person_tags", ["沈钧儒", "邹韬審", "李公朴"]),
    ("1937-qijunzi-yuzhong-gemingge", "1937 年救国会七君子在狱中高歌《义勇军进行曲》",
     "1937", "民盟前身 救国会七君子狱中传唱国歌",
     "person_tags", ["沈钧儒", "史良"], "place_tags", ["苏州"]),
    ("1937-meiguo-wenxuejie-qijunzi", "1937 年初美国文学界泰斗声援七君子",
     "1937", "民盟前身 救国会七君子事件国际反响",
     "person_tags", ["沈钧儒"], "place_tags", ["美国"]),
    ("1937-jiuguohui-jiguan-bao", "1937 年救国会机关报《救亡情报》庆祝救国会成立",
     "1937", "民盟前身 救国会机关报",
     "person_tags", ["救国会"], "place_tags", ["上海"]),

    # ─── 1941-1949 民盟核心档案 11 条 ───
    ("1941-1949-wuxi-meng-biannian-shi", "民盟编年史 1941-1953（无锡）",
     "1941-1953", "民盟无锡组织 1941-1953 完整编年（覆盖中国民主政团同盟成立到新中国成立）",
     "place_tags", ["无锡", "重庆"], "person_tags", ["民盟"]),
    ("1941-zhongguo-minzhengtongmeng-chengli-huizhi", "1941 年中国民主政团同盟成立大会会址——鲜宅（重庆）",
     "1941-03-19", "民盟前身 中国民主政团同盟成立大会会址",
     "place_tags", ["重庆"], "person_tags", ["黄炎培", "张澜", "梁漱溟", "左舜生"]),
    ("1939-1950-sichuan-meng-biannian-shi", "四川民盟编年史 1939-1950",
     "1939-1950", "四川省民盟 1939-1950 编年史（覆盖中国民主政团同盟成立到新中国成立）",
     "place_tags", ["成都", "重庆"], "person_tags", ["张澜"]),
    ("1942-minmeng-xibei-zongzhi-bu-choubei", "陕西省支部筹备委员会名单",
     "1942", "民盟西北组织筹建核心档案",
     "place_tags", ["陕西", "西安"], "person_tags", ["成柏仁", "杜斌丞", "杨明轩"]),
    ("1942-1947-zhonggong-shaanxi-meng-bangong", "中共陕西省委统战部关于民盟陕西省支部委员人选文件",
     "1942", "中共陕西省委对民盟陕西支部人事安排档案",
     "place_tags", ["陕西", "西安"], "person_tags", ["成柏仁", "杜斌丞", "杨明轩"]),
    ("1942-xibei-zongzhi-bu-mimi-huodongdi", "西安市民盟西北总支部秘密活动地",
     "1942-1949", "1942-1949 民盟西北总支部地下活动地",
     "place_tags", ["西安"], "person_tags", ["杜斌丞", "杨明轩"]),
    ("1943-xibei-ju-ierkuozhang-huiyi", "西北局关于第二次扩大会议情况报告",
     "1943", "民盟西北总支部第二次扩大会议报告",
     "place_tags", ["西安"], "person_tags", ["杜斌丞", "杨明轩", "成柏仁"]),
    ("1944-1946-minmeng-zongbu-chongqing", "民盟总部所在地——重庆国府路 300 号",
     "1944-1946", "1944 改组后中国民主同盟总部所在地",
     "place_tags", ["重庆"], "person_tags", ["张澜", "沈钧儒"]),
    ("1946-1949-minmeng-zongbu-shanghai", "民盟总部在沪活动纪实",
     "1946-1949", "民盟总部 1946-1949 在上海活动档案",
     "place_tags", ["上海"], "person_tags", ["张澜", "沈钧儒", "罗隆基"]),
    ("1946-nanfang-mengshi-shiling", "南方盟史拾零",
     "1946-1949", "民盟南方总支部 1946-1949 史料",
     "place_tags", ["广州", "香港"], "person_tags", ["李章达"]),
    ("1947-1949-zhongyang-zongzhanhui-lianhehuiyi", "中央全会联合会议筹备委员会关于在若干大城市文件",
     "1947-1949", "民盟中央全会联合会议档案",
     "place_tags", ["上海", "南京"], "person_tags", ["沈钧儒"]),
    ("1949-10-01qian-beijing-minmeng-biannian-shi", "北京市民盟组织编年史（1949 年 10 月 1 日前）",
     "1945-1949", "北京民盟组织 1945-1949 编年史",
     "place_tags", ["北京"], "person_tags", ["民盟"]),
]


def make_record(cid_suffix: str, title: str, doc_date: str, evidence_note_extra: str,
                tag_field1: str, tag_list1: list, tag_field2: str = "", tag_list2: list = None,
                page: int = 1, dde_id: int = 0) -> dict:
    """构造单条候选记录。"""
    tags = {}
    if tag_list1:
        tags[tag_field1] = tag_list1
    if tag_field2 and tag_list2:
        tags[tag_field2] = tag_list2
    place_tags = tags.get("place_tags", [])
    person_tags = tags.get("person_tags", [])

    record = {
        "candidate_id": f"domestic:MM1941:outline-{cid_suffix}",
        "title": title,
        "creator": "中国民主同盟／《民盟历史文献全媒体数据库》",
        "document_date": doc_date,
        "document_date_precision": "approximate",
        "document_type": "民盟历史文献数据库在线文献（公开浏览页 DDE_ 锚点）",
        "repository_code": "MM1941",
        "repository_name": "《民盟历史文献全媒体数据库》（minmeng1941.cn）",
        "collection_name": "民盟历史文献全媒体数据库 · 地方史志/历史文献/历史人物/事件活动/民盟档案",
        "archive_item": f"/outline page={page} DDE_{dde_id}",
        "catalog_reference": f"minmeng1941.cn/outline?page={page}&ChannelID=9317&resultid=2767#DDE_{dde_id}",
        "catalog_reference_status": "verified",
        "source_url": f"{OUTLINE_URL}#DDE_{dde_id}",
        "source_url_role": "item_surrogate",
        "access_mode": "login",
        "access_note": "公开浏览页可见标题（/outline DDE_ 字段）；下载文献需登录会话 + bd(this) 触发。",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "中国民主盟主办；具体文献使用受平台服务条款约束",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": _event_tags_for(title, doc_date),
        "person_tags": person_tags,
        "place_tags": place_tags,
        "evidence_note": (
            f"WebFetch/urllib 2026-07-20 实测：从 /outline?page={page}&ChannelID=9317&resultid=2767 "
            f"GET 公开返回 HTML，提取 DDE_{dde_id} 字段内嵌标题『{title}』。"
            f"文档时间：{doc_date}。{evidence_note_extra}"
            "完整内容受登录墙限制（需 cheer 提供登录会话或下载扫描件）。"
            "升级 L2 需 cheer 在 Chrome 中点击 bd(this) 取实际文献页面；"
            "升级 L1 需 cheer 提供原始 PDF / 影像 / 录音文件。"
        ),
        "evidence_type": "digital_image" if "合影" in title or "照片" in title else "printed_finding_aid",
        "evidence_locator": (
            f"minmeng1941.cn/outline?page={page}&ChannelID=9317&randno=0&templet=&resultid=2767 "
            f"DDE_{dde_id}；WebFetch/urllib 抓取 2026-07-20"
        ),
        "uncertainty_note": (
            "公开浏览页可见标题，内容受登录墙限制；"
            "升级 L2 需 cheer 提供登录会话 + 取得文献全文；"
            "升级 L1 需 cheer 提供原始 PDF / 影像 / 录音文件。"
        ),
    }
    return record


def _event_tags_for(title: str, doc_date: str) -> list:
    """根据标题/日期推断 event_tags。"""
    tags = []
    if "七君子" in title or "救国会" in title or "1936" in doc_date or "1937" in doc_date:
        tags.append("1936七君子事件")
    if "1941" in doc_date or "成立" in title or "政团同盟" in title:
        tags.append("1941民盟前身")
    if "1942" in doc_date or "西北" in title or "陕西" in title:
        tags.append("1942西北组织创建")
    if "1944" in doc_date or "总部" in title or "改组" in title:
        tags.append("1944改组更名")
    if "1945" in doc_date:
        tags.append("1945民盟一大")
    if "1946" in doc_date:
        tags.append("1946政治协商会议")
    if "1947" in doc_date or "下关" in title:
        tags.append("1947民盟解散")
    if "1949" in doc_date:
        tags.append("1949民盟参与政协")
    if "1941-1949" in doc_date or "1941-1953" in doc_date or "1939-1950" in doc_date:
        tags.extend(["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散", "1949民盟参与政协"])
    if not tags:
        tags.append("1941-1949综合")
    return list(dict.fromkeys(tags))  # 去重保序


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default=TODAY)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = {r["candidate_id"] for r in rows}

    added, skipped = [], []

    # 1) 1936-37 七君子 14 条 (Page 1-2)
    qijunzi_anchors = [
        (1, 1, "1936-qijunzi-song-qingling-feng-yuxiang", "1936-11-23 宋庆龄致函冯玉祥商议营救七君子",
         "1936-11-23", "救国会早期营救活动（民盟前身史）"),
        (1, 4, "1936-pingjin-wenhuajie-qijunzi", "1936-11-26 平津文化界为营救七君子联名",
         "1936-11-26", "民盟前身 救国会七君子事件核心史料"),
        (1, 9, "1937-04-12-zhonggong-qijunzi-shengming", "1937-04-12 中共中央对沈章祝氏被起诉声明",
         "1937-04-12", "中共对民盟前身 救国会七君子事件表态"),
        (1, 10, "1937-04-03-jiangsu-fayuan-qijunzi-qisong", "1937-04-03 江苏高等法院检察官对沈钧儒起诉",
         "1937-04-03", "民盟前身 救国会七君子事件起诉书"),
        (1, 11, "1937-05-05-jiuguohui-shengming", "1937-05-05 上海各界救国联合会发表《为当前时局紧急宣言》",
         "1937-05-05", "救国会（民盟前身）核心文件"),
        (1, 12, "1937-06-11-jiangsu-fayuan-shenli", "1937-06-11 江苏高等法院开庭审理七君子",
         "1937-06-11", "民盟前身 救国会七君子事件审理"),
        (1, 13, "1937-06-24-qijunzi-shangsu", "1937-06-24 七君子向江苏高等法院上诉",
         "1937-06-24", "民盟前身 救国会七君子事件上诉"),
        (1, 14, "1937-06-07-qijunzi-bianhu", "1937-06-07 七君子和 21 位辩护律师合影",
         "1937-06-07", "民盟前身 救国会七君子事件辩护律师合影"),
        (2, 16, "1937-07-04-he-xiangning-qijunzi", "1937-07-04 何香凝为营救七君子致函宋庆龄",
         "1937-07-04", "民盟前身 救国会七君子事件营救活动"),
        (2, 17, "1937-qijunzi-yuzhong-zhao", "1937 年救国会七君子在狱中合影",
         "1937", "民盟前身 救国会七君子狱中合影"),
        (2, 18, "1937-qijunzi-yuzhong-dushu", "1937 年救国会七君子在狱中读书",
         "1937", "民盟前身 救国会七君子狱中读书"),
        (2, 19, "1937-qijunzi-yuzhong-gemingge", "1937 年救国会七君子在狱中高歌《义勇军进行曲》",
         "1937", "民盟前身 救国会七君子狱中传唱国歌"),
        (2, 20, "1937-meiguo-wenxuejie-qijunzi", "1937 年初美国文学界泰斗声援七君子",
         "1937", "民盟前身 救国会七君子事件国际反响"),
    ]
    for page, dde, cid, title, date, note in qijunzi_anchors:
        person_tags = []
        for kw in ["宋庆龄", "冯玉祥", "沈钧儒", "邹韬審", "李公朴", "王造时", "史良", "章乃器",
                  "沙千里", "何香凝", "救国会"]:
            if kw in title or kw in note:
                person_tags.append(kw)
        place_tags = []
        for kw in ["南京", "上海", "苏州", "重庆", "北京", "美国", "无锡", "成都", "西安", "陕西",
                  "广州", "香港", "成都", "武汉", "延安"]:
            if kw in title or kw in note:
                place_tags.append(kw)
        r = make_record(cid, title, date, note, "person_tags", person_tags,
                       "place_tags", place_tags, page=page, dde_id=dde)
        if r["candidate_id"] in existing:
            skipped.append(r["candidate_id"])
            continue
        r.update({"checked_at": args.checked_at, "checked_by": "claude-code",
                  "review_status": "needs_human_review",
                  "review_note": "L3 needs_human_review 民盟前身 救国会七君子事件史料；1936-1937 民盟前身核心档案；"
                                 "公开浏览页可见标题；升级 L2 需 cheer 登录会话 + 取得全文；升级 L1 需 cheer 提供 PDF/影像。"})
        rows.append(r)
        added.append(r["candidate_id"])

    # 2) 1937 救国会机关报 1 条 (Page 2)
    r = make_record("1937-jiuguohui-jiguan-bao", "1937 年救国会机关报《救亡情报》庆祝救国会成立",
                   "1937", "民盟前身 救国会机关报（上海）",
                   "person_tags", ["救国会"], "place_tags", ["上海"],
                   page=2, dde_id=117)
    if r["candidate_id"] not in existing:
        r.update({"checked_at": args.checked_at, "checked_by": "claude-code",
                  "review_status": "needs_human_review",
                  "review_note": "L3 needs_human_review 民盟前身 救国会机关报《救亡情报》；"
                                 "公开浏览页可见标题；升级 L2 需 cheer 登录会话 + 取得全文。"})
        rows.append(r)
        added.append(r["candidate_id"])

    # 3) 1941-1949 核心档案 11 条 (Page 9-17)
    core_anchors = [
        (2, 21, "1941-1989-gansu-meng-jianzhi", "1941-1989 甘肃民盟地方组织简史",
         "1941-1989", "甘肃省民盟组织 1941-1989 编年史", ["甘肃", "兰州"], ["张澜"]),
        (2, 22, "1941-zhongguo-minzhengtongmeng-chengli-huizhi",
         "1941 年中国民主政团同盟成立大会会址——鲜宅（重庆）",
         "1941-03-19", "民盟前身 中国民主政团同盟成立大会会址",
         ["重庆"], ["黄炎培", "张澜", "梁漱溟", "左舜生"]),
        (2, 23, "1946-beiyoudang-tewu-qinfeng-bao", "1946 年被国民党特务捣毁的《秦风报》报社",
         "1946", "1946 国民党特务破坏民盟西北组织机关报《秦风·工商日报联合版》",
         ["西安"], ["成柏仁"]),
        (2, 24, "1946-nian-shengming-jianghua-neirong", "1946 年声明讲话内容",
         "1946", "1946 年民盟重要声明讲话档案", ["上海", "南京"], ["张澜", "沈钧儒"]),
        (6, 77, "1949qian-beijing-minmeng-biannian-shi", "北京市民盟组织编年史（1949 年 10 月 1 日前）",
         "1945-1949", "北京民盟组织 1945-1949 编年史", ["北京"], ["民盟"]),
        (8, 107, "jianguoqian-fujian-mengshi-ziliao-shang", "建国前福建盟史资料汇编（上）",
         "1946-1949", "1946-1949 福建民盟史料汇编上卷", ["福州", "厦门"], ["民盟"]),
        (8, 108, "jianguoqian-fujian-mengshi-ziliao-zhong", "建国前福建盟史资料汇编（中）",
         "1946-1949", "1946-1949 福建民盟史料汇编中卷", ["福州", "厦门"], ["民盟"]),
        (8, 109, "jianguoqian-fujian-mengshi-ziliao-xia", "建国前福建盟史资料汇编（下）",
         "1946-1949", "1946-1949 福建民盟史料汇编下卷", ["福州", "厦门"], ["民盟"]),
        (8, 116, "1946-1953-jiangsu-meng-biannian-shi", "江苏民盟编年史 1946-1953",
         "1946-1953", "江苏省民盟 1946-1953 编年史", ["南京", "苏州"], ["沈钧儒"]),
        (9, 124, "1941-1953-wuxi-meng-biannian-shi", "民盟编年史 1941-1953（无锡）",
         "1941-1953", "无锡民盟 1941-1953 编年史（覆盖中国民主政团同盟成立到新中国成立）",
         ["无锡", "重庆"], ["民盟"]),
        (10, 144, "1942-1949-minmeng-zai-shaanxi", "民盟在陕西",
         "1942-1949", "1942-1949 民盟在陕西（民盟西北组织核心史料）",
         ["陕西", "西安"], ["成柏仁", "杜斌丞", "杨明轩"]),
        (10, 145, "1942-1949-minmeng-zai-shaanxi-jing", "民盟在陕西（精）",
         "1942-1949", "1942-1949 民盟在陕西 精装本",
         ["陕西", "西安"], ["成柏仁", "杜斌丞", "杨明轩"]),
        (10, 148, "1944-1946-minmeng-zongbu-chongqing", "民盟总部所在地——重庆国府路 300 号",
         "1944-1946", "1944 改组后中国民主同盟总部所在地",
         ["重庆"], ["张澜", "沈钧儒"]),
        (10, 149, "1946-1949-minmeng-zongbu-shanghai", "民盟总部在沪活动纪实",
         "1946-1949", "民盟总部 1946-1949 在上海活动档案",
         ["上海"], ["张澜", "沈钧儒", "罗隆基"]),
        (10, 150, "1946-1949-nanfang-mengshi-shiling", "南方盟史拾零",
         "1946-1949", "民盟南方总支部 1946-1949 史料", ["广州", "香港"], ["李章达"]),
        (11, 158, "1942-2012-shaanxi-meng-70nian", "陕西民盟 70 年",
         "1942-2012", "1942-2012 陕西民盟组织史", ["陕西", "西安"], ["成柏仁", "杜斌丞", "杨明轩"]),
        (11, 159, "shaanxi-minmeng-shi", "陕西民盟史",
         "1942-2012", "陕西民盟组织史", ["陕西", "西安"], ["成柏仁", "杜斌丞", "杨明轩"]),
        (11, 161, "1942-shaanxi-tongzhanbu-meng-zhibu-renxuan",
         "陕西省委统战部关于民盟陕西省支部委员人选文件",
         "1942", "中共陕西省委对民盟陕西支部人事安排档案",
         ["陕西", "西安"], ["成柏仁", "杜斌丞", "杨明轩"]),
        (11, 164, "shaanxi-sheng-zhibu-choubei-weiyuanhui-mingdan",
         "陕西省支部筹备委员会名单", "1942",
         "民盟西北组织筹建核心档案", ["陕西", "西安"], ["成柏仁", "杜斌丞", "杨明轩"]),
        (12, 168, "shanghai-minmeng-biannian-shi", "上海民盟编年史",
         "1945-2018", "上海民盟 1945-2018 编年史",
         ["上海"], ["张澜", "沈钧儒", "罗隆基"]),
        (12, 178, "1939-1950-sichuan-meng-biannian-shi", "四川民盟编年史 1939-1950",
         "1939-1950", "四川省民盟 1939-1950 编年史（覆盖中国民主政团同盟成立到新中国成立）",
         ["成都", "重庆"], ["张澜", "张秀熟", "潘大逵"]),
        (13, 184, "1942-1949-xian-minmeng-xibei-zongzhibu-mimi-huodongdi",
         "西安市民盟西北总支部秘密活动地",
         "1942-1949", "1942-1949 民盟西北总支部地下活动地",
         ["西安"], ["杜斌丞", "杨明轩"]),
        (13, 185, "1943-xibei-ju-ierkuozhang-huiyi",
         "西北局关于第二次扩大会议情况报告",
         "1943", "民盟西北总支部第二次扩大会议报告",
         ["西安"], ["杜斌丞", "杨明轩", "成柏仁"]),
        (16, 233, "1947-1949-zhongyang-zongzhanhui-lianhehuiyi",
         "中央全会联合会议筹备委员会关于在若干大城市文件",
         "1947-1949", "民盟中央全会联合会议档案",
         ["上海", "南京"], ["沈钧儒"]),
        (16, 240, "1941-2014-chongqing-meng-shi-jing", "重庆民盟史（精）",
         "1941-2014", "1941-2014 重庆民盟组织史 精装本",
         ["重庆"], ["张澜", "黄炎培", "梁漱溟"]),
    ]
    for page, dde, cid, title, date, note, places, persons in core_anchors:
        r = make_record(cid, title, date, note, "person_tags", persons,
                       "place_tags", places, page=page, dde_id=dde)
        if r["candidate_id"] in existing:
            skipped.append(r["candidate_id"])
            continue
        r.update({"checked_at": args.checked_at, "checked_by": "claude-code",
                  "review_status": "needs_human_review",
                  "review_note": f"L3 needs_human_review 民盟核心档案；{note}；"
                                 "公开浏览页可见标题；升级 L2 需 cheer 登录会话 + 取得全文；升级 L1 需 cheer 提供 PDF/影像。"})
        rows.append(r)
        added.append(r["candidate_id"])

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {"added": added, "skipped": skipped, "applied": args.apply,
         "total_records": len(rows), "added_count": len(added)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())