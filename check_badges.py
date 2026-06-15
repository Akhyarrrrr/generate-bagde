import os
import re
import csv
import argparse
from pathlib import Path


def normalize_name(name: str) -> str:
    """
    Ubah nama jadi aman untuk filename:
    - strip spasi
    - ganti spasi jadi underscore
    - hapus karakter aneh (selain a-zA-Z0-9 _ -)
    - rapikan underscore berlebih
    """
    if name is None:
        name = ""
    name = name.strip()

    # beberapa orang pakai gelar/titik/koma, kita rapikan
    name = name.replace("\u00A0", " ")  # non-breaking space -> space
    name = re.sub(r"\s+", " ", name)    # multiple spaces -> single

    name = name.replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9_-]", "", name)  # remove weird chars
    name = re.sub(r"_+", "_", name)             # collapse ___
    name = name.strip("_-")
    return name


def normalize_npm(npm: str) -> str:
    """
    Pastikan NPM hanya angka (kalau ada spasi/quote).
    """
    if npm is None:
        return ""
    npm = str(npm).strip()
    npm = re.sub(r"\D", "", npm)  # keep digits only
    return npm


def read_csv_expected(data_csv: Path, npm_col="NPM", name_col="Nama") -> dict:
    """
    Return dict expected_filename -> original_row (dict)
    """
    expected = {}

    with data_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if npm_col not in reader.fieldnames or name_col not in reader.fieldnames:
            raise ValueError(
                f"Kolom CSV tidak ketemu. Fieldnames: {reader.fieldnames}\n"
                f"Pastikan ada kolom '{npm_col}' dan '{name_col}'."
            )

        for i, row in enumerate(reader, start=2):  # start=2 karena header line 1
            npm = normalize_npm(row.get(npm_col, ""))
            name = normalize_name(row.get(name_col, ""))

            if not npm or not name:
                # skip baris yang tidak valid tapi tetap bisa dilaporkan kalau mau
                continue

            filename = f"{npm}_{name}.png"

            # jika ada duplikasi NPM+Nama, simpan yang pertama dan catat
            if filename not in expected:
                expected[filename] = row

    return expected


def list_out_files(out_dir: Path) -> set:
    files = set()
    for p in out_dir.glob("*.png"):
        files.add(p.name)
    return files


def main():
    ap = argparse.ArgumentParser(description="Cek kesesuaian data.csv vs hasil badge di folder out/")
    ap.add_argument("--csv", default="data.csv", help="Path ke data.csv")
    ap.add_argument("--out", default="out", help="Folder output badge (default: out)")
    ap.add_argument("--npm-col", default="NPM", help="Nama kolom NPM di CSV (default: NPM)")
    ap.add_argument("--name-col", default="Nama", help="Nama kolom Nama di CSV (default: Nama)")
    ap.add_argument("--export", default="", help="Opsional: export expected list ke CSV (misal expected_list.csv)")
    args = ap.parse_args()

    data_csv = Path(args.csv)
    out_dir = Path(args.out)

    if not data_csv.exists():
        raise SystemExit(f"❌ File CSV tidak ditemukan: {data_csv.resolve()}")
    if not out_dir.exists():
        raise SystemExit(f"❌ Folder out tidak ditemukan: {out_dir.resolve()}")

    expected = read_csv_expected(data_csv, npm_col=args.npm_col, name_col=args.name_col)
    out_files = list_out_files(out_dir)

    expected_files = set(expected.keys())

    missing = sorted(expected_files - out_files)
    extra = sorted(out_files - expected_files)
    present = sorted(expected_files & out_files)

    print("============================================================")
    print(f"CSV           : {data_csv.resolve()}")
    print(f"OUT folder    : {out_dir.resolve()}")
    print(f"Total data CSV (valid NPM+Nama) : {len(expected_files)}")
    print(f"✅ Sudah ada badge             : {len(present)}")
    print(f"❌ Belum ada badge (missing)   : {len(missing)}")
    print(f"⚠️  File nyasar (extra)        : {len(extra)}")
    print("============================================================")

    if missing:
        print("\n--- MISSING (harusnya ada tapi tidak ditemukan di out/) ---")
        for fn in missing:
            row = expected.get(fn, {})
            npm = normalize_npm(row.get(args.npm_col, "")) if row else ""
            nama = row.get(args.name_col, "") if row else ""
            print(f"- {fn}  | NPM={npm} | Nama={nama}")

    if extra:
        print("\n--- EXTRA (ada di out/ tapi tidak ada di data.csv) ---")
        for fn in extra:
            print(f"- {fn}")

    if args.export:
        export_path = Path(args.export)
        with export_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["expected_filename", "npm", "nama_raw"])
            for fn, row in expected.items():
                w.writerow([fn, normalize_npm(row.get(args.npm_col, "")), row.get(args.name_col, "")])
        print(f"\n📄 Export expected list: {export_path.resolve()}")


if __name__ == "__main__":
    main()
