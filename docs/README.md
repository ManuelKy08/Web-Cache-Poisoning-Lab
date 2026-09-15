# Web Cache Poisoning Lab — penjelasan & real case

Lab Flask yang memodelkan **web cache poisoning & web cache deception**:
cache CDN menyimpan respon dengan kunci **path-only**, sedangkan origin merender konten
dari input di luar kunci (header Host/X-Forwarded-Host, query param, padding path).
Attacker meng-populasi cache → semua pengunjung laman kena.

- Port: `http://127.0.0.1:5096`
- CDN = cache in-memory (`/api/cache` untuk inspeksi); host sah `shop.corp.test`.
- Flag: `CACHE-LAB{Flag_Cache_Poisoning_Stored_Wildfire_5525}`

## 4 Skenario (mapping real class)
1. **Web Cache Deception** (`.css` padding) — profil privat dengan `Cache-Control: public`
   tersimpan saat victim request `/profile/victim.css`; attacker replay tanpa login → data bocor.
2. **Poisoning 302** (unkeyed Host) — origin build redirect dari `Host`/`X-Forwarded-Host`;
   respon 302 beracun di-cache → semua pengunjung dilempar ke host penyerang (SEO-jack).
3. **Unkeyed `X-Forwarded-Host` → stored XSS** — origin render `<script src="//HOST/...">` dari
   header; siram sekali → semua user load skrip attacker.
4. **Unkeyed query param** — origin merefleksikan `?ref=` ke HTML; param tidak masuk cache-key
   → sekali racun, semua pengunjung dapat XSS.

## Mengapa RENTAN
- Cache-key hanya = **path** (`suspicious request` dipaksa ke origin, respon disimpan apa adanya).
- Origin percaya header Host/X-Forwarded-Host tanpa validasi (`host` apapun diterima).
- Tidak ada whitelist query param pada cacheable endpoints; setup Vary/Key tidak dipakai.

## Fix (FIXED mode)
- Profil privat & data pribadi → `Cache-Control: no-store`, dan padding path ditolak.
- Host/Forwarded-Host divalidasi ke daftar host sah → selain itu 400 (tidak tersimpan).
- Query param di-whitelist (`page`); param lain → 400, tidak direfleksikan ke HTML.
- (Di produksi: pertimbangkan CDN `cache-key` yg mencakup `Vary: Host`, header param penting.)

## Cara jalankan
```
python -m app.main         # dari folder lab — port 5096
```
### Docker
```bash
docker compose up -d --build
```
Payload & cheat-sheet: `payloads/README.md`, `docs/cache-cheatsheet.md`.