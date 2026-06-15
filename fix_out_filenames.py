import re
import os
import csv
from pathlib import Path

def normalize_name(name: str) -> str:
    name = (name or "").strip()
    name = name.replace("\u00A0", " ")
    name = re.sub(r"\s+", " ", name)
    name = name.replace(" ", "_")
    # hapus titik dan karakter aneh (sama seperti checker)
    name = re.sub(r"[^A-Za-z0-9_-]", "", name)
    name = re.sub(r"_+", "_", name).strip("_-")
    return name

def normalize_npm(npm: str) -> str:
    npm = str(npm or "").strip()
    npm = re.sub(r"\D", "", npm)
    return npm

def build_expected_map(data_csv: Path, npm_col="NPM", name_col="Nama"):
    expected = {}
    with data_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            npm_raw = row.get(npm_col, "")
            name_raw = row.get(name_col, "")
            npm = normalize_npm(npm_raw)
            name = normalize_name(name_raw)
            if not npm or not name:
                continue
            expected[npm] = f"{npm}_{name}.png"
    return expected

def main():
    data_csv = Path("data.csv")
    out_dir = Path("out")

    if not data_csv.exists():
        raise SystemExit("data.csv tidak ditemukan")
    if not out_dir.exists():
        raise SystemExit("folder out tidak ditemukan")

    expected_by_npm = build_expected_map(data_csv)

    renamed = 0
    skipped = 0
    conflict = 0

    for p in out_dir.glob("*.png"):
        old = p.name

        # ambil npm dari awal filename (sebelum underscore pertama)
        m = re.match(r"^(\d+)_", old)
        if not m:
            skipped += 1
            continue

        npm_in_file = m.group(1)

        # kalau npm di file hilang 0 depan, kita coba cocokkan juga:
        # cari expected berdasarkan npm persis dulu
        target = expected_by_npm.get(npm_in_file)

        # kalau gak ketemu, coba pad kiri dengan 0 sampai panjang 12 (umum NPM USK kadang 12)
        if target is None:
            # coba beberapa panjang masuk akal: 11-14
            found = None
            for L in [11, 12, 13, 14]:
                padded = npm_in_file.zfill(L)
                if padded in expected_by_npm:
                    found = expected_by_npm[padded]
                    break
            target = found

        if not target:
            skipped += 1
            continue

        new_path = out_dir / target

        # kalau sudah sama, skip
        if p.name == new_path.name:
            skipped += 1
            continue

        # kalau nama target sudah ada file lain, jangan tabrak
        if new_path.exists():
            conflict += 1
            continue

        p.rename(new_path)
        renamed += 1

    print("DONE")
    print(f"renamed  : {renamed}")
    print(f"skipped  : {skipped}")
    print(f"conflict : {conflict}")
    if conflict:
        print("Ada conflict: target filename sudah ada. Itu berarti ada duplikasi NPM atau file dobel.")

if __name__ == "__main__":
    main()
