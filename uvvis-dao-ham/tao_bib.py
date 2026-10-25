"""Regenerate references.bib from danh_muc_bai_bao.csv with BibTeX-correct author names.

Usage: python tao_bib.py [--csv danh_muc_bai_bao.csv] [--out references.bib]
"""
import argparse
import csv
import re


def format_author(raw):
    """'Sanchez Rojas F' -> 'Sanchez Rojas, F.'; 'Mot AC' -> 'Mot, A. C.'."""
    raw = raw.strip()
    if not raw or raw.lower().startswith("et al"):
        return None
    parts = raw.split()
    if len(parts) > 1 and re.fullmatch(r"[A-Z]{1,3}", parts[-1]):
        family = " ".join(parts[:-1])
        given = " ".join(f"{c}." for c in parts[-1])
        return f"{family}, {given}"
    return raw


def authors_field(raw):
    names = []
    for chunk in raw.split(";"):
        chunk = chunk.replace("et al.", "").strip()
        name = format_author(chunk)
        if name:
            names.append(name)
    if "et al" in raw:
        names.append("others")
    return " and ".join(names)


def bib_key(row):
    first = row["tac_gia"].split(";")[0].split()[0]
    first = re.sub(r"[^A-Za-z]", "", first)
    return f"{row['id']}_{first}{row['nam']}"


def to_entry(row):
    is_book = "sach" in row["tap_chi"].lower()
    vol, _, pages = row["tap_trang"].partition(":")
    fields = [("author", authors_field(row["tac_gia"])), ("title", row["tieu_de"])]
    if is_book:
        fields.append(("publisher", row["tap_chi"].replace("(sach)", "").strip()))
    else:
        fields.append(("journal", row["tap_chi"]))
    fields.append(("year", row["nam"]))
    if vol:
        fields.append(("volume", vol))
    if pages:
        fields.append(("pages", pages.replace("-", "--")))
    if row["doi"]:
        fields.append(("doi", row["doi"]))
    note = []
    if row["pmid"]:
        note.append(f"PMID: {row['pmid']}")
    if row["pmcid"]:
        note.append(f"PMCID: {row['pmcid']}")
    if row["ghi_chu"]:
        note.append(row["ghi_chu"])
    if note:
        fields.append(("note", "; ".join(note)))
    fields.append(("keywords", row["nhom"]))
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
    return f"@{'book' if is_book else 'article'}{{{bib_key(row)},\n{body}\n}}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="danh_muc_bai_bao.csv")
    ap.add_argument("--out", default="references.bib")
    args = ap.parse_args()
    with open(args.csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(to_entry(r) for r in rows))
    print(f"{len(rows)} entries -> {args.out}")


if __name__ == "__main__":
    main()
