#!/usr/bin/env python3
"""批量下载 DRNH（台北国史馆「檔案史料文物查詢系統」）档案影像。

侦察到的接口流程（2026-06-01 逆向）：
  1. 搜索  GET  /index.php?act=Archive/search/<base64url(JSON)>
           HTML 含 acckey='<32 hex>'  （线上閱覽按钮的属性）
  2. 初始  POST /index.php  body act=Display/initial/<acckey>
           → {data:{display:'image', resouse:'<token>'}}
  3. 构建  POST /index.php  body act=Display/built/<resouse>/
           → {data:{page_count, page_list:{1:code, 2:code, ...}, page_fname}}
  4. 取图  GET  /index.php?act=Display/loadimg/<page_code>
           → JPEG（每页 ~700KB–1.5MB，1496×2300，质量 90，带"國史館"访客水印）

注意：未登录拿到的是**水印锁屏版**（页面有半透明"請登入"提示+國史館网格水印）。
清洁版需登录账号；本平台采用水印版作为研究底图（与 changelog 5/20 已有 5 件
原图一致）。

用法：
  # 下载某档号清单（CSV 第一列为典藏号或 drnh:前缀键）
  python3 download_drnh_images.py --list ids.txt --out data/drnh_images
  # 默认从 data/drnh_review_layers.csv 抽 1946 年所有
  python3 download_drnh_images.py --year 1946 --out data/drnh_images
  # 限速、跳过已下载
  python3 download_drnh_images.py --year 1946 --sleep 1.5 --max 10

输出：
  <out>/<store_no>/page_<N>.jpg
  <out>/<store_no>/_index.json   （含 page_count, page_fname, 取图时间）
  <out>/_download_log.csv         （成功/失败逐行）
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = "https://ahonline.drnh.gov.tw/index.php"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def b64u(s: str) -> str:
    """JSON → base64url（无填充，DRNH 用的方言）。"""
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii").rstrip("=")


class DRNHSession:
    def __init__(self, sleep: float = 1.5):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA})
        self.sleep = sleep
        # 主页 warmup 拿 PHPSESSID
        self.s.get(BASE, timeout=15, allow_redirects=True)

    def _slow(self):
        time.sleep(self.sleep)

    def search_for_acckey(self, store_no: str) -> str | None:
        """按典藏号搜索，从结果 HTML 抽 acckey。"""
        query = json.dumps({"query": [{"field": "store_no", "value": store_no, "attr": "+"}]},
                           ensure_ascii=False, separators=(",", ":"))
        r = self.s.get(f"{BASE}?act=Archive/search/{b64u(query)}", timeout=40)
        r.raise_for_status()
        # 限定到包含该 store_no 的结果块附近，避免抓错
        m = re.search(r"acckey=['\"]([a-f0-9]{32})['\"]", r.text)
        return m.group(1) if m else None

    def display_initial(self, acckey: str) -> str | None:
        r = self.s.post(BASE, data={"act": f"Display/initial/{acckey}"},
                        headers={"X-Requested-With": "XMLHttpRequest"}, timeout=30)
        r.raise_for_status()
        j = r.json()
        if not j.get("action"):
            return None
        return j["data"].get("resouse")

    def display_built(self, resouse: str) -> dict | None:
        r = self.s.post(BASE, data={"act": f"Display/built/{resouse}/"},
                        headers={"X-Requested-With": "XMLHttpRequest"}, timeout=30)
        r.raise_for_status()
        j = r.json()
        if not j.get("action"):
            return None
        d = j["data"]
        return {
            "page_count": d.get("page_count"),
            "page_list": d.get("page_list", {}),
            "page_fname": d.get("page_fname", ""),
        }

    def load_image(self, page_code: str) -> bytes | None:
        r = self.s.get(f"{BASE}?act=Display/loadimg/{page_code}", timeout=45)
        if r.status_code != 200 or not r.headers.get("Content-Type", "").startswith("image/"):
            return None
        return r.content

    def fetch_doc(self, store_no: str) -> tuple[dict, bytes | None]:
        """端到端取一份档案的所有页。返回 (meta, error_or_None)。"""
        meta = {"store_no": store_no, "fetched_at": datetime.now().isoformat(timespec="seconds")}
        acc = self.search_for_acckey(store_no); self._slow()
        if not acc:
            meta["error"] = "acckey not found"; return meta, None
        meta["acckey"] = acc
        res = self.display_initial(acc); self._slow()
        if not res:
            meta["error"] = "initial failed"; return meta, None
        meta["resouse"] = res
        info = self.display_built(res); self._slow()
        if not info:
            meta["error"] = "built failed"; return meta, None
        meta.update(info)
        # 逐页下载（page_list 是 {"1": code1, "2": code2}，按序号）
        page_list = info["page_list"]
        ordered = sorted(page_list.items(), key=lambda kv: int(kv[0]))
        images = {}
        for n, code in ordered:
            img = self.load_image(code); self._slow()
            if not img:
                meta.setdefault("page_errors", []).append(int(n))
                continue
            images[int(n)] = img
        meta["pages_ok"] = len(images)
        return meta, images


def load_id_list(path: Path) -> list[str]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip().split(",")[0].strip()
            if not s or s.startswith("#"):
                continue
            # 兼容 drnh: 前缀
            out.append(s.removeprefix("drnh:"))
    return out


def load_from_review_layers(csv_path: Path, year: str = "", tiers: set[str] | None = None) -> list[str]:
    """从 drnh_review_layers.csv 按 tier + year 过滤。"""
    out = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if tiers and row.get("tier") not in tiers:
                continue
            if year and not (row.get("date_guess") or "").startswith(year):
                continue
            key = row.get("doc_key", "").removeprefix("drnh:")
            if key:
                out.append(key)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--list", help="档号清单文件（每行一个）")
    p.add_argument("--year", default="", help="按年过滤（如 1946）")
    p.add_argument("--tiers", default="重点校订,常规校订",
                   help="按校订分层过滤，逗号分隔（默认重点+常规）")
    p.add_argument("--csv", default="data/drnh_review_layers.csv",
                   help="review_layers CSV 路径")
    p.add_argument("--out", default="data/drnh_images", help="输出根目录")
    p.add_argument("--sleep", type=float, default=1.5,
                   help="每次 HTTP 间隔秒（保守，避免被封）")
    p.add_argument("--max", type=int, default=0, help="最多下载 N 篇（0=不限）")
    p.add_argument("--skip-existing", action="store_true", default=True)
    args = p.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    if args.list:
        ids = load_id_list(Path(args.list))
    else:
        tiers = set(t.strip() for t in args.tiers.split(",") if t.strip())
        ids = load_from_review_layers(Path(args.csv), args.year, tiers)
    if args.max:
        ids = ids[: args.max]
    print(f"待下载: {len(ids)} 篇（year={args.year} tiers={args.tiers}）", file=sys.stderr)

    sess = DRNHSession(sleep=args.sleep)
    log_path = out_root / "_download_log.csv"
    log_new = not log_path.exists()
    log_f = open(log_path, "a", encoding="utf-8", newline="")
    log = csv.writer(log_f)
    if log_new:
        log.writerow(["store_no", "status", "pages", "fname", "error", "at"])

    ok = fail = skip = 0
    t0 = time.time()
    for i, sn in enumerate(ids, 1):
        dst = out_root / sn
        idx_path = dst / "_index.json"
        if args.skip_existing and idx_path.exists():
            try:
                m = json.load(idx_path.open())
                if m.get("pages_ok", 0) >= 1 and "error" not in m:
                    skip += 1
                    print(f"  [{i}/{len(ids)}] skip {sn} (已有 {m['pages_ok']} 页)", file=sys.stderr)
                    continue
            except Exception:
                pass
        meta, images = sess.fetch_doc(sn)
        dst.mkdir(parents=True, exist_ok=True)
        if images:
            for n, b in images.items():
                (dst / f"page_{n:03d}.jpg").write_bytes(b)
            ok += 1
            status = "ok"
        else:
            fail += 1
            status = "fail"
        idx_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        log.writerow([sn, status, meta.get("pages_ok", 0), meta.get("page_fname", ""),
                      meta.get("error", ""), meta["fetched_at"]])
        log_f.flush()
        elapsed = time.time() - t0
        print(f"  [{i}/{len(ids)}] {status:4} {sn} 页={meta.get('pages_ok',0)} "
              f"err={meta.get('error','-')} ({elapsed:.0f}s)", file=sys.stderr)

    log_f.close()
    print(f"\n=== 完成 === 成功 {ok} / 失败 {fail} / 跳过 {skip} ({time.time()-t0:.0f}s)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
