#!/usr/bin/env python3
"""把 CIA archive.org 镜像核心 21 篇民盟档案入 zipei_data sqlite

入库流程：
1. 读 data/cia_meng/manifest.json + 各档案 OCR text
2. 清理 OCR 噪声（页眉/页脚/表单字段/批注水印等）
3. 写入 sources / documents / pages / page_fts 表
4. 标记 source_platform='cia'，与 FRUS 区分

翻译由后续 translate_cia_meng.py 单独跑。
"""
import sqlite3, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "research_index.sqlite"
CIA_DIR = ROOT / "data" / "cia_meng"
MANIFEST = CIA_DIR / "manifest.json"
CORE_IDENTS_FILE = Path("/tmp/cia_core_idents.json")


def clean_ocr_text(raw: str) -> str:
    """去除 archive.org OCR 噪声（CIA 文档常见模式）"""
    text = raw

    # 1. 删除 archive.org djvu 加的页面分隔符（U+000C）
    text = text.replace("\x0c", "\n\n--- 页 ---\n\n")

    # 2. 去除 "Approved For Release ..." 解密水印
    text = re.sub(r'Approv[ed]+\s+For\s+Release.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'For\s+Release.*?\d{4}/\d{1,2}/\d{1,2}.*', '', text, flags=re.IGNORECASE)

    # 3. 去除 "CIA-RDP82-..." 等档案号水印行（独占行的）
    text = re.sub(r'^\s*CIA-RDP[\w-]+\s*$', '', text, flags=re.MULTILINE)

    # 4. 去 CIA 表单"STATE NAVY AIR FBI ARMY" 等分发清单
    text = re.sub(
        r'^\s*(STATE|NAVY|ARMY|AIR|FBI|NSRB|DISTRIBUTION|CONFIDENTIAL)\s*[\|\[\]X\s]*$',
        '', text, flags=re.MULTILINE,
    )

    # 5. 去机密标记 (CONFIDENTIAL / SECRET / RESTRICTED 独占行)
    text = re.sub(
        r'^\s*(CONFIDENTIAL|SECRET|RESTRICTED|TOP SECRET|UNCLASSIFIED)[\.\,]?\s*$',
        '', text, flags=re.MULTILINE,
    )

    # 6. 删除 25X1A 等保密码占位
    text = re.sub(r'\b25X\d[A-Z]?\b', '', text)

    # 7. 删除 "This document is hereby regraded..." 等长水印
    text = re.sub(
        r'This document is hereby regraded.*?(?:United States\.|$)',
        '', text, flags=re.DOTALL | re.IGNORECASE,
    )

    # 8. 合并多个连续空行
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # 9. trim
    return text.strip()


def clean_title(title: str) -> str:
    """从 archive.org 标题里抽干净的档案标题"""
    if not title:
        return ""
    # archive.org 上有时是 "CIA Reading Room cia-rdp...: REAL TITLE"
    m = re.search(r': (.+)$', title)
    if m and title.startswith('CIA Reading Room cia-'):
        return m.group(1).strip()
    return title.strip()


def main():
    if not CORE_IDENTS_FILE.exists():
        print(f"ERR: 找不到 {CORE_IDENTS_FILE}", file=sys.stderr)
        sys.exit(1)
    core_idents = set(json.load(open(CORE_IDENTS_FILE)))
    manifest = json.load(open(MANIFEST))

    # 只保留核心 21 篇
    core_docs = [m for m in manifest if m['identifier'] in core_idents]
    print(f"manifest: {len(manifest)} 篇，核心: {len(core_docs)} 篇")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. 确保 source 存在
    cur.execute(
        """SELECT id FROM sources WHERE source_type='cia' AND source_id='ciareadingroom' LIMIT 1"""
    )
    row = cur.fetchone()
    if row:
        source_id = row['id']
        print(f"source 已存在: id={source_id}")
    else:
        cur.execute(
            """INSERT INTO sources (source_type, source_id, title, origin_url, local_path)
               VALUES (?, ?, ?, ?, ?)""",
            (
                "cia",
                "ciareadingroom",
                "CIA Records Reading Room (archive.org mirror)",
                "https://archive.org/details/ciareadingroom",
                str(CIA_DIR),
            ),
        )
        source_id = cur.lastrowid
        print(f"新建 source: id={source_id}")

    inserted = 0
    skipped = 0
    for d in core_docs:
        ident = d['identifier']
        doc_key = f"cia-meng:{ident}"
        # 已入库则跳过
        cur.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,))
        if cur.fetchone():
            skipped += 1
            continue

        title = clean_title(d.get('title', ''))
        date_guess = d.get('date', '')[:10]
        detail_url = d.get('detail_url') or f"https://archive.org/details/{ident}"
        # 读 OCR text: archive.org 实际文件名带 identifier 前缀
        doc_dir = CIA_DIR / 'documents' / ident
        txt_candidates = list(doc_dir.glob('*_djvu.txt'))
        if not txt_candidates:
            print(f"  ⚠ 找不到 OCR text: {doc_dir}")
            continue
        txt_path = txt_candidates[0]
        raw = txt_path.read_text(encoding='utf-8', errors='replace')
        cleaned = clean_ocr_text(raw)

        # 写 documents
        cur.execute(
            """INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id,
                                       doc_number, title, date_guess, url, local_html, local_txt,
                                       hit_type, matched_terms, source_platform)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                doc_key,
                "CIA-CREST",                       # volume_id
                "CIA Records Reading Room",        # volume_title
                ident,                             # doc_id
                "",                                # doc_number
                title,                             # title
                date_guess,
                detail_url,
                "",                                # local_html
                str(txt_path.relative_to(ROOT)),   # local_txt
                "core",                            # hit_type
                d.get('matched_term', ''),         # matched_terms
                "cia",                             # source_platform
            ),
        )
        document_id = cur.lastrowid

        # 写 pages（每篇档案作为一个 page，整篇 OCR text）
        cur.execute(
            """INSERT INTO pages (document_id, page_label, page_url, text)
               VALUES (?, ?, ?, ?)""",
            (document_id, "1", detail_url, cleaned),
        )
        page_id = cur.lastrowid

        # 写 FTS（与 FRUS 同结构）
        try:
            cur.execute(
                """INSERT INTO page_fts (volume_id, doc_id, title, page_label, matched_terms, text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("CIA-CREST", ident, title, "1", d.get('matched_term', ''), cleaned),
            )
        except sqlite3.OperationalError as e:
            print(f"  FTS 插入 skip ({e})")

        # 文档分级（核心档案）
        cur.execute(
            """INSERT OR REPLACE INTO document_classifications
               (document_id, grade, score, reason, needs_review)
               VALUES (?, ?, ?, ?, ?)""",
            (document_id, "核心文献", 90, "CIA 民盟主题核心档案（archive.org 镜像）", 0),
        )

        inserted += 1
        print(f"  ✓ [{date_guess}] {title[:60]}  (page_id={page_id})")

    conn.commit()
    print()
    print(f"=== 入库完成 ===")
    print(f"  新入库: {inserted} 篇")
    print(f"  跳过(已存在): {skipped}")

    # 总数验证
    cur.execute("SELECT COUNT(*) FROM documents WHERE source_platform='cia'")
    print(f"  CIA documents 总数: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM pages p JOIN documents d ON d.id=p.document_id WHERE d.source_platform='cia'")
    print(f"  CIA pages 总数: {cur.fetchone()[0]}")
    conn.close()


if __name__ == '__main__':
    main()
