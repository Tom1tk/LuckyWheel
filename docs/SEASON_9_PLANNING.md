# Lucky Wheel — Season 9 Planning Document

> Prepared from live database analytics (wheeldb, season 8 / "Casino" era),
> chat history, `models.py`, `wheel_modes.py`, `wagers.py`, `prestige.py`,
> `community_goals.py`, and Season 8 postmortem docs. Planning only — the
> build spec that follows is SEASON_9_BUILD_SPEC.md.

---

## TL;DR

Season 8's problem was **not** that nothing shipped — it's that **one player
solved the game in 24 hours** and the economy ran so far past comprehension
that everyone else stopped playing. The live numbers make this unambiguous:

- **5 real players spun** (dylan, worm67, tom7, chudwigvanbetahoven, f22).
  griffin, p3nnyth3p3nguin and netenyahu1948 never spun at all.
- **dylan hit Prestige 20 (max) on day one** and reached **1.03e38 wins in 453
  spins** — a number so large that tom7 asked *"WHAT is that pascal win
  number"* and dylan himself said *"too many big number"*.
- **Everyone else quit within two weeks.** The last real chat message is
  2026-07-07. The season expired 2026-07-03 and **nobody rolled it over** —
  the game has been silently dead for four weeks.
- **Community systems never filled.** Singularity reached 0.15% of target
  (147,930 / 100M, and 99.3% of that was dylan). The fishing goal is 0/5000.
  dylan hit his per-player caps on the jackpot (50/50) and wager (15,000/15,000)
  goals — the caps worked, the *targets* were 5–10x too big for 5 players.
- **Bounties were the healthiest feature** — every active player used them
  (dylan 14 days, worm67 18, tom7 10, chud 6). Deterministic per-day bounties
  are the engagement loop that worked.

Season 9 must therefore:

1. **Keep numbers readable.** Cap the runaway compounding (vault + stake decay)
   so a "big win" is comprehensible and competitive again.
2. **Scale community systems to ~5 players.** Make singularity, goals, and the
   pot actually fill — that's the reward loop that was 100% dead.
3. **Give players a reason to return.** A fresh rollover resets everything to
   parity (dylan's 1e38, his maxed prestige and his bought-out shop all reset),
   plus new content: Arcade theme, Zealot wheel mode, dragonfish, prestige
   titles.
4. **Keep what worked.** Daily bounties, the wheel-mode rotation (now with
   mirror reachable + zealot), prestige as the prestige system, fishing.

---

## Table of Contents

1. [Where the game is now — Season 8 (Casino) state](#1-where-the-game-is-now--season-8-casino-state)
2. [Player analysis](#2-player-analysis)
3. [What happened and why](#3-what-happened-and-why)
4. [Season 9 design pillars](#4-season-9-design-pillars)
5. [Season 9 scope](#5-season-9-scope)
6. [Open decisions & risks](#6-open-decisions--risks)

---

## 1. Where the game is now — Season 8 (Casino) state

Season 8 (internal season 9, player-facing **8**, name "Casino") started
2026-06-26 23:44 UTC and ended 2026-07-03 23:44 UTC. It has **not been rolled
over** — `ends_at` has passed by four weeks and `ensure_current_season` only
logs a warning.

**Final snapshot (internal season 8 → ended at rollover):**

| Position | Player  | Wins        |
|----------|---------|-------------|
| 1        | tom7    | 297,836,900,436 |
| 2        | worm67  | 131,702,750,206 |
| 3        | dylan   | 3,596,467,270   |

**Live state (season 8, "Casino" era):**

| Player    | Wins   | Losses | Prestige | Spin count | Owned items | Notable |
|-----------|--------|--------|----------|-----------|-------------|---------|
| dylan     | 1.03e38 | 44    | 20 (max) | 453        | ~60 items, everything in the shop | cumulative 1.53e38 |
| worm67    | 149    | 80     | 4        | 235        | 16 items (wager + early upgrades) | 26 fish clicks |
| chudwigvanbetahoven | 62 | 2 | 3 | 10 | prestige_unlock + 3 cosmetics | — |
| tom7      | 45     | 3      | 2        | 76         | 11 items (wager + win power) | — |
| f22       | 4      | 2      | 0        | 5          | 2 cosmetics | — |
| griffin   | 0      | 0      | 0        | 0          | 1 cosmetic  | legacy 539,281 wins |
| p3nnyth3p3nguin / netenyahu1948 | 0 | 0 | 0 | 0 | 1 cosmetic | never spun |

**Community state:**

| System     | Progress                            | Verdict |
|------------|-------------------------------------|---------|
| Singularity | 147,930 / 100,000,000 (0.15%)      | dead — dylan = 99.3% of it |
| Goal: jackpot | 98 / 500 (caps: dylan 50, chud 21, worm 16, tom 11) | targets ~5x too big |
| Goal: wager  | 15,000 / 100,000 (dylan at his 15k cap) | targets ~5x too big |
| Goal: species | 30 / 100                           | closest to filling |
| Goal: fish   | 0 / 5,000                           | fishing abandoned |
| Goal: prestige | 2 / 50                             | only 2 prestiges happened |
| Pot          | 0 / 500, filled=false                | legacy system, idle |
| Chat         | 80 real rows; last activity 2026-07-07 | silent since |

---

## 2. Player analysis

- **dylan** is the operator/whale. He bought every functional item, maxed
  prestige day one, and his 453 spins compounded to 1.03e38. He is the
  economy's entire output. His own chat: *"too many big number"*.
- **worm67** is the most *consistent* player (235 spins, most bounty days, the
  only real fisher). He reached prestige 4 and left — he played honestly and
  still fell 36 orders of magnitude behind dylan.
- **tom7** won the *previous* season (297B) but this season played only 76
  spins and left after the numbers went absurd.
- **chudwigvanbetahoven** got rate-limited ("Why is my ass getting timed out")
  and quit after 10 spins.
- **f22, griffin, p3nnyth3p3nguin, netenyahu1948** barely exist this season.

The pattern: players return at a season launch, play for 1–2 weeks, and leave
when the leaderboard becomes unreadable or the community systems stall.

---

## 3. What happened and why

1. **The economy ran away in 24 hours.** dylan reached prestige 20 and 1e38
   on day one. The compounding stack — 45% stake × max win/bonus power ×
   classes (1.2–1.25×) × jackpot 25× × win_echo 2× × double-down 45× × hot
   streak +50% — is multiplicative and unbounded. Prestige 20's flat +40% is
   irrelevant next to a ×1,000,000,000 jackpot chain.
2. **Unreadable numbers ended the game.** The chat shows players literally
   could not parse the scores ("pascal win number"). When you can't read the
   scoreboard, there's no score to chase.
3. **Community targets were designed for a full server.** Every cap worked;
   the targets (100M, 500, 50, 100k, 5,000) needed ~20+ players to fill in a
   week. With 5 players, nothing ever completed, so the reward loop
   (tokens → insurance → gambling) never turned.
4. **Fishing was abandoned.** fish goal 0/5,000; only worm67 fished at all.
   The singularity (a fish-click sink) was fed almost entirely by dylan.
5. **The season was never rolled over.** `ends_at` passed 2026-07-03 and no
   one advanced the season — four weeks of silence since.

---

## 4. Season 9 design pillars

1. **Legible economy.** Add a **payout vault cap** (wins above the cap bank
   instead of compounding) and **stake decay** (max stake % falls as your
   balance grows). Numbers stay readable, and a runaway whale can't compound
   past the field.
2. **Scaled community rewards.** Retune singularity (100M → 5M), goals, and
   the pot to a ~5-player server so they actually complete and pay out.
3. **Fresh-start re-engagement.** The S9 rollover resets wins, prestige, and
   functional items for *everyone* — dylan's 1e38 and bought-out shop do not
   carry over. Combined with new content, this is the relaunch hook.
4. **Keep what worked.** Daily bounties, prestige, wager, wheel-mode rotation,
   fishing, chat. Add to, don't tear down.

---

## 5. Season 9 scope

Theme **"Arcade"** (neon synthwave), plus:

- **Content:** page theme `page_season9` + arcade canvas background;
  wheel themes `theme_arcade`/`theme_pixel`/`theme_holo`; fish skins
  `fish_joystick`/`fish_pixel`/`fish_ghost`; **dragonfish** legendary catch.
- **Gameplay:** **Zealot** wheel mode (8% jackpot, ×100) joins the rotation,
  which now includes **mirror** (fixes mirror + its bounty being unreachable);
  **prestige titles** (level → title ladder).
- **Economy (the fix):** **vault payout cap** + **stake decay**;
  **singularity retune**; **community-goal retune**; pot rollover target 500.
- **Docs/ops:** planning/build-spec/tickets/progress docs, PATCH_NOTES + README
  Season 9 sections, migrations 073–075, staging verification + rollover.

Details in SEASON_9_BUILD_SPEC.md.

---

## 6. Open decisions & risks

- **Payout cap shape** (`max(1M, wins × 2)` with overflow → vault). Risk:
  players may feel a jackpot "capped" is a nerf — mitigated by banking the
  overflow (it's claimable, not lost) and by it only applying at ≥ 1M wins.
- **Stake decay floor.** Min 10% max stake at 1B+ wins keeps the wager system
  usable without re-enabling runaway compounding.
- **Rollover naming.** `advance_season` gains an optional pfn/name override so
  the staging rollover can set player-facing 9 / name "Arcade" explicitly.
- **dylan's lifetime cumulative** (1.53e38) persists for tier-3 gating only;
  his per-season wins and prestige reset with everyone else. No special-casing
  him — the economy fixes are the systemic answer.
