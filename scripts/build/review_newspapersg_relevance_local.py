#!/usr/bin/env python3
"""Local relevance review and title translation for NewspaperSG.

This does not translate full OCR text. It provides a deterministic audit layer
while the API-based full translation job is unavailable.
"""
from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
OUT_DIR = ROOT / "data" / "newspapersg"
TITLE_CSV = OUT_DIR / "title_translations.csv"
REVIEW_CSV = OUT_DIR / "relevance_review.csv"


TITLE_ZH = {
    '"QUIT CHINA WEEK" 20,000 Chinese Have Already Signed Petition To Truman': "“退出中国周”：两万名华人已签署致杜鲁门请愿书",
    '"RISE AGAINST NANKING DICTATORSHIP" APPEAL': "“起来反对南京独裁”呼吁",
    '"It Will Have Profound Effects Abroad"': "“将在海外产生深远影响”",
    '"U.S. Prolonging Civil War In China By Aiding Kuomintang"': "“美国援助国民党正在延长中国内战”",
    "'International' Rally in Singapore urges Americans Quit China": "新加坡“国际”集会敦促美军退出中国",
    "20,000 Sign \"Quit China\" Petition": "两万人签署“退出中国”请愿书",
    "A. DENIAL": "罗隆基否认提交备忘录",
    "ANTI-CHIANG WEEK HERE": "本地发起反蒋周",
    "Another Political Army In China?": "中国又一支政治力量？",
    "Blast Against Democratic League Hint Kuomintang May Outlaw It": "抨击民盟：国民党或将其取缔",
    "CHINA DEMOCRATIC LEAGUE DECLARED UNLAWFUL": "中国民主同盟被宣布为非法团体",
    "CHINA DEMOCRATIC LEAGUE OUTLAWED": "中国民主同盟被取缔",
    "CHINA INVASION REPORT DENIED": "否认入侵中国报道",
    "CHINA'S MAGNA CARTA": "中国的大宪章",
    "CHINESE GO VERNMENT OUTLAWS DEMOCRATIC LEAGUE": "中国政府取缔民主同盟",
    "COMMUNIST CHINA DEMANDS EARLY WITHDRAWAL OF U.S. FORCES FROM JAPAN": "中共方面要求美军尽早撤出日本",
    "CONCESSION TO BANNED LEAGUE": "对被禁民盟的让步",
    "China As-You-Were": "中国局势依旧",
    "China Democrat In Penang": "中国民主人士抵槟城",
    "China Democratic League Outlawed": "中国民主同盟被取缔",
    "China Democratic League Plans Pan-Malayan H. Q.": "中国民主同盟计划设立泛马来亚总部",
    "China Democratic League Plans To Establish Pan-Malayan H.Q.": "中国民主同盟计划建立泛马来亚总部",
    "China Political Party In Burma": "中国政治党派在缅甸活动",
    "China: New Hope": "中国：新的希望",
    "China's Charter Of Freedom": "中国的自由宪章",
    "China's Third Party May Break Deadlock": "中国第三党或可打破僵局",
    "Chinese Greetings": "华人致意",
    "Chinese seek release of Author in Sumatra": "华人要求释放苏门答腊作家",
    "Kuomintang Blamed For Deadlock": "国民党被指造成僵局",
    "Coalition Government For China Urged": "敦促中国组织联合政府",
    "Complete Deadlock In China": "中国局势完全陷入僵局",
    "Compromise Hopes In Chungking": "重庆妥协希望",
    "DEMOCRATIC LEAGUE MEMBERS TO LEE?": "民主同盟成员将离沪？",
    "Democratic League Causes New Hitch In China Talks": "民主同盟使中国谈判再生波折",
    "Democratic League Indicted": "民主同盟遭指控",
    "Democrats Have New Formula To End War": "民主派提出结束内战的新方案",
    "Dynamiting The Bridge": "炸毁桥梁",
    "EX-DAIF ORCE MEN SEEK POLITICAL REFUGE HERE": "前军人来此寻求政治庇护",
    "Exemption To Foreign Political Bodies In S'pore Withdraw": "新加坡撤销外国政治团体登记豁免",
    "Leftist Chinese Reject Chiang's Election": "左翼华人反对蒋介石当选",
    "Local Chinese Launch 'Quit China Week' Today": "本地华人今日发起“退出中国周”",
    "MALAYA BRANCH OF DEMOCRATIC LEAGUE WILL CONTINUE TO FUNCTION": "民主同盟马来亚分部将继续活动",
    "MINORITY PARTIES": "少数党派",
    "MR. TAN KAH KEE ACCLAIMED LEADER AT MASS RALLY": "陈嘉庚在群众大会上获推为领袖",
    "Malayan Administration Carrying'On Anti-Chinese Policy?": "马来亚当局在推行反华政策吗？",
    "Manchuria: Plan To End Strife Rejected": "满洲：结束冲突方案遭拒",
    "Meeting Ends In \"Free For All\"": "会议演变为混乱冲突",
    "Message From The Director, China Democratic League, Singapore": "中国民主同盟新加坡负责人来函",
    "NO INTERFERENCE IN LOCAL POLITICS": "不干预本地政治",
    "Overseas Democratic League's Decision": "海外民主同盟的决定",
    "POLITICAL EVOLUTION OF MALAYA HAS BEGUN": "马来亚政治演进已经开始",
    "Peace Delegates Beaten Up": "和平代表遭殴打",
    "Peace Necessary": "和平是必要的",
    "Police Guard Shanghai Democratic League Hq": "警方守卫上海民主同盟总部",
    "RED CHINA SEEKS SHARE IN JAP TREATY": "红色中国要求参与对日和约",
    "REDS IN BURMA PREPA TO INVADE CHINA": "缅甸红色力量据称准备进攻中国",
    "Rights Of Overseas Chinese": "海外华人的权利",
    "S'hai Police take Over Democratic League I lqrs.": "上海警方接管民主同盟总部",
    "S'pore Branch Of, C. D. L. To Continue, Despite Nanking Ban": "虽遭南京取缔，中国民主同盟新加坡分部仍将继续",
    "S'pore Chinese Cable Truman": "新加坡华人致电杜鲁门",
    "SPORE REDS LAUNCH ANTI-CHIANG WEEK": "新加坡左翼发起反蒋周",
    "Sequel To Democratic League Ban": "民主同盟被禁的后续",
    "THE MASTER MIND": "幕后策划者",
    "TALKS ON REORGANIZATION OF CHINESE GOVERNMENT": "关于改组中国政府的会谈",
    "TWO CHINESE PARTIES LOSE STATUS": "两个中国政党失去合法地位",
    "The Far East And The Next World War": "远东与下一场世界大战",
    "Untitled": "无题报道",
    "中國民主同盟新加坡分部前日成立選出臨時執委七人": "中国民主同盟新加坡分部前日成立，选出临时执委七人",
    "中國民盟雪分部籌委會成立": "中国民盟雪兰莪分部筹委会成立",
    "傳政府已下令總攻擊張垣延安亦廣播總動員中共民盟正式拒絕參加國民大會政府接受馬帥建議兩會同時舉行": "传政府已下令总攻击张垣，延安亦广播总动员；中共、民盟正式拒绝参加国民大会",
    "前民盟黨員均得自由": "前民盟党员均可自由活动",
    "各地僑胞紛紛召開反對內戰大會致電民主同盟加緊督促實現全面停戰": "各地侨胞纷纷召开反内战大会，致电民主同盟促成全面停战",
    "平教授請政府收囘民盟非法令張瀾將自動解散民盟所謂自由份子多擬逃往香港": "平津教授请政府收回民盟非法令，张澜将自动解散民盟，所谓自由分子多拟逃往香港",
    "庇朥警察懷疑民盟召傳搜查無所獲前被拘禁現釋放者尚守法": "庇朥警方怀疑民盟活动，传召搜查无所获；前被拘禁后获释者仍守法",
    "張君勱組黨將告實現": "张君劢组党将告实现",
    "斥胡愈之的謬論": "驳斥胡愈之的谬论",
    "本坡民盟辦事處負責人對時局發表談話": "本坡民盟办事处负责人就时局发表谈话",
    "民盟星辦事處召開盟員茶話會歡迎莊明理先生報告祖國政情": "民盟新加坡办事处召开盟员茶话会，欢迎庄明理先生报告祖国政情",
    "民盟勾結共匪事實（二）": "民盟勾结中共事实（二）",
    "民盟勾結共匪事實四": "民盟勾结中共事实（四）",
    "民盟總部自港遷平": "民盟总部由香港迁往北平",
    "民盟辦事處主任胡愈之給王吉士先生的公開信": "民盟办事处主任胡愈之致王吉士先生公开信",
    "民盟領袖羅隆基又責美協助國軍中立界對東北局勢抱悲觀": "民盟领袖罗隆基再责美国协助国军，中立界对东北局势悲观",
    "海外民盟如繼續活動政府將另以辦法取締": "海外民盟如继续活动，政府将另行办法取缔",
    "當地政府對民盟不擬採任何動作": "当地政府对民盟暂不采取任何动作",
    "聯邦政府宣佈中國民主同盟為非法團體": "联邦政府宣布中国民主同盟为非法团体",
    "關於李公樸案論爭民盟堅持反對特務暗殺國新社記者訪問胡愈之": "关于李公朴案论争：民盟坚持反对特务暗杀，国新社记者访胡愈之",
    "李公樸聞一多被剌案政府决嚴令澈查彭宣傳部長答記者問張主任電滇省緝兇手": "李公朴、闻一多被刺案：政府决定严令彻查，宣传部长答记者问",
}


DIRECT_TERMS = [
    "china democratic league",
    "chinese democratic league",
    "中国民主同盟",
    "中國民主同盟",
    "民盟",
    "民主同盟",
]
LEAGUE_TERMS = ["democratic league"]
PERSON_TERMS = [
    "lo lung-chi",
    "chang lan",
    "huang yen-pei",
    "li kung-pu",
    "wen i-to",
    "hu yuzhi",
    "胡愈之",
    "李公樸",
    "李公朴",
    "聞一多",
    "闻一多",
    "張君勱",
    "张君劢",
    "羅隆基",
    "罗隆基",
]
FALSE_POSITIVE_TERMS = [
    "malayan democratic union",
    "malayan democratic league",
    "taiwan democratic league",
    "台湾民主同盟",
    "臺灣民主同盟",
    "馬來亞民主",
    "马来亚民主",
]


def classify(title: str, matched_terms: str, text: str) -> tuple[str, int, str, int]:
    hay = f"{title}\n{matched_terms}\n{text}".lower()
    if any(term in hay for term in FALSE_POSITIVE_TERMS):
        return "前台不展示", 10, "名称相近但不是中国民主同盟。", 1
    direct = any(term.lower() in hay for term in DIRECT_TERMS)
    league = any(term in hay for term in LEAGUE_TERMS)
    person = any(term.lower() in hay for term in PERSON_TERMS)
    if direct:
        return "核心文献", 92, "直接出现中国民主同盟、民盟组织或海外分部。", 0
    if league and person:
        return "核心文献", 86, "民主同盟与民盟核心人物或事件同时出现。", 0
    if league:
        return "相关文献", 76, "出现 Democratic League，语境为中国内战、国民党、南京政府或海外华人政治活动。", 0
    if person:
        return "人物关联", 64, "未直接出现民盟名称，但关联民盟核心人物或李公朴、闻一多等关键事件。", 0
    return "前台不展示", 20, "本地规则未检出与中国民主同盟的密切关联。", 1


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT d.id AS document_id, d.doc_key, d.title, d.date_guess, d.matched_terms,
               group_concat(p.text, '\n') AS full_text
        FROM documents d
        JOIN pages p ON p.document_id=d.id
        WHERE d.source_platform='newspapersg'
        GROUP BY d.id
        ORDER BY d.date_guess, d.doc_key
        """
    ).fetchall()

    review_rows: list[dict[str, object]] = []
    titles: dict[str, str] = {}
    for row in rows:
        title = row["title"] or ""
        title_zh = TITLE_ZH.get(title, title)
        titles[title] = title_zh
        grade, score, reason, needs_review = classify(
            title,
            row["matched_terms"] or "",
            row["full_text"] or "",
        )
        conn.execute(
            """
            INSERT INTO document_classifications(document_id, grade, score, reason, needs_review)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                grade=excluded.grade,
                score=excluded.score,
                reason=excluded.reason,
                needs_review=excluded.needs_review
            """,
            (row["document_id"], grade, score, reason, needs_review),
        )
        review_rows.append(
            {
                "doc_key": row["doc_key"],
                "date": row["date_guess"] or "",
                "title": title,
                "title_zh": title_zh,
                "grade": grade,
                "score": score,
                "needs_review": needs_review,
                "reason": reason,
            }
        )
    conn.commit()
    conn.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with TITLE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "title_zh"])
        for title in sorted(titles):
            writer.writerow([title, titles[title]])

    with REVIEW_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["doc_key", "date", "title", "title_zh", "grade", "score", "needs_review", "reason"],
        )
        writer.writeheader()
        writer.writerows(review_rows)

    counts: dict[str, int] = {}
    for row in review_rows:
        counts[row["grade"]] = counts.get(row["grade"], 0) + 1
    print(f"reviewed {len(review_rows)} NewspaperSG docs")
    print(counts)
    print(TITLE_CSV)
    print(REVIEW_CSV)


if __name__ == "__main__":
    main()
