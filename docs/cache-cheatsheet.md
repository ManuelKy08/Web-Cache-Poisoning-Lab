# Web Cache Poisoning & Deception — cheat-sheet memo

## Bedanya poisoning vs deception
- **Poisoning**: attacker buat cache *menyimpan versi beracun* dari halaman publik →
  semua pengunjung kena.
- **Deception**: cache *menyimpan data privat* dari satu user (dengan padding path) →
  attacker replay path yang sama untuk baca datanya.

## Deteksi cepat poisoning (manual)
1. Minta halaman dengan header aneh: `X-Forwarded-Host: evil.com`, `X-Host`/`Host`, `X-Forwarded-Scheme`.
2. Lihat apakah header/param **tere-refleksi** ke body (script src, canonical, 302 Location).
3. Cek header respon `X-Cache: hit/miss`, `Age:`, `Set-Cookie` di cache. Jika `Age` naik = di-cache.
4. Tunggu: jika `refleksi` bisa masuk cache (cache key tak mencakup input itu) → poisoning sukses.

## Payload peek (bos)
```
GET /?ref=javascript:alert(document.cookie)//            # param unkeyed reflected
GET /  X-Forwarded-Host: evil.com                        # js host reflected => XSS
GET /welcome  Host: evil.com                             # 302 Location = evil
GET /profile/victim.css                                  # deception: private served + cached
```

## Checklist audit cache key
- [ ] Cache-key terdiri dari **apa saja**? cek `Vary`, `Cache-Control: pub,error?`, `Age`, `X-Cache` di tiap respon 200/302/404.
- [ ] Apakah input yang tidak ada di cache-key memengaruhi status/body/headers? (host, path/suffix, param, cookie)
- [ ] Respon auth (data pribadi, 302, error page) dapat di-cache? (harusnya `no-store`).
- [ ] Ada teknik padding path `.css`, `.js`, `;`, `..%2f`, `%0a` untuk menipu origin vs cache?
- [ ] Versi aplikasi berbeda interpretasi path (normalisasi, backslash, query-with->)? → "cache key confusion".

## Referensi
- James Kettle, "Practical Web Cache Poisoning" (2018) & "Web Cache Entanglement" — PortSwigger.
- HackerOne Shopify #1695604 (CDN cache poisoning DoS).