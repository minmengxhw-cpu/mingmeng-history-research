#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "wilson_center"
PDF_DIR = OUT / "pdfs"
HTML_DIR = OUT / "mirrors"
TEXT_DIR = OUT / "text"
MANIFEST = OUT / "manifest.json"


DOCS = [
    {
        "doc_key": "wilson:134160",
        "title": "Democratic Parties and Groups in the Preparatory Committee to Convene a Political Consultative Conference",
        "date": "1949-07-07",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/democratic-parties-and-groups-preparatory-committee-convene-political-consultative",
        "mirror_url": "https://docslib.org/doc/7270969/july-07-1949-democratic-parties-and-groups-in-the-preparatory-committee-to-convene-a-political-consultative-conference",
        "kind": "html",
        "grade": "核心文献",
        "score": 98,
        "reason": "Wilson 档案中直接列出新政协预备委员会民主党派与团体，民盟史直接相关。",
    },
    {
        "doc_key": "wilson:122808",
        "title": "Record of Conversation between Soviet Ambassador in China Apollon Petrov and Zhou Enlai and Wang Ruofei",
        "date": "1945-10-05",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/record-conversation-between-soviet-ambassador-china-apollon-petrov-and-zhou-enlai-and-wang",
        "mirror_url": "https://docslib.org/doc/1932438/october-05-1945-record-of-conversation-between-soviet-ambassador-in-china-apollon-petrov-and-zhou-enlai-and-wang-ruofei",
        "kind": "html",
        "grade": "核心文献",
        "score": 92,
        "reason": "1945 重庆谈判时期苏联使馆视角，涉及中共、国民党与第三方政治格局。",
    },
    {
        "doc_key": "wilson:122809",
        "title": "Record of Conversation between Soviet Ambassador in China Apollon Petrov and Mao Zedong, Zhou Enlai and Wang Ruofei",
        "date": "1945-10-10",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/record-conversation-between-soviet-ambassador-china-apollon-petrov-and-mao-zedong-zhou-0",
        "mirror_url": "https://bannedthought.org/China/Individuals/MaoZedong/Other/Mao-Zhou-DiscussionWithSovietAmbassadorPetrov-1945-1010.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 82,
        "reason": "重庆谈判后期中共高层与苏联使馆会谈，构成民盟与政协语境的背景材料。",
    },
    {
        "doc_key": "wilson:113789",
        "title": "Cable, Mao Zedong to Stalin",
        "date": "1948-12-30",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/113789",
        "mirror_url": "https://www.commonprogram.science/documents/113789.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 78,
        "reason": "1948 年底毛泽东向斯大林通报当前局势，是新政协与联合政府筹备前夜的重要背景。",
    },
    {
        "doc_key": "wilson:112226",
        "title": "Cable, Terebin to Stalin [via Kuznetsov]",
        "date": "1949-01-10",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/112226",
        "mirror_url": "https://www.commonprogram.science/documents/112226.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 74,
        "reason": "1949 年初围绕和谈、调停与中共建政策略的苏方转报，补足新政协前政治语境。",
    },
    {
        "doc_key": "wilson:112436",
        "title": "Memorandum of Conversation between Anastas Mikoyan and Mao Zedong",
        "date": "1949-01-31",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/112436",
        "mirror_url": "https://docslib.org/doc/9184408/january-31-1949-memorandum-of-conversation-between-anastas-mikoyan-and-mao-zedong",
        "kind": "html",
        "grade": "核心文献",
        "score": 88,
        "reason": "毛泽东与米高扬讨论联合政府筹备、国共和谈和中共建政安排，直接关联新政协政治背景。",
    },
    {
        "doc_key": "wilson:113239",
        "title": "Memorandum of Conversation between Anastas Mikoyan and Mao Zedong",
        "date": "1949-02-03",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/113239",
        "mirror_url": "https://www.commonprogram.science/documents/113239.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 82,
        "reason": "米高扬与毛泽东继续讨论建政、外交和政治安排，补足 1949 年初新政协背景链条。",
    },
    {
        "doc_key": "wilson:121774",
        "title": "Anastas Mikoyan's Recollections of his Trip to China",
        "date": "1958-09-04",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/anastas-mikoyans-recollections-his-trip-china",
        "mirror_url": "https://www.commonprogram.science/documents/121774.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 80,
        "reason": "米高扬回忆录提供 1949 年中共与苏联沟通背景，可辅助理解新政协前后政治安排。",
    },
    {
        "doc_key": "wilson:113318",
        "title": "Memorandum of Conversation between Anastas Mikoyan and Mao Zedong",
        "date": "1949-02-04",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/113318",
        "mirror_url": "https://www.commonprogram.science/documents/113318.pdf",
        "kind": "pdf",
        "grade": "核心文献",
        "score": 90,
        "reason": "讨论新政协预备委员会、未来政权性质和中苏关系，是 1949 政治安排关键背景。",
    },
    {
        "doc_key": "wilson:113323",
        "title": "Memorandum of Conversation between Anastas Mikoyan and Mao Zedong",
        "date": "1949-02-05",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/memorandum-conversation-between-anastas-mikoyan-and-mao-zedong-1",
        "mirror_url": "https://www.commonprogram.science/documents/113323.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 84,
        "reason": "米高扬同毛泽东会谈，补足 1949 年初中苏沟通脉络。",
    },
    {
        "doc_key": "wilson:113377",
        "title": "Cable, Mao Zedong [via Kovalev] to Stalin",
        "date": "1949-06-14",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/cable-mao-zedong-kovalev-stalin",
        "mirror_url": "https://www.commonprogram.science/documents/113377.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 78,
        "reason": "毛泽东经科瓦廖夫向斯大林请示建政、军事与内战问题，关联新政权筹建背景。",
    },
    {
        "doc_key": "wilson:113379",
        "title": "Cable, Filippov [Stalin] to Mao Zedong [via Kovalev]",
        "date": "1949-06-18",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/cable-filippov-stalin-mao-zedong-kovalev",
        "mirror_url": "https://www.commonprogram.science/documents/113379.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 78,
        "reason": "斯大林就中国建政、军事和资源问题回复毛泽东，提供苏方政策背景。",
    },
    {
        "doc_key": "wilson:113382",
        "title": "Kovalev reports to Stalin advice on running a communist government",
        "date": "1949-07-06",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/113382",
        "mirror_url": "https://www.commonprogram.science/documents/113382.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 76,
        "reason": "科瓦廖夫致斯大林报告，反映苏方对中共建政的观察。",
    },
    {
        "doc_key": "wilson:liu-shaoqi-stalin-1949-07-27",
        "title": "Memorandum of Conversation between Liu Shaoqi and Stalin",
        "date": "1949-07-27",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/memorandum-conversation-between-liu-shaoqi-and-stalin",
        "mirror_url": "https://www.commonprogram.science/documents/27071949.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 82,
        "reason": "刘少奇访苏期间与斯大林会谈，构成新中国成立前中苏分工与建政背景。",
    },
    {
        "doc_key": "wilson:liu-shaoqi-mao-1949-07-18",
        "title": "Liu Shaoqi about his meeting with Stalin",
        "date": "1949-07-18",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/cable-liu-shaoqi-mao-zedong",
        "mirror_url": "https://www.commonprogram.science/documents/18071949.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 78,
        "reason": "刘少奇向毛泽东汇报会见斯大林情况，补足 1949 年中苏沟通链条。",
    },
    {
        "doc_key": "wilson:134156",
        "title": "Report from the Head of the Delegation of the CC of the Chinese Communist Party, 'The Current State of the Chinese Revolution'",
        "date": "1949-07-04",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/134156",
        "mirror_url": "https://www.commonprogram.science/documents/04071949.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 82,
        "reason": "刘少奇代表团向斯大林报告中国革命当前状态，包含新政权组织和统一战线政治背景。",
    },
    {
        "doc_key": "wilson:134157",
        "title": "Report from the Head of the Delegation of the Chinese Communist Party CC to Stalin",
        "date": "1949-07-06",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/134157",
        "mirror_url": "https://www.commonprogram.science/documents/134157.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 78,
        "reason": "刘少奇代表团关于苏联政府与社会结构的报告，关联中共建政制度设计背景。",
    },
    {
        "doc_key": "wilson:113353",
        "title": "Kovalev reports to Stalin on conversation with Mao Zedong",
        "date": "1949-04-13",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/113353",
        "mirror_url": "https://www.commonprogram.science/documents/113353.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 76,
        "reason": "1949 年 4 月科瓦廖夫转述毛泽东意见，是中苏建政沟通背景材料。",
    },
    {
        "doc_key": "wilson:mao-liu-1949-12-18",
        "title": "Telegram Mao Zedong to Liu Shaoqi about meeting with Stalin",
        "date": "1949-12-18",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/110393",
        "mirror_url": "https://www.commonprogram.science/documents/18-12-1949.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 74,
        "reason": "毛泽东访苏后向刘少奇通报会见斯大林情况，补足 1949 年底中苏关系背景。",
    },
    {
        "doc_key": "wilson:113441",
        "title": "Report, Kovalev to Stalin",
        "date": "1949-12-24",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/113441",
        "mirror_url": "https://www.commonprogram.science/documents/113441.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 80,
        "reason": "科瓦廖夫向斯大林报告中共中央政策与实践问题，涉及知识分子、民族资产阶级和新政权运行背景。",
    },
    {
        "doc_key": "wilson:111240",
        "title": "Record of conversation between Stalin and Mao Zedong",
        "date": "1949-12-16",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/111240",
        "mirror_url": "https://www.commonprogram.science/documents/111240.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 76,
        "reason": "毛泽东首次访苏会谈，反映新中国成立后中苏战略沟通。",
    },
    {
        "doc_key": "wilson:roshchin-zhou-1949-11-10",
        "title": "Roshchin Memorandum of Conversation with Prime Minister and Foreign Minister Zhou Enlai",
        "date": "1949-11-10",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/diary-nv-roshchin-memorandum-conversation-prime-minister-zhou-enlai-10-november-1949",
        "mirror_url": "https://www.commonprogram.science/documents/10111949.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 76,
        "reason": "新政协后周恩来与苏联大使罗申会谈，反映建国初期外交与政治安排背景。",
    },
    {
        "doc_key": "wilson:119300",
        "title": "On the People's Democratic Dictatorship: In Commemoration of the Twenty-eighth Anniversary of the Communist Party of China",
        "date": "1949-06-30",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/119300",
        "mirror_url": "https://www.commonprogram.science/documents/ON%20THE%20PEOPLE's%20dictatorship.pdf",
        "kind": "pdf",
        "grade": "相关文献",
        "score": 78,
        "reason": "毛泽东 1949 年论人民民主专政文本，说明民主党派、新政协与新政权合法性框架的政治语境。",
    },
    {
        "doc_key": "wilson:117031",
        "title": "Report, Peng Dehuai to Mao Zedong and the CCP Central Committee (Excerpt)",
        "date": "1958-06-05",
        "original_url": "https://digitalarchive.wilsoncenter.org/document/117031",
        "mirror_url": "https://docslib.org/doc/2763319/june-05-1958-report-peng-dehuai-to-mao-zedong-and-the-ccp-central-committee-excerpt",
        "kind": "html",
        "grade": "相关文献",
        "score": 62,
        "reason": "1958 年国防报告摘录中回顾新政协、民主党派和中央人民政府组成，可作为民盟早期建政语境的延伸材料。",
    },
]


def urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36",
            "Accept": "text/html,application/pdf,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def extract_html_text(path: Path) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    article = soup.select_one("#pubText article") or soup.select_one("article") or soup.body or soup
    return " ".join(article.get_text(" ", strip=True).split())


def extract_pdf_text(path: Path, out_txt: Path) -> str:
    subprocess.run(["pdftotext", "-layout", str(path), str(out_txt)], check=True)
    return out_txt.read_text(encoding="utf-8", errors="replace").strip()


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    for doc in DOCS:
        slug = doc["doc_key"].replace("wilson:", "").replace("/", "_")
        ext = "pdf" if doc["kind"] == "pdf" else "html"
        raw_path = (PDF_DIR if ext == "pdf" else HTML_DIR) / f"{slug}.{ext}"
        txt_path = TEXT_DIR / f"{slug}.txt"

        status = "ok"
        error = ""
        try:
            if not raw_path.exists() or raw_path.stat().st_size < 1024:
                raw_path.write_bytes(urlopen_bytes(doc["mirror_url"]))
                time.sleep(1)
            if doc["kind"] == "pdf":
                text = extract_pdf_text(raw_path, txt_path)
            else:
                text = extract_html_text(raw_path)
                txt_path.write_text(text, encoding="utf-8")
            if len(text) < 500:
                status = "short_text"
                error = f"extracted text too short: {len(text)}"
        except (OSError, subprocess.CalledProcessError, urllib.error.URLError) as exc:
            status = "failed"
            error = str(exc)

        record = dict(doc)
        record.update(
            {
                "status": status,
                "error": error,
                "local_raw": str(raw_path.relative_to(ROOT)) if raw_path.exists() else "",
                "local_txt": str(txt_path.relative_to(ROOT)) if txt_path.exists() else "",
                "text_chars": txt_path.stat().st_size if txt_path.exists() else 0,
            }
        )
        records.append(record)
        print(f"{status:10s} {doc['doc_key']} {record['text_chars']} chars")
        if error:
            print(f"  {error}")

    MANIFEST.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in records if r["status"] == "ok")
    print(f"\nWilson mirror fetch complete: {ok}/{len(records)} ok")
    print(MANIFEST.relative_to(ROOT))


if __name__ == "__main__":
    main()
