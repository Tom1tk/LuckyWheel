#!/usr/bin/env python3
"""RV-10: snapshot the state before a tide rollover, then verify it afterwards.

    post_rollover_check.py snapshot --db NAME --out FILE.json
    post_rollover_check.py verify --db NAME --before FILE.json [--live-url URL]

verify prints one PASS/FAIL line per check and exits 1 if any check fails.
A wrong connected database exits 3 (see advance_tide.connect_checked).
"""
import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from advance_tide import connect_checked  # also puts the repo root on sys.path
import models
import seasons
from season_config import SEASON_CONFIG

THEME = SEASON_CONFIG['theme_item']
COSMETICS = {k for k, v in models.ITEM_CURRENCY.items() if v == 'losses'}
KNOWN_IDS = (set(models.SHOP_ITEMS) | set(models.RETIRED_ITEMS)
             | set(models.RETIRED_S9_ITEMS) | set(models.FISH_SKINS))
COSMETIC_SAMPLE = 50
REAL_PLAYERS_SQL = ("SELECT count(*) FROM game_state gs JOIN users u ON u.id = gs.user_id "
                    "WHERE u.ip_address <> '127.0.0.1' AND gs.wins > 0")


def read_state(conn):
    """Everything the post-rollover checks compare against."""
    with conn.cursor() as cur:
        cur.execute('SELECT season_number, player_facing_number, sub_number FROM seasons ORDER BY id LIMIT 1')
        season_number, pfn, sub = cur.fetchone()
        cur.execute('SELECT count(*) FROM users')
        users = cur.fetchone()[0]
        cur.execute('SELECT user_id, owned_items FROM game_state ORDER BY user_id LIMIT %s', (COSMETIC_SAMPLE,))
        cosmetics = [[uid, sorted(set(owned or []) & COSMETICS)] for uid, owned in cur.fetchall()]
        cur.execute('SELECT user_id, caught_species FROM game_state ORDER BY user_id')
        species = hashlib.md5(json.dumps(cur.fetchall(), default=str).encode()).hexdigest()
        cur.execute(REAL_PLAYERS_SQL)
        real_players = cur.fetchone()[0]
    return {
        'season_number': season_number,
        'pfn': pfn,
        'sub': sub,
        'label': seasons.season_label(pfn, sub, season_number),
        'users': users,
        'cosmetics': cosmetics,
        'species_md5': species,
        'real_players': real_players,
    }


def _next_label(before):
    if before['sub'] is None:
        return None
    return seasons.season_label(before['pfn'], before['sub'] + 1, before['season_number'])


def _missing_grant(cur, item):
    cur.execute('SELECT count(*) FROM game_state WHERE NOT (%s = ANY(COALESCE(owned_items, ARRAY[]::text[])))',
                (item,))
    return cur.fetchone()[0]


def _live_check(name, url):
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return name, resp.status == 200, f'HTTP {resp.status}'
    except (urllib.error.URLError, OSError) as exc:
        return name, False, f'{url}: {exc}'


def run_checks(conn, before, live_url=''):
    """Return a list of (name, ok, detail) for every post-rollover check."""
    after = read_state(conn)
    results = []
    expected = _next_label(before)
    results.append(('label_advanced', after['label'] == expected,
                    f"now {after['label']}, expected {expected}"))
    with conn.cursor() as cur:
        cur.execute('SELECT label FROM season_log WHERE season_number = %s', (before['season_number'],))
        logged = [row[0] for row in cur.fetchall()]
        results.append(('season_log_row', logged == [before['label']],
                        f"logged {logged}, expected [{before['label']!r}]"))

        cur.execute('SELECT count(*) FROM game_state WHERE wins <> 0')
        unreset = cur.fetchone()[0]
        results.append(('wins_reset', unreset == 0, f'{unreset} rows with wins <> 0'))

        results.append(('grants_theme', _missing_grant(cur, THEME) == 0, f'{THEME} missing for some rows'))
        results.append(('auto_spin_unlock', _missing_grant(cur, 'auto_spin_unlock') == 0,
                        'auto_spin_unlock missing for some rows'))

        cur.execute('SELECT x FROM game_state, unnest(owned_items) x '
                    'UNION SELECT x FROM game_state, unnest(active_cosmetics) x')
        unknown = sorted({row[0] for row in cur.fetchall()} - KNOWN_IDS)
        results.append(('known_items', not unknown, f'unknown ids {unknown}'))

        uids = [uid for uid, _ in before['cosmetics']]
        owned_now = {}
        if uids:
            cur.execute('SELECT user_id, owned_items FROM game_state WHERE user_id = ANY(%s)', (uids,))
            owned_now = {uid: set(owned or []) for uid, owned in cur.fetchall()}
        lost = {uid: sorted(set(ids) - owned_now.get(uid, set())) for uid, ids in before['cosmetics']}
        lost = {uid: miss for uid, miss in lost.items() if miss}
        results.append(('cosmetics_kept', not lost, f'lost cosmetics {lost}'))

        if before['real_players']:
            cur.execute('SELECT count(*) FROM season_snapshots WHERE season_number = %s',
                        (before['season_number'],))
            rows = cur.fetchone()[0]
            results.append(('snapshot_rows', rows >= 1, f'{rows} season_snapshots rows for {before["label"]}'))
        else:
            results.append(('snapshot_rows', True, 'not applicable: no real player with wins > 0'))

    results.append(('species_unchanged', after['species_md5'] == before['species_md5'],
                    'caught_species changed'))
    results.append(('users_unchanged', after['users'] == before['users'],
                    f"users {before['users']} -> {after['users']}"))
    if live_url:
        base = live_url.rstrip('/')
        results.append(_live_check('live_season', f'{base}/api/season'))
        results.append(_live_check('live_hall_of_fame', f'{base}/api/hall-of-fame'))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description='Snapshot and verify a Season 9 tide rollover.')
    sub = parser.add_subparsers(dest='cmd', required=True)
    snap = sub.add_parser('snapshot', help='record the state before the rollover')
    snap.add_argument('--db', required=True)
    snap.add_argument('--out', required=True)
    ver = sub.add_parser('verify', help='check the state after the rollover')
    ver.add_argument('--db', required=True)
    ver.add_argument('--before', required=True)
    ver.add_argument('--live-url', default='')
    args = parser.parse_args(argv)

    conn = connect_checked(args.db)
    try:
        if args.cmd == 'snapshot':
            state = read_state(conn)
            Path(args.out).write_text(json.dumps(state, indent=2))
            print(f"snapshot {state['label']} users={state['users']} -> {args.out}")
            return 0

        before = json.loads(Path(args.before).read_text())
        results = run_checks(conn, before, args.live_url)
    finally:
        conn.close()

    for name, ok, detail in results:
        print(f'PASS {name} ({detail})' if ok and detail else f'PASS {name}' if ok else f'FAIL {name}: {detail}')
    failed = [name for name, ok, _ in results if not ok]
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
