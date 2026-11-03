"""Download + compress all listing photos from an import folder into a media tree.

    python media.py <import-folder> <media-root> <source-key> [--max-px 1280] [--quality 72] [--workers 8]

Result: <media-root>/<source-key>/<listing-slug>/01.webp, 02.webp, ...
and <media-root>/<source-key>/index.json  ({slug: ["01.webp", ...]}).
Resumable: already converted files are skipped. Needs Pillow + requests.
"""
import argparse
import io
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
local = threading.local()


def session():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.headers.update(HEADERS)
    return local.s


def convert(job, max_px, quality):
    out, urls, referer = job
    if out.exists() and out.stat().st_size > 1000:
        return "skip"
    last = None
    for u in urls:
        for _ in range(2):
            try:
                r = session().get(u, timeout=60, headers={"Referer": referer})
                r.raise_for_status()
                if "text/html" in r.headers.get("content-type", ""):
                    raise RuntimeError("html")
                im = Image.open(io.BytesIO(r.content))
                im = im.convert("RGB")
                im.thumbnail((max_px, max_px))
                buf = io.BytesIO()
                im.save(buf, "WEBP", quality=quality, method=4)
                out.parent.mkdir(parents=True, exist_ok=True)
                tmp = out.with_suffix(".tmp")
                tmp.write_bytes(buf.getvalue())
                tmp.replace(out)
                return "ok"
            except Exception as exc:
                last = exc
    return f"fail {urls[0]}: {last}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("import_dir")
    ap.add_argument("media_root")
    ap.add_argument("source")
    ap.add_argument("--max-px", type=int, default=1280)
    ap.add_argument("--quality", type=int, default=72)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    cat = json.loads((Path(a.import_dir) / "catalog.json").read_text(encoding="utf-8"))
    root = Path(a.media_root) / a.source
    jobs, index = [], {}
    for p in cat["properties"]:
        names = []
        for i, ph in enumerate(p.get("photos") or [], 1):
            name = f"{i:02d}.webp"
            names.append(name)
            jobs.append((root / p["slug"] / name, ph.get("urls") or [ph["url"]], p["url"]))
        index[p["slug"]] = names
    root.mkdir(parents=True, exist_ok=True)
    print(f"{len(cat['properties'])} listings, {len(jobs)} photos", flush=True)
    done = ok = fail = 0
    with ThreadPoolExecutor(a.workers) as pool, open(root / "failures.log", "a", encoding="utf-8") as flog:
        for res in pool.map(lambda j: convert(j, a.max_px, a.quality), jobs):
            done += 1
            if res.startswith("fail"):
                fail += 1
                flog.write(res + "\n")
            else:
                ok += 1
            if done % 500 == 0:
                print(f"{done}/{len(jobs)} ok={ok} fail={fail}", flush=True)
    # keep only files that exist
    index = {s: [n for n in names if (root / s / n).exists()] for s, names in index.items()}
    (root / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"done {done} ok={ok} fail={fail}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
