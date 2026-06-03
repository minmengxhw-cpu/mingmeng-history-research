#!/usr/bin/env python3
"""NewspaperSG OCR 噪声清洗工具

针对 data/newspapersg/documents/*.txt 整页 OCR，去除：
- 单字符散行（< 3 字符的行）
- 高噪声率行（非中文/英文/标点/数字 占比 > 30%）
- 重复符号行（横线、点、星号等装饰）
- 颠倒排版字符块（连续中文 + 中间夹大量空格）

输出：
- data/newspapersg/documents_clean/*.txt（清洗后 OCR）
- data/newspapersg/ocr_clean_stats.csv（清洗前后字符数对比）

清洗策略保守——只去明显噪声，保留所有疑似有效中文段落。
"""
from __future__ import annotations
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "data" / "newspapersg" / "documents"
DST = ROOT / "data" / "newspapersg" / "documents_clean"
STATS = ROOT / "data" / "newspapersg" / "ocr_clean_stats.csv"


def clean_line(line: str) -> str | None:
    s = line.strip()
    if not s: return None
    # 1) 极短行（仅 1-2 字符且无中文）
    if len(s) <= 2 and not re.search(r"[一-鿿]", s):
        return None
    # 2) 纯符号 / 装饰行
    if re.fullmatch(r"[-—–_=*·.\s/\\|()\[\]<>]+", s):
        return None
    # 3) 高噪声率：非中文/英文/数字/常见标点 占比 > 30%
    if len(s) >= 3:
        clean_chars = re.findall(r"[一-鿿　-〿＀-￯a-zA-Z0-9，。；：、！？\"\"''（）()【】《》．,;:!?\"'.\s-]", s)
        if len(clean_chars) / len(s) < 0.7:
            return None
    # 4) "OCR 颠倒" 嫌疑：中文字符散在大量空格中（如 "和 圖" 形态）
    if len(s) <= 6:
        zh_count = len(re.findall(r"[一-鿿]", s))
        if zh_count >= 1 and zh_count <= 2 and len(s) - zh_count >= 4:
            return None
    return s


def clean_text(text: str) -> str:
    keep = [ln for ln in (clean_line(ln) for ln in text.split("\n")) if ln]
    return "\n".join(keep)


def main():
    DST.mkdir(parents=True, exist_ok=True)
    stats = []
    files = sorted(SRC.glob("*.txt"))
    print(f"清洗 {len(files)} 个 OCR 文件", file=sys.stderr)
    for p in files:
        raw = p.read_text(encoding="utf-8", errors="replace")
        cleaned = clean_text(raw)
        (DST / p.name).write_text(cleaned, encoding="utf-8")
        stats.append({
            "filename": p.name,
            "raw_chars": len(raw),
            "clean_chars": len(cleaned),
            "noise_pct": f"{(1 - len(cleaned)/max(len(raw),1))*100:.1f}",
        })
    with STATS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["filename","raw_chars","clean_chars","noise_pct"])
        w.writeheader()
        for s in stats: w.writerow(s)
    total_raw = sum(s["raw_chars"] for s in stats)
    total_clean = sum(s["clean_chars"] for s in stats)
    print(f"\n=== 完成 === 原始 {total_raw:,} 字符 → 清洗 {total_clean:,} 字符 "
          f"({(1-total_clean/total_raw)*100:.1f}% 噪声)", file=sys.stderr)
    print(f"输出: {DST}/ 与 {STATS}", file=sys.stderr)


if __name__ == "__main__":
    main()
