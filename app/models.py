import os
import sqlite3
import threading
import time
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'lab.db')

FLAG = 'CACHE-LAB{Flag_Cache_Poisoning_Stored_Wildfire_5525}'

_db_lock = threading.Lock()

GOOD_HOST = 'shop.corp.test'

# `cache` simulasi CDN: url-path -> respon (dengan/ tanpa racun)
CACHE = {}


def reset_cache():
    CACHE.clear()
    CACHE['/'] = {'status': 200, 'html': '<h1>Home :)</h1><p>laman bersih</p>',
                  'headers': {'cache-control': 'public, max-age=3600'}, 'poison': None}
    CACHE.setdefault('/welcome', {'status': 302, 'location': 'https://shop.corp.test/dashboard',
                                  'headers': {'cache-control': 'public, max-age=600'}, 'poison': None})


@contextmanager
def conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with _db_lock, conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS settings(
          key TEXT PRIMARY KEY,
          vulnerable INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT,
          source TEXT,
          msg TEXT
        );
        ''')


def seed():
    init_db()
    with _db_lock, conn() as c:
        if os.environ.get('LAB_RESET') == '1':
            c.execute('DELETE FROM settings')
        for k in ('s1', 's2', 's3', 's4'):
            c.execute('INSERT OR IGNORE INTO settings(key,vulnerable) VALUES(?,1)', (k,))


def setting(key):
    with _db_lock, conn() as c:
        row = c.execute('SELECT vulnerable FROM settings WHERE key=?', (key,)).fetchone()
        return row['vulnerable'] == 1 if row else True


def set_setting(key, vuln):
    with _db_lock, conn() as c:
        cur = c.execute('UPDATE settings SET vulnerable=? WHERE key=?', (1 if vuln else 0, key))
        if cur.rowcount == 0:
            c.execute('INSERT OR REPLACE INTO settings(key,vulnerable) VALUES(?,?)', (key, 1 if vuln else 0))


def all_settings():
    with _db_lock, conn() as c:
        rows = c.execute('SELECT key, vulnerable FROM settings').fetchall()
        return {r['key']: bool(r['vulnerable']) for r in rows}


def log(source, msg):
    with _db_lock, conn() as c:
        c.execute('INSERT INTO logs(ts,source,msg) VALUES(?,?,?)',
                  (time.strftime('%Y-%m-%d %H:%M:%S'), source, msg))


def last_logs(n=80):
    with _db_lock, conn() as c:
        rows = c.execute('SELECT ts,source,msg FROM logs ORDER BY id DESC LIMIT ?', (n,)).fetchall()
        return [{'ts': r['ts'], 'source': r['source'], 'msg': r['msg']} for r in rows]