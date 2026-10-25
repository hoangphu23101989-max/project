"""Download legal open-access PDFs for the papers listed in danh_muc_bai_bao.csv.

Sources, in order: Unpaywall (best OA location), Europe PMC (OA full text by DOI or PMCID).
Paywalled papers are NOT downloaded; they are written to can_truy_cap_thu_vien.csv with a
https://doi.org/ link so they can be retrieved through the institutional library.

Usage:
    python tai_bai_bao.py --email you@example.com [--csv danh_muc_bai_bao.csv] [--out pdf] [--dry-run]
"""
import argparse
import csv
import re
import time
from pathlib import Path

import requests

UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"
EPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EPMC_PDF = "https://europepmc.org/articles/{pmcid}?pdf=render"
HEADERS = {"User-Agent": "uvvis-dao-ham/1.0 (academic literature retrieval)"}
PAUSE_S = 1.0


def safe_name(row):
    first = re.sub(r"[^A-Za-z]", "", row["tac_gia"].split(";")[0].split()[0])
    return f"{row['id']}_{first}{row['nam']}.pdf"


def unpaywall_pdf_urls(doi, email, session):
    r = session.get(UNPAYWALL.format(doi=doi), params={"email": email}, timeout=30)
    if r.status_code != 200:
        return []
    data = r.json()
    urls = []
    best = data.get("best_oa_location") or {}
    for loc in [best] + (data.get("oa_locations") or []):
        url = loc.get("url_for_pdf")
        if url and url not in urls:
            urls.append(url)
    return urls


def europepmc_pdf_urls(doi, pmcid, session):
    urls = []
    if pmcid:
        urls.append(EPMC_PDF.format(pmcid=pmcid))
    if doi:
        r = session.get(
            EPMC_SEARCH,
            params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"},
            timeout=30,
        )
        if r.status_code == 200:
            for res in r.json().get("resultList", {}).get("result", []):
                if res.get("pmcid") and EPMC_PDF.format(pmcid=res["pmcid"]) not in urls:
                    urls.append(EPMC_PDF.format(pmcid=res["pmcid"]))
                for ft in res.get("fullTextUrlList", {}).get("fullTextUrl", []):
                    if ft.get("documentStyle") == "pdf" and ft.get("availabilityCode") in ("OA", "F"):
                        if ft["url"] not in urls:
                            urls.append(ft["url"])
    return urls


def fetch_pdf(url, dest, session):
    r = session.get(url, timeout=60, allow_redirects=True)
    if r.status_code == 200 and r.content[:5] == b"%PDF-":
        dest.write_bytes(r.content)
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True, help="Email required by the Unpaywall API")
    ap.add_argument("--csv", default="danh_muc_bai_bao.csv")
    ap.add_argument("--out", default="pdf")
    ap.add_argument("--dry-run", action="store_true", help="Only list candidate URLs, do not download")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(args.csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    session = requests.Session()
    session.headers.update(HEADERS)
    log, library = [], []

    for row in rows:
        doi, pmcid = row["doi"].strip(), row["pmcid"].strip()
        dest = out / safe_name(row)
        if dest.exists():
            log.append([row["id"], doi, "da_co", "", str(dest)])
            continue
        if not doi and not pmcid:
            log.append([row["id"], doi, "khong_co_DOI", "", ""])
            library.append([row["id"], row["tieu_de"], row["tap_chi"], row["nam"], "", "Khong co DOI: tim theo tieu de"])
            continue

        candidates = []
        try:
            if doi:
                candidates += [("unpaywall", u) for u in unpaywall_pdf_urls(doi, args.email, session)]
                time.sleep(PAUSE_S)
            candidates += [("europepmc", u) for u in europepmc_pdf_urls(doi, pmcid, session)]
            time.sleep(PAUSE_S)
        except requests.RequestException as e:
            log.append([row["id"], doi, f"loi_mang: {e}", "", ""])
            continue

        if args.dry_run:
            log.append([row["id"], doi, "dry_run", " | ".join(u for _, u in candidates), ""])
            continue

        ok = False
        for source, url in candidates:
            try:
                if fetch_pdf(url, dest, session):
                    log.append([row["id"], doi, "tai_duoc", source, str(dest)])
                    ok = True
                    break
            except requests.RequestException:
                pass
            time.sleep(PAUSE_S)
        if not ok:
            log.append([row["id"], doi, "khong_co_ban_mo", "", ""])
            library.append([row["id"], row["tieu_de"], row["tap_chi"], row["nam"],
                            f"https://doi.org/{doi}" if doi else "", "Truy cap qua thu vien"])
        print(f"{row['id']}: {log[-1][2]}")

    with open("ket_qua_tai.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "doi", "trang_thai", "nguon", "duong_dan"])
        w.writerows(log)
    with open("can_truy_cap_thu_vien.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "tieu_de", "tap_chi", "nam", "link", "ghi_chu"])
        w.writerows(library)
    n_ok = sum(1 for r in log if r[2] in ("tai_duoc", "da_co"))
    print(f"\nTai duoc/da co: {n_ok}/{len(rows)}. Can truy cap thu vien: {len(library)}.")
    print("Ket qua: ket_qua_tai.csv, can_truy_cap_thu_vien.csv")


if __name__ == "__main__":
    main()
