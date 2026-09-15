<div align="center">
<a href="https://ibb.co/CpnVmMbg"><img src="https://i.ibb.co/SDKV5dtb/image.png" alt="image" border="0"></a>
</div>


# Web Cache Poisoning Lab

Lab Flask yang memodelkan **4 vektor web cache poisoning / deception** bikin sekali
di-populasi, semua pengunjung kena: **deception .css padding** (data privat bocor),
**poison 302 via unkeyed Host**, **unkeyed X-Forwarded-Host → stored XSS**, dan
**refleksi query param unkeyed → stored XSS**. Tiap skenario toggle **RENTAN / FIXED**,
bisa di-exercise manual lewat endpoint curl `/api/fetch`.

## 🧨 4 Skenario

| # | Vektor | Efek |
|---|--------|------|
| 1 | `.css` padding pada `/profile/victim.css` | Web Cache Deception → profil privat victim bocor |
| 2 | `X-Forwarded-Host: evil.com` pada `/welcome` | 302 beracun ter-cache → semua pengunjung dilempar ke evil |
| 3 | `X-Forwarded-Host` pada `/` | `<script src="//evil.com/...">` ter-cache → stored XSS massal |
| 4 | `/?ref=javascript:...` | Refleksi beracun ter-cache di `/` → XSS semua pengunjung |

Host sah: `shop.corp.test`. Flag: `CACHE-LAB{Flag_Cache_Poisoning_Stored_Wildfire_5525}`.

## 🚀 Menjalankan
### Docker (rekomendasi)
```bash
docker compose up -d --build      # buka http://127.0.0.1:5096
docker compose down               # stop
docker compose down -v            # stop + reset
```
### Lokal
```bash
pip install -r requirements.txt
python -m app.main
```

## 🧭 Cara main
- Dashboard → **Jalankan Exploit** → toggle **FIXED** → ulangi.
- Eksplorasi manual: `POST /api/fetch` (simulasi CDN+origin+store), `GET /api/cache`
  (inspeksi isi cache). Lihat `payloads/README.md`.
- Cheat-sheet audit (deteksi, payload, checklist cache-key): `docs/cache-cheatsheet.md`.

## Isi repo
```
app/          Flask: cache in-memory + origin (RENTAN/FIXED) + PoC
docs/         penjelasan + cache-cheatsheet.md
payloads/     set exploit curl
templates, static/   UI neon
```

## ⚠️ Warning
- Lab edukasi lokal/Docker saja — jangan di-deploy publik. Semua data & flag dummy.
