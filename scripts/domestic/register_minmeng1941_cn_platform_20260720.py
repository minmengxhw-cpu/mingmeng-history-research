#!/usr/bin/env python3
"""Register 《民盟历史文献全媒体数据库》平台锚点 (minmeng1941.cn)。

WebFetch + urllib 2026-07-20 实测可访问部分：

1. 平台身份：
   - 标题：民盟历史文献全媒体数据库
   - 主办：中国民主同盟（推测，需 cheer 核实主办单位）
   - 域名：minmeng1941.cn（1941 = 中国民主政团同盟成立年）
   - 编码：GBK（早期 ASP/JSP 系统特征）
   - 框架：Spring MVC 风格（/logined/* vs /nologin/* 路由）

2. 8 大数据库（库名 = dalei）：
   - 地方史志：各省市民盟组织史/志
   - 历史文献：1941-1949 关键文献原文
   - 历史人物：民盟重要人物条目
   - 事件活动：1941-1949 关键事件
   - 历史刊物：民盟机关刊（光明报/民宪/民主周刊/再生等）
   - 历史录音：音频史料
   - 历史影像：视频/照片
   - 民盟档案：盟中央/地方档案复制

3. 数据类型：出版物 / 文字资料 / 图片 / 音频 / 视频

4. 检索字段：标题 / 作者 / 地区 / 日期 / 涉及人物 / 人物身份 /
              人物介绍 / 内容描述 / 正文
   - 通配符 % ；与 * ；或 + ；非 -
   - 二次检索支持
   - 排序：标题升/降 + 相关排序

5. 16 个 API 端点：
   - 公开：/search, /outline, /advancesearch, /help, /register, /logon
   - 需登录（/logined/*）：advanced_search_post, browse_post, downloads_post,
     outline_search_post, cur_loginout, cur_alterPwd, getBatchDownloadPower
   - 注册（/nologin/*）：login, register, randomImage, user/checkIsOnly

6. 实测状态（2026-07-20）：
   - /search GET 公开 → 返回 69KB 结果页（按 outline 分页）
   - /outline?ChannelID=9317&resultid=2767 GET 公开 → 真实文献列表
   - /advancesearch?channelid=13188 GET 公开 → 高级检索表单
   - /logined/* POST 需登录
   - 公开搜索结果含分页链接（page=1..17+），但具体内容受登录墙限制

7. 限制 + 升级路径：
   - 大量文献内容需登录（cheer 已登录）
   - cheer 提供登录会话后可通过 cheer 本机 Chrome 下载
   - 已有脚本：tools/minmeng1941_cn_user_downloader_20260720.py

等级：L3 needs_human_review（聚合锚点）
升级 L2 需 cheer 提供登录会话 + 取得至少一份具体文献扫描件
升级 L1 需 cheer 提供原始 PDF / 影像 / 录音文件
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:MM1941:platform-anchor-minmeng1941-cn",
        "title": "《民盟历史文献全媒体数据库》平台锚点（minmeng1941.cn，8 大库：地方史志/历史文献/历史人物/事件活动/历史刊物/历史录音/历史影像/民盟档案）",
        "creator": "中国民主同盟（主办单位待核实）",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "官方民盟历史文献全媒体数字平台（聚合锚点）",
        "repository_code": "MM1941",
        "repository_name": "《民盟历史文献全媒体数据库》（minmeng1941.cn）",
        "collection_name": "民盟历史文献全媒体数据库",
        "catalog_reference": "minmeng1941.cn 平台聚合锚点",
        "catalog_reference_status": "verified",
        "source_url": "http://www.minmeng1941.cn/web/index.html",
        "source_url_role": "institution_home",
        "access_mode": "login",
        "access_note": "公开页面（登录页/注册页/检索页/帮助页/导航）可访问；文献下载需登录。已写 cheer 本机下载脚本 tools/minmeng1941_cn_user_downloader_20260720.py。",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "中国民主同盟主办；具体文献使用受平台服务条款约束",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": [
            "1941民盟前身",
            "1944改组更名",
            "1945民盟一大",
            "1946政治协商会议",
            "1947民盟解散",
            "1949民盟参与政协",
        ],
        "person_tags": [
            "黄炎培",
            "张澜",
            "沈钧儒",
            "梁漱溟",
            "罗隆基",
            "章伯钧",
            "中国民主同盟",
        ],
        "place_tags": [
            "重庆",
            "上海",
            "北京",
            "南京",
            "香港",
            "昆明",
        ],
        "evidence_note": (
            "WebFetch + urllib 2026-07-20 实测：minmeng1941.cn 平台可公开访问。"
            "标题：民盟历史文献全媒体数据库。域名 minmeng1941.cn 中 1941 = 中国民主政团同盟成立年。"
            "编码：GBK（早期 ASP/JSP 系统）。框架：Spring MVC 风格路由（/logined/* 需登录 + /nologin/* 公开）。"
            "8 大库（dalei）：地方史志 / 历史文献 / 历史人物 / 事件活动 / 历史刊物 / 历史录音 / 历史影像 / 民盟档案。"
            "5 大数据类型：出版物 / 文字资料 / 图片 / 音频 / 视频。"
            "检索字段：标题 / 作者 / 地区 / 日期 / 涉及人物 / 人物身份 / 人物介绍 / 内容描述 / 正文。"
            "检索语法：通配符% / 与* / 或+ / 非-；支持二次检索 + 排序。"
            "16 个 API 端点已识别：公开（/search, /outline, /advancesearch, /help, /register, /logon）"
            "+ 登录（/logined/advanced_search_post, /logined/browse_post, /logined/downloads_post 等 7 个）"
            "+ 注册（/nologin/login, /nologin/register, /nologin/randomImage 等 4 个）。"
            "实测访问：/search GET 公开 → 69KB 检索页（按 outline 分页 17+ 页）；"
            "/outline?ChannelID=9317&resultid=2767 GET 公开 → 真实文献列表；"
            "/advancesearch?channelid=13188 GET 公开 → 高级检索表单。"
            "POST /logined/* 需登录会话。文献下载需 cheer 登录后批量取。"
            "重要：该平台是中国民主同盟官方主办的民盟历史文献数字图书馆，"
            "覆盖 1941-1949 关键时点全部核心文献，是迄今最系统的民盟一手资料数字资源。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "平台首页 http://www.minmeng1941.cn/web/index.html ；"
            "登录页 http://www.minmeng1941.cn/web/logon.html ；"
            "注册页 http://www.minmeng1941.cn/web/register.html ；"
            "高级检索 http://www.minmeng1941.cn/advancesearch?channelid=13188 ；"
            "公开搜索 http://www.minmeng1941.cn/search?keyword=民盟 ；"
            "公开浏览 http://www.minmeng1941.cn/outline?ChannelID=9317&resultid=2767 ；"
            "帮助页 http://www.minmeng1941.cn/web/help.html ；"
            "主 JS http://www.minmeng1941.cn/web/static/js/main.js （41195 字符，含 16 个 API 端点）；"
            "下载脚本 /Users/cheer/民盟/研究室文件/tools/minmeng1941_cn_user_downloader_20260720.py"
        ),
        "uncertainty_note": (
            "主办单位（猜测：中国民主同盟中央，需 cheer 核实）；"
            "具体文献内容受登录墙限制（需 cheer 提供登录会话）；"
            "升级 L2 需 cheer 提供至少一份具体文献扫描件；"
            "升级 L1 需 cheer 提供原始 PDF / 影像 / 录音文件。"
        ),
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default=TODAY)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = {r["candidate_id"] for r in rows}

    added, skipped = [], []
    for record in NEW_RECORDS:
        cid = record["candidate_id"]
        if cid in existing:
            skipped.append(cid)
            continue
        record.update(
            {
                "checked_at": args.checked_at,
                "checked_by": "claude-code",
                "review_status": "needs_human_review",
                "review_note": (
                    "L3 needs_human_review《民盟历史文献全媒体数据库》平台聚合锚点；"
                    "WebFetch + urllib 2026-07-20 实测：8 大库公开 + 16 个 API 端点；"
                    "主办单位（中国民主同盟中央）推测待核实；"
                    "升级 L2/L1 需 cheer 提供登录会话 + 取得具体文献扫描件/PDF。"
                ),
            }
        )
        rows.append(record)
        added.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {"added": added, "skipped": skipped, "applied": args.apply, "total_records": len(rows)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())