import os
import re
import io
import pandas as pd
import requests
from PIL import Image, ImageDraw, ImageFont

# HEIC/HEIF support
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_ENABLED = True
except Exception:
    HEIF_ENABLED = False


# =========================
# CONFIG: FILES
# =========================
TEMPLATE_PATH = "template.png"
CSV_PATH = "data.csv"
OUT_DIR = "out"

# =========================
# CONFIG: BASE TEMPLATE (patokan 638x1004)
# auto-scale jika template beda ukuran
# =========================
BASE_W, BASE_H = 638, 1004

# Area DALAM frame foto (base coords)
BASE_PHOTO_BOX = (182, 284, 455, 653)

# Posisi teks (base)
BASE_NAME_Y = 677
BASE_NPM_Y = 745

# ✅ FIX UTAMA: kotak clear placeholder yang AMAN (tidak nyentuh frame)
# (dibuat lebih "turun" dibanding versi sebelumnya)
BASE_CLEAR_NAME_BOX = (70, 662, 568, 718)
BASE_CLEAR_NPM_BOX = (170, 722, 468, 770)

# Rounded corner foto (base)
BASE_PHOTO_RADIUS = 32

# =========================
# CONFIG: FOTO (biar pas & tidak nutup border)
# =========================
PHOTO_INSET = 10  # menjauh dari border frame (8-14 aman)
PHOTO_SHIFT_Y = 3  # ✅ turun sedikit biar "pas kiri-kanan" (0-12)

# =========================
# CONFIG: FONT (Cooper Hewitt OTF)
# =========================
FONT_NAME_PATH = "fonts/CooperHewitt.bold.otf"
FONT_NPM_PATH = "fonts/CooperHewitt.book.otf"

BASE_NAME_FONT_SIZE = 44
BASE_NPM_FONT_SIZE = 22

TEXT_COLOR = (20, 45, 90)

# =========================
# HTTP (untuk gambar URL)
# =========================
HTTP_TIMEOUT = 25
UA_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}


# =========================
# HELPERS
# =========================
def safe_filename(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[^\w\-\. ]+", "", s)
    s = s.replace(" ", "_")
    return s[:150] if len(s) > 150 else s


def scale_box(box, sx, sy):
    x1, y1, x2, y2 = box
    return (int(x1 * sx), int(y1 * sy), int(x2 * sx), int(y2 * sy))


def cover_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Crop & resize gaya cover agar memenuhi box tanpa distorsi."""
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        new_w = int(src_h * tgt_ratio)
        x1 = (src_w - new_w) // 2
        img = img.crop((x1, 0, x1 + new_w, src_h))
    else:
        new_h = int(src_w / tgt_ratio)
        y1 = (src_h - new_h) // 2
        img = img.crop((0, y1, src_w, y1 + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def draw_center_text(
    draw: ImageDraw.ImageDraw, text: str, y: int, font, color, canvas_w: int
):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (canvas_w - text_w) // 2
    draw.text((x, y), text, font=font, fill=color)


def rounded_mask(size, radius):
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    return m


def normalize_drive_url(url: str) -> str:
    """
    Convert Google Drive share link -> direct download.
    """
    u = url.strip()
    if "drive.google.com/file/d/" in u:
        file_id = u.split("/file/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    if "drive.google.com/open?id=" in u:
        file_id = u.split("open?id=")[1].split("&")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return u


def load_image_from_url(url: str) -> Image.Image:
    url = normalize_drive_url(url)
    r = requests.get(
        url, headers=UA_HEADERS, timeout=HTTP_TIMEOUT, allow_redirects=True
    )
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def load_image(photo_value: str) -> Image.Image:
    v = str(photo_value).strip()
    if v.lower().startswith("http://") or v.lower().startswith("https://"):
        return load_image_from_url(v)
    return Image.open(v).convert("RGBA")


def fill_rect_with_local_bg(canvas: Image.Image, draw: ImageDraw.ImageDraw, rect):
    """
    Isi rect dengan warna background lokal (sample kecil dari area itu),
    supaya hapus placeholder tidak bikin 'kotak putih' beda warna.
    """
    x1, y1, x2, y2 = rect
    x_s = min(canvas.size[0] - 1, max(0, x1 + 3))
    y_s = min(canvas.size[1] - 1, max(0, y1 + 3))
    bg = canvas.convert("RGB").getpixel((x_s, y_s))
    draw.rectangle(rect, fill=(*bg, 255))


# =========================
# MAIN
# =========================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    if not os.path.exists(FONT_NAME_PATH):
        raise FileNotFoundError(f"Font not found: {FONT_NAME_PATH}")

    if not os.path.exists(FONT_NPM_PATH):
        raise FileNotFoundError(f"Font not found: {FONT_NPM_PATH}")

    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    W, H = template.size

    print(f"[INFO] Template: {W}x{H}")
    print(
        f"[INFO] HEIC/HEIF enabled: {HEIF_ENABLED} (pip install pillow-heif kalau False)"
    )

    sx = W / BASE_W
    sy = H / BASE_H
    smin = min(sx, sy)

    PHOTO_BOX = scale_box(BASE_PHOTO_BOX, sx, sy)
    CLEAR_NAME_BOX = scale_box(BASE_CLEAR_NAME_BOX, sx, sy)
    CLEAR_NPM_BOX = scale_box(BASE_CLEAR_NPM_BOX, sx, sy)

    NAME_Y = int(BASE_NAME_Y * sy)
    NPM_Y = int(BASE_NPM_Y * sy)

    name_font = ImageFont.truetype(
        FONT_NAME_PATH, max(10, int(BASE_NAME_FONT_SIZE * sy))
    )
    npm_font = ImageFont.truetype(FONT_NPM_PATH, max(10, int(BASE_NPM_FONT_SIZE * sy)))

    x1, y1, x2, y2 = PHOTO_BOX
    box_w = x2 - x1
    box_h = y2 - y1

    inset = max(0, int(PHOTO_INSET * smin))
    shift_y = int(PHOTO_SHIFT_Y * smin)

    # posisi foto (turun sedikit dengan shift_y)
    ix1 = x1 + inset
    iy1 = y1 + inset + shift_y
    iw = box_w - 2 * inset
    ih = box_h - 2 * inset

    if iw <= 10 or ih <= 10:
        raise ValueError("PHOTO_INSET terlalu besar, kecilkan nilainya.")

    radius = max(1, int(BASE_PHOTO_RADIUS * smin))
    radius2 = max(1, radius - int(inset * 0.7))
    mask = rounded_mask((iw, ih), radius2)

    df = pd.read_csv(CSV_PATH)
    for col in ["nama", "npm", "gambar"]:
        if col not in df.columns:
            raise ValueError(
                f"CSV must contain columns: nama,npm,gambar. Found: {list(df.columns)}"
            )

    for idx, row in df.iterrows():
        nama = str(row["nama"]).strip()
        npm = str(row["npm"]).strip()
        gambar = str(row["gambar"]).strip()

        if not nama or not npm:
            print(f"[SKIP] Row {idx+1}: empty nama/npm")
            continue

        canvas = template.copy()
        draw = ImageDraw.Draw(canvas)

        # 1) tempel foto dulu
        try:
            img = load_image(gambar)
            img = cover_resize(img, iw, ih)
            canvas.paste(img, (ix1, iy1), mask)
        except Exception as e:
            print(f"[WARN] Foto gagal ({npm} - {nama}) -> {gambar}\n  {e}")

        # 2) ✅ FIX: clear placeholder pakai box tetap (bukan berdasarkan panjang nama)
        fill_rect_with_local_bg(canvas, draw, CLEAR_NAME_BOX)
        fill_rect_with_local_bg(canvas, draw, CLEAR_NPM_BOX)

        # 3) tulis teks (nama dibuat uppercase biar konsisten gaya badge)
        draw = ImageDraw.Draw(canvas)
        draw_center_text(draw, nama.upper(), NAME_Y, name_font, TEXT_COLOR, W)
        draw_center_text(draw, npm, NPM_Y, npm_font, TEXT_COLOR, W)

        out_file = safe_filename(f"{npm}_{nama}.png")
        out_path = os.path.join(OUT_DIR, out_file)
        canvas.save(out_path)
        print(f"[OK] {out_path}")

    print("[DONE] All badges generated.")


if __name__ == "__main__":
    main()
