#!/usr/bin/env python3
"""List continuous-play flags, newest first. Usage: python3 bin/cheat_flags.py [days, default 7]"""
import sys
from pathlib import Path

import psycopg2
from dotenv import dotenv_values

url = dotenv_values(Path(__file__).resolve().parent.parent / '.env')['DATABASE_URL']
days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
with psycopg2.connect(url) as conn, conn.cursor() as cur:
    cur.execute('''SELECT u.username, f.kind, f.started_at, f.last_seen, f.detail, u.banned_until
                   FROM cheat_flags f JOIN users u ON u.id = f.user_id
                   WHERE f.last_seen > NOW() - make_interval(days => %s)
                   ORDER BY f.last_seen DESC''', (days,))
    rows = cur.fetchall()
if not rows:
    print(f'No flags in the last {days} days.')
for name, kind, started, seen, detail, banned in rows:
    ban = f'  [banned until {banned:%a %d %b %H:%M}]' if banned else ''
    print(f'{name:20} {kind:16} {started:%a %d %b %H:%M} -> {seen:%a %d %b %H:%M}  {detail}{ban}')
