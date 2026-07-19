#!/usr/bin/env python3
import sqlite3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
IMG_DIR = ROOT / "data" / "drnh_images"

def ingest_images():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 确保 images 表存在
    cur.execute("""
        CREATE TABLE IF NOT EXISTS drnh_images (
            document_id INTEGER,
            page_num INTEGER,
            file_path TEXT,
            PRIMARY KEY(document_id, page_num)
        )
    """)
    
    count = 0
    # 遍历目录
    for doc_dir in IMG_DIR.iterdir():
        if not doc_dir.is_dir():
            continue
            
        # 兼容旧目录名 drnh__典藏号 和下载器当前生成的直接典藏号目录。
        dir_name = doc_dir.name
        if dir_name.startswith("drnh__"):
            store_no = dir_name.removeprefix("drnh__")
        elif re.fullmatch(r"\d{3}-\d{6}-\d{5}-\d{3}", dir_name):
            store_no = dir_name
        else:
            continue
        
        # 查找对应的 document_id
        doc = cur.execute("SELECT id FROM documents WHERE doc_id = ?", (store_no,)).fetchone()
        if not doc:
            print(f"警告: 未找到典藏号 {store_no} 的文档，跳过图片")
            continue
            
        doc_id = doc[0]
        
        # 兼容旧命名 p1.jpg 和下载器当前命名 page_001.jpg。
        image_files = sorted(set(doc_dir.glob("p*.jpg")) | set(doc_dir.glob("page_*.jpg")))
        for img_file in image_files:
            try:
                match = re.fullmatch(r"p(\d+)|page_(\d+)", img_file.stem)
                if not match:
                    continue
                page_num = int(match.group(1) or match.group(2))
                cur.execute(
                    "INSERT OR REPLACE INTO drnh_images(document_id, page_num, file_path) VALUES (?, ?, ?)",
                    (doc_id, page_num, str(img_file.relative_to(ROOT)))
                )
                count += 1
            except ValueError:
                continue
                
    conn.commit()
    conn.close()
    print(f"完成，共关联 {count} 张图片")

if __name__ == "__main__":
    ingest_images()
