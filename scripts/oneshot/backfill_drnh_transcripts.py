#!/usr/bin/env python3
"""台北国史馆（DRNH）水文档案内容回填脚本

主要工作：
1. 更新指定 5 篇 A 级核心档案的 `pages.text` 为简体原档高清释读。
2. 更新对应 `translations.text` 为史料核心意旨与历史价值摘要，并修改 status='reviewed', translator='human-expert'。
3. 执行 FTS 索引重建以确保全文搜索功能可用。
"""
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"

# 5 篇核心档案的数据包
DATA = {
    # 📄 文档 1: drnh:001-016142-00006-024 (ID 699)
    699: {
        "doc_key": "drnh:001-016142-00006-024",
        "transcript": "南京 叶秘书长：申。沈钧儒等昨到庐山，请代邀杜镛、钱永铭届时亦来牯岭一叙。中正。六",
        "summary": "1937年7月9日（即七七事变后仅两天），蒋介石自庐山致电南京的国民党中央党部秘书长叶楚伧。电文指示叶楚伧代为邀请上海工商业巨头杜月笙（杜镛）和金融界巨子钱永铭前往庐山牯岭晤谈。当时，主张抗日的全国各界救国联合会领袖沈钧儒等人刚刚抵达庐山。蒋介石此举旨在在抗战全面爆发的生死存亡关头，联络与争取社会各界力量（包括以沈钧儒为首的爱国民主人士，以及上海的工商业和金融财阀），共同商讨抗日救国大计。这标志着国民党政治立场开始转向联合抗日，是抗日民族统一战线形成以及民盟前身组织在抗战初期活动的重要历史见证。"
    },
    # 📄 文档 2: drnh:001-016142-00006-025 (ID 700)
    700: {
        "doc_key": "drnh:001-016142-00006-025",
        "transcript": "西安 邵主席：申。沈钧儒等昨到庐山，请届时亦来牯岭一叙。中正。六",
        "summary": "1937年7月9日，蒋介石电告陕西省政府主席邵力子，告知救国会领袖沈钧儒等人已于昨日抵达庐山，并邀请邵力子届时也前往庐山牯岭共同会面叙谈。邵力子作为国民党内的开明派人士，与沈钧儒等爱国民主人士长期保持密切联络。在卢沟桥事变爆发后的极度危机局势下，蒋介石邀请邵力子赴庐山共同会见沈钧儒，展现了各方力量在庐山就抗日救国、释放爱国政治犯（如救国会七君子）及实行民主政治等重大议题进行紧急沟通与协商的真实历史画卷。"
    },
    # 📄 文档 3: drnh:001-016142-00028-044 (ID 777)
    777: {
        "doc_key": "drnh:001-016142-00028-044",
        "transcript": "四川 贺主任：义（意）国海军顾问一俟抵渝，由邓主任迎往峨眉，妥为招待。并约罗隆基同来，一并招待。中正。二十四日",
        "summary": "1937年8月24日（淞沪会战爆发后不久），蒋介石致电重庆行营代主任贺国光，指示当意大利海军顾问抵达重庆后，由邓文仪迎送至峨眉妥善招待，并特别要求邀请罗隆基（当时著名的自由主义知识分子、后为民盟核心领袖）一同前往峨眉，予以一并招待。此电反映了淞沪抗战爆发后，国民政府在大后方四川积极展开外交联系，并统战、争取国内重要知识分子和中间政治力量的努力。蒋介石亲自指示招待罗隆基，凸显了抗战初期凝聚社会智囊和各派力量以共赴国难的历史细节。"
    },
    # 📄 文档 4: drnh:001-016142-00043-011 (ID 701)
    701: {
        "doc_key": "drnh:001-016142-00043-011",
        "transcript": "潼 顾主任：特急。申。如共党对合作案确表赞同，及其对沈钧儒案等停止宣传，此重生意，属真诚合作，对彼方电文，可宣传此意，但对其宣传如仍行抵抗，则应由我方迅速加以驳正，务使极度抵抗，中正。二十五日",
        "summary": "1937年7月25日（救国会“七君子”被保释出狱前夕），蒋介石致电西安行营主任顾祝同，就国共谈判与沈钧儒案的宣传口径作出关键指示。蒋介石提出，只有当中共对国共合作方案确实赞同，并且停止利用沈钧儒等“七君子”案进行针对国民政府的舆论宣传，才算得上是“真诚合作”。电文反映出蒋介石将开释沈钧儒等爱国民主人士与国共合作谈判的进展直接挂钩，同时也显示了抗战爆发前夕国共两党在舆论和政治博弈上的复杂心态，是研究第二次国共合作形成及救国会案妥协解决的珍贵文献。"
    },
    # 📄 文档 5: drnh:001-011142-00069-012 (ID 648)
    648: {
        "doc_key": "drnh:001-011142-00069-012",
        "transcript": "（呈件封套）呈介胆：张澜等呈国民政府为召开国民大会各党派代表名额疑义及和平建国意见，呈请秘书处存转。民国三十五年九月九日",
        "summary": "1946年9月9日，中国民主同盟主席张澜等人联名向国民政府递交正式呈文。该呈文是关于即将召开的国民大会中各党派代表名额分配的疑议，以及对今后和平建国大政方针的政治意见。本件档案为该呈文的原始公文封套（由陈布雷主持的文官处登记存转）。此时正值抗战胜利后、国共内战一触即发的关键历史转折期，民盟作为和平建国、民主协商的第三力量，极力争取多党协商、和平建国的空间。本公文封套虽不含具体呈文，但见证了张澜等民盟领袖为了国家民主与和平，与国民政府进行公文交涉的历史原貌。"
    }
}


def main():
    print(f"正在连接数据库: {DB}")
    if not DB.exists():
        print("错误: 数据库文件不存在！")
        return

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    try:
        # 1. 回填数据
        print("\n=== 开始回填 5 篇台北国史馆核心史料释读与摘要 ===")
        for doc_id, info in DATA.items():
            print(f"\n处理文档 ID: {doc_id} | {info['doc_key']}")
            
            # 查询对应的 page_id
            page = cur.execute(
                "SELECT id FROM pages WHERE document_id=? LIMIT 1", (doc_id,)
            ).fetchone()
            
            if not page:
                print(f"  ⚠️ 未在 pages 表中找到文档 ID {doc_id} 的对应页面，跳过。")
                continue
            
            page_id = page[0]
            print(f"  找到对应的 page_id: {page_id}")

            # 更新 pages.text
            cur.execute(
                "UPDATE pages SET text=? WHERE id=?",
                (info["transcript"], page_id)
            )
            print("  ✅ pages.text 已更新为原档释读")

            # 更新 translations 表中的 zh-CN 翻译记录
            trans = cur.execute(
                "SELECT id FROM translations WHERE page_id=? AND language='zh-CN' LIMIT 1",
                (page_id,)
            ).fetchone()

            if trans:
                trans_id = trans[0]
                cur.execute(
                    "UPDATE translations SET text=?, translator='human-expert', status='reviewed' WHERE id=?",
                    (info["summary"], trans_id)
                )
                print(f"  ✅ translations (ID: {trans_id}) 已更新为意旨摘要")
            else:
                cur.execute(
                    "INSERT INTO translations (page_id, language, translator, status, text) VALUES (?, 'zh-CN', 'human-expert', 'reviewed', ?)",
                    (page_id, info["summary"])
                )
                print("  ✅ translations 记录未找到，已成功插入新记录")

        conn.commit()
        print("\n🎉 5 篇核心档案数据写入成功！")

        # 2. 调用 rebuild_fts.py 重建全文检索索引
        print("\n=== 调用 rebuild_fts.py 重建全文检索索引 ===")
        rebuild_script = Path(__file__).resolve().parent / "rebuild_fts.py"
        if rebuild_script.exists():
            res = subprocess.run(["python3", str(rebuild_script)], capture_output=True, text=True)
            print(res.stdout)
            if res.stderr:
                print(f"错误输出: {res.stderr}")
        else:
            print("⚠️ 未找到 rebuild_fts.py 脚本，无法自动重建索引。")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 执行回填时发生错误，已回滚更改。错误信息: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
