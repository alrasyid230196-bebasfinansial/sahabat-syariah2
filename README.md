# Sahabat Syariah — Online-ready

Website Flask yang dapat diakses dari HP setelah dideploy ke hosting. Pengguna cukup memasukkan kode emiten seperti BBCA, BBRI, BMRI, TLKM, ANTM, atau BRIS.

## Isi
- Harga dan perubahan harga
- PER, PBV, EPS, BVPS
- ROE, ROA, Net Profit Margin
- Dividend Yield
- Pendapatan, laba, aset, ekuitas, utang
- Pertumbuhan pendapatan dan laba tahunan jika data tersedia
- Arus kas operasi dan Free Cash Flow jika data tersedia
- Grafik harga 1 tahun
- Catatan screening syariah dan tautan DES OJK
- Tampilan responsif untuk HP Android/Vivo

## Deploy cepat ke Render
Render mendukung Flask. Gunakan:
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Health Check: `/health`

Langkah:
1. Buat repository GitHub baru, misalnya `sahabat-syariah`.
2. Upload semua file/folder dalam paket ini.
3. Di Render pilih New > Web Service dan hubungkan repository.
4. Pilih Python 3 dan Free untuk uji coba.
5. Deploy. Setelah selesai Render memberi URL `onrender.com` yang bisa dibuka dari HP Vivo.

## Catatan data
- Data pasar berasal dari Yahoo Finance melalui yfinance dan dapat tertunda/tidak lengkap.
- Data ini bukan feed resmi BEI dan bukan jaminan real-time.
- Status syariah tidak diputuskan oleh rasio proxy aplikasi. Status resmi harus dicek pada DES OJK terbaru.
- Aplikasi tidak memberikan rekomendasi beli/jual.

## Pengembangan berikutnya
Untuk penggunaan serius, ganti sumber data dengan penyedia data pasar resmi/berlisensi dan buat sinkronisasi DES OJK otomatis.
