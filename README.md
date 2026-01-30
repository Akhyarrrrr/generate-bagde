# Design Badge KKN (Auto Generator)

Script Python untuk **membuat badge KKN secara otomatis** berdasarkan data CSV  
(foto, nama, dan NPM), menggunakan template PNG.

---

## 📁 Struktur Folder

Pastikan struktur folder seperti berikut:

Design badge KKN/
├─ fonts/
│  ├─ CooperHewitt.bold.otf
│  └─ CooperHewitt.book.otf
├─ out/                 # hasil badge (auto dibuat)
├─ data.csv             # data peserta
├─ template.png         # template badge
├─ generate-badge.py    # script utama
└─ README.md

---

## 📄 Format data.csv

File CSV **wajib** memiliki kolom berikut:

nama,npm,gambar  
Ahmad Fauzan,210123456,photos/ahmad.jpg  
Siti Aisyah,210123457,https://drive.google.com/file/d/XXXX/view  

Keterangan:
- **nama** → Nama peserta
- **npm** → NPM / NIM
- **gambar** → Path foto lokal atau URL (Google Drive / URL langsung)

---

## 🖼️ Template Badge

- Ukuran patokan template: **638 × 1004 px**
- Script akan **menyesuaikan otomatis** jika ukuran template berbeda
- Foto:
  - Tidak menutup frame
  - Sudut rounded
  - Posisi teks selalu rata tengah

---

## ⚙️ Instalasi Dependency

Disarankan menggunakan virtual environment.

pip install pillow pandas requests pillow-heif

Catatan:
- `pillow-heif` opsional, tetapi disarankan jika foto berasal dari iPhone (HEIC).

---

## ▶️ Cara Menjalankan

Jalankan perintah berikut di folder project:

python generate-badge.py

Hasil badge akan otomatis tersimpan di folder:

out/

Dengan format nama file:

NPM_NAMA.png

---

## 🔧 Pengaturan Tambahan (Opsional)

Beberapa parameter yang bisa disesuaikan di dalam script:

PHOTO_INSET  
Mengatur jarak foto dari frame badge

PHOTO_SHIFT_Y  
Menggeser posisi foto ke bawah / atas

BASE_NAME_FONT_SIZE  
Ukuran font nama

BASE_NPM_FONT_SIZE  
Ukuran font NPM

---

## ✅ Catatan

- Nama akan otomatis ditulis **huruf kapital**
- Placeholder teks di template akan dibersihkan otomatis
- Mendukung foto lokal maupun URL
- Aman untuk batch besar (puluhan hingga ratusan badge)

---

Selesai. Selamat mencetak badge KKN 🎓✨

