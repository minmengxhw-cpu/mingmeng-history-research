#!/usr/bin/env python3
import sqlite3
import json
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
            
        # 目录名格式为 drnh__典藏号 (例如 drnh__001-011142-00069-012)
        # 我们需要从这个名字中提取出中间的典藏号
        dir_name = doc_dir.name
        if not dir_name.startswith("drnh__"):
            continue
        store_no = dir_name.replace("drnh__", "")
        
        # 查找对应的 document_id
        doc = cur.execute("SELECT id FROM documents WHERE doc_id = ?", (store_no,)).fetchone()
        if not doc:
            print(f"警告: 未找到典藏号 {store_no} 的文档，跳过图片")
            continue
            
        doc_id = doc[0]
        
        # 遍历图片文件 (p1.jpg, p2.jpg...)
        for img_file in doc_dir.glob("p*.jpg"):
            try:
                page_num = int(img_file.stem[1:]) # 获取数字部分
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
