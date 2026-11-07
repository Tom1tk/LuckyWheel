"""Tide Regatta: each tide day (21:00-21:00 London) is a race.

A player's first 3 manual stakes in a race count. Each scores what the wheel
landed: lose 0, win 1, jackpot 5, whatever Treasure / Echo / Double or Nothing
then paid. Places score 5/3/2/1 race points (ties share the higher place); a
race score of 0 doesn't place. The tide is ranked by race points, then wins.
"""
import datetime as dt

import talents
import tide_stats

STAKES_PER_RACE = 3
RACES = 7
SCORES = {'lose': 0, 'win': 1, 'jackpot': 5}
POINTS = (5, 3, 2, 1)


def race_number(now_utc: dt.datetime) -> int:
    return talents.tide_day(now_utc) + 1


def race_ends_at(now_utc: dt.datetime) -> dt.datetime:
    # tide_start is London-aware, so adding days keeps 21:00 across DST.
    return talents.tide_start(now_utc) + dt.timedelta(days=race_number(now_utc))


def log_stake(cur, user_id: int, now_utc: dt.datetime, result: str) -> None:
    """Count this stake if it is one of the player's first 3 in the race.

    Runs in the spin's transaction; ON CONFLICT keeps a race between two
    requests from raising (and so from rolling the spin back).
    """
    cur.execute(
        '''INSERT INTO regatta_stakes (user_id, tide_date, race, n, result, score)
           SELECT %s, %s, %s, count(*) + 1, %s, %s
             FROM regatta_stakes WHERE user_id = %s AND tide_date = %s AND race = %s
           HAVING count(*) < %s
           ON CONFLICT DO NOTHING''',
        (user_id, tide_stats.tide_date(now_utc), race_number(now_utc), result, SCORES[result],
         user_id, tide_stats.tide_date(now_utc), race_number(now_utc), STAKES_PER_RACE),
    )


def race_scores(cur, tide_date: dt.date) -> dict:
    """{race: {user_id: (username, score, [scores in order])}}, test users hidden."""
    cur.execute(
        '''SELECT r.race, r.user_id, u.username, r.score
             FROM regatta_stakes r JOIN users u ON u.id = r.user_id
            WHERE r.tide_date = %s AND u.ip_address <> '127.0.0.1'
            ORDER BY r.race, r.user_id, r.n''',
        (tide_date,),
    )
    out: dict = {}
    # Callers pass plain or RealDict cursors.
    rows = [tuple(r.values()) if isinstance(r, dict) else r for r in cur.fetchall()]
    for race, uid, name, score in rows:
        _, total, scores = out.setdefault(race, {}).get(uid, (name, 0, []))
        out[race][uid] = (name, total + score, scores + [score])
    return out


def placings(race: dict) -> dict:
    """{user_id: points} for one race; ties share the higher place."""
    totals = [v[1] for v in race.values() if v[1] > 0]
    pts = {}
    for uid, (_, total, _) in race.items():
        better = sum(1 for t in totals if t > total)
        pts[uid] = POINTS[better] if total > 0 and better < len(POINTS) else 0
    return pts


def tide_points(cur, tide_date: dt.date, before_race: int = RACES + 1) -> dict:
    """{user_id: race points} from races numbered below before_race."""
    total: dict = {}
    for race, scores in race_scores(cur, tide_date).items():
        if race < before_race:
            for uid, p in placings(scores).items():
                total[uid] = total.get(uid, 0) + p
    return total


def race_end_msg(race: int, scores: dict) -> str | None:
    top = max((v[1] for v in scores.values()), default=0)
    if top == 0:
        return None
    names = sorted(v[0] for v in scores.values() if v[1] == top)
    if len(names) == 1:
        return f'🏁 Race {race} goes to {names[0]}, scoring {top}.'
    return f'🏁 Race {race} is a dead heat: {" and ".join(names)}, scoring {top}.'


def announce_finished(cur, now_utc: dt.datetime) -> list:
    """Messages for races that have ended and weren't announced yet (each once).

    Race 7 ends at the turn, so the new tide's first call announces it.
    """
    today = tide_stats.tide_date(now_utc)
    due = [(today, r) for r in range(1, race_number(now_utc))]
    due.append((today - dt.timedelta(days=7), RACES))
    msgs = []
    for tide, race in due:
        cur.execute('INSERT INTO regatta_announced (tide_date, race) VALUES (%s, %s) '
                    'ON CONFLICT DO NOTHING RETURNING race', (tide, race))
        if cur.fetchone():
            msg = race_end_msg(race, race_scores(cur, tide).get(race, {}))
            if msg:
                msgs.append(msg)
    return msgs
