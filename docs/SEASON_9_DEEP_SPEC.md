# Season 9 "Tides": the deep rework (Charts, Surge, the Fight)

This doc extends `SEASON_9_SPEC.md`. The S9 baseline (weekly tides, universal auto-spin, medals, progressive disclosure, Tides theme and background) stays. This doc replaces **how you get stronger** within a tide and **how fishing plays**.

**One-line pitch:** every tide you chart a course. Ten points, three seas, and you can't have everything. The fish you catch decide how hard your wheel hits.

---

## 0. Diagnosis: why S9 still felt like S8

1. **The shop is a checklist.** In S8 one player (dylan) bought 57 of 59 functional items. Casual players bought cosmetics, then `winmult_1–3` and `bonusmult_1–2`, and stopped. Nobody chose anything. They either bought everything or bought the obvious next tier. Owners per functional item:

   | Owners | Items |
   |---|---|
   | 8 | `page_season8` (cosmetic) |
   | 4–5 | `trail_1` (cosmetic), `fish_tropical` (cosmetic), `prestige_unlock` |
   | 3 | `wager_unlock`, `winmult_1–3`, `bonusmult_1–2` |
   | 1 (dylan only) | most others |

2. **Fishing is a side-wallet.** Tap within 1.8 s, get "fish bucks", convert them to wins at a decaying rate. One player made 47,751 catches, nearly all by autofisher. Fishing never touched the wheel, the thing people actually watch.
3. **One engine decides the race on day 1.** Staking at 30–45% compounds at about +12% per staked spin on Steady. That is how one prod account reached ~1e38. Whoever starts staking first is unreachable by Saturday.

## 1. Research → principles

| Source | Lesson | Used here |
|---|---|---|
| **Path of Exile** keystones; **Diablo II** skill trees | A small number of big, rule-changing nodes creates identity. Ten +2% nodes don't. | One **keystone** per tree. Each one bends a rule and costs something. |
| **Slay the Spire**, **Balatro** | Builds emerge from *scarcity plus synergy*. You see more good options than you can take. | At most 14 points against 34 ranks on offer. A full tree costs 10–13. |
| **Hades** mirror (free respec) | Respec friction should be low enough to experiment and high enough that choices stick. | Adding points is always free. A refund (re-chart) is **once per London day**. |
| **Stardew Valley**, **Animal Crossing** | Time-of-day and seasonal availability make a reason to come back. It isn't a chore if nothing is lost by missing it. | Fish bite at dawn, day, dusk or night, at high or low tide, and two **migrants** visit each tide on a 4-tide cycle. |
| **Dredge**, **Stardew** fishing bar, **Sea of Thieves** | A short skill fight with readable tension beats a single timing tap. Size and records give mastery a target. | Hook → **tension fight** → land. Weight depends on how cleanly you played. Personal **records** persist. |
| **Winner-take-all tournament theory** (Lazear–Rosen; Tullock contests) | When effort or edge compounds, trailing players quit. Variance lets trailing players catch up, but only if it doesn't dominate. | Pure builds land within ~×3 of each other at the 7-day median. Riptide is the variance build, with its ×1000 tail removed. |
| **Self-Determination Theory** (autonomy, competence, relatedness) | Choice (Charts), mastery (the Fight, records) and social (podium, chat) have to all be present. | One system per need. No new currency. |
| **Horizontal vs vertical progression** | Carry-over must widen options, not raise power, or veterans run away. | What carries over is *knowledge*: the encyclopaedia, records and cosmetics. It never carries **points or multipliers**. |

## 2. What each functional item becomes

All wins-priced items leave the shop. The shop sells **cosmetics only**. Functional gear now comes from **Charts**. A talent rank *grants* existing item ids into `owned_items`, so the battle-tested spin engine (`_resolve_spin`) is unchanged.

| Item(s) | S8 owners | Fate |
|---|---|---|
| `bonusmult_1–3` / `winmult_1–2` | 3 | 🌊 Undertow / Rising Tide ranks |
| `bonusmult_4–6`, `winmult_3–7` | 1 | **Retired.** These were the vertical treadmill. |
| `regen_shield` | 1 | 🌊 Breakwater (row 3). Recharge 5 → **25** wins. |
| `resilience`, `fortune_charm`, `win_echo` | 1 | 🌊 Steady Keel, Fortune Charm, Echo |
| `wager_unlock`, `wager_stake_extend_1–2` | 3 / 1 | 🌀 Open Water, Deep Water |
| `wager_stake_extend_3`, `wager_hot_streak` | 1 | **Retired.** Hot streak never fires under chip-limited staking (sim: identical to the digit). |
| `jackpot` | 1 | 🌀 Treasure. **A staked jackpot pays ×5, not ×25.** |
| `wager_safety_net` + `wager_insurance` | 1 | 🌀 Safety Line (both) |
| `wager_double_down` | 1 | 🌀 Double or Nothing |
| `dice_charge_2–4`, `dice_extra` | 1 | 🌀 Loaded Dice, Third Die |
| `lure_1–3` | 2 | 🎣 Better Bait |
| `lure_4–5` | 1 | **Retired** |
| `autofisher_1–4` | 2 | 🎣 Deckhand (1–2), Old Salt (3–4) |
| `auto_cast` | 1 | 🎣 Auto-Cast |
| `precise_angler_1–3` | 1 | **Retired.** The tap-timing skill is replaced by the Fight. |
| `catch_of_the_day` | 1 | **Universal.** Everyone's first catch each day is worth ×5. |
| `lucky_seven`, `class_*`, `fish_to_wager`, `lure_specialization` | 1 | **Retired** |
| `guard`, `prestige_unlock`, `aquarium`, `auto_spin_unlock` | — | Already retired or universal in S9 |

Retired items stay in `SHOP_ITEMS` so `post_rollover_check` and legacy `owned_items` stay valid. `/api/buy` returns **403** for every wins-priced item, with the message `"Gear comes from Charts now — open 🧭 Charts."`. Legacy copies keep working until the next rollover strips them.

## 3. Charts (talents)

### 3.1 Points

- **Points this tide = min(14, 1 + days the tide has run (0..6) + points bought).** Days count from Fri 21:00 London. With no buying, day 0 gives 1 point and day 6 gives 7.
- **Levelling up:** `POST /api/charts/level-up` buys one point with wins. The first costs 1,000 wins and each next ×6 (1k, 6k, 36k, 216k, 1.3M, …); wins are spent (`chart_points_bought`, reset each tide). 409 at 14, 400 if short of wins.
- **Why 14, of 34 ranks:** one full tree (10–13) plus a small splash, so builds stay distinct and no one owns every tree. Sim (`talents` + 28.8k auto-spins/day): a dedicated buyer hits 14 around day 5; a non-buyer ends the tide at 7. Buying spends wins, so it costs leaderboard standing; that is the trade.
- **Why not a prestige-style reset to 0:** the leaderboard ranks by wins, so wiping them per level would punish the players the feature should reward.
- **Charting:** `POST /api/charts {alloc}` replaces the whole allocation atomically.
  - If the new allocation contains the old one (only adds), it is always allowed.
  - If it removes anything, it is a **re-chart** and is allowed once per London day (`talent_rechart_date`).
- **Rules:**
  - Rank costs 1 point.
  - Row 2 needs 2 points already in that tree. Row 3 needs 4.
  - A keystone needs 6 points in its tree, and you can hold **only one** keystone.
  - A talent with `requires` needs that talent at full rank.

### 3.2 Trees

Rank `n` grants every item up to rank `n` (the full chain), so the engine helpers behave the same in the sim and live.

**🌊 Swell: ride the streak.**

| Row | Talent | Ranks | Grants / effect | Copy |
|---|---|---|---|---|
| 1 | Undertow | 3 | `bonusmult_1..3` | "Streak bonuses ×2 / ×4 / ×8" |
| 1 | Rising Tide | 2 | `winmult_1..2` | "Every win pays ×2 / ×4" |
| 2 | Steady Keel | 1 | `resilience` | "Sometimes a loss only knocks your streak back one" |
| 2 | Fortune Charm | 1 | `fortune_charm` | "Streak bonuses sometimes pay +25%" |
| 2 | Echo | 1 | `win_echo` | "Wins sometimes pay twice" |
| 3 | Breakwater | 1 | `regen_shield` | "Blocks one loss, recharges after 25 wins" |
| K | **Spring Tide** | 1 | streak bonus ×2 | "Streak bonuses ×2 again — but you can't stake or roll dice" |

**🌀 Riptide: bet the tide.**

| Row | Talent | Ranks | Grants / effect | Copy |
|---|---|---|---|---|
| 1 | Open Water | 1 | `wager_unlock` | "Stake up to 30% of your wins. Each staked spin costs 1 🪙" |
| 1 | Loaded Dice | 3 | `dice_charge_2..4` | "Hold 2 / 3 / 4 dice charges" |
| 2 | Deep Water | 2 | `wager_stake_extend_1..2` | "Stake up to 35% / 40%" (requires Open Water) |
| 2 | Treasure | 1 | `jackpot` | "1% of wins are jackpots: ×25, or ×5 on a staked spin" |
| 2 | Safety Line | 1 | `wager_safety_net`, `wager_insurance` | "Staked losses refund a little; arm insurance once a day" (requires Open Water) |
| 3 | Third Die | 1 | `dice_extra` | "Roll three dice" |
| 3 | Double or Nothing | 1 | `wager_double_down` | "Re-stake your last win in one go" (requires Open Water) |
| K | **Rogue Wave** | 1 | +2 max dice charges, dice recharge in 5 min | "Dice come back twice as fast and stack two higher — but no 🎣 Surge for you" |

**🎣 Angler: read the water.**

| Row | Talent | Ranks | Grants / effect | Copy |
|---|---|---|---|---|
| 1 | Rich Waters | 3 | Surge ×25 / ×50 / ×100 | "Surge spins pay ×25 / ×50 / ×100 (base ×5)" |
| 1 | Better Bait | 2 | `lure_1..2` / `lure_1..3`, +25% Surge per rank | "Faster bites, bigger catches, +25% Surge" |
| 2 | Deckhand | 2 | `autofisher_1..2` | "Auto-fish while you're away" |
| 2 | Steady Hands | 3 | reel bar 0.24 → 0.28 / + bar accel 1.6 → 2.4, top speed 0.8 → 1.2 / + catch drain 0.20 → 0.15 per s | "A wider reel bar" / "Wider bar, and it moves 50% faster" / "Wider, faster bar, and a slipping fish gets away 25% slower" |
| 2 | Auto-Cast | 1 | `auto_cast` | "Recast automatically" |
| 3 | Old Salt | 1 | `autofisher_1..4` (requires Deckhand 2) | "Auto-fish catches rares, and more often" |
| K | **Deep Sea** | 1 | rare/legendary bite ×3; junk and commons don't bite; bites 50% slower | "Only the big ones bite — and they take their time" |

Tree sizes: Swell 10, Riptide 11, Angler 13. With at most 14 points, a full tree leaves 1–4 points for a splash, never a second tree.

### 3.3 Keystone trade-offs (enforced server-side)

- **Spring Tide:** `validate_stake` → 0, and `/api/roll-dice` → 403 `"Spring Tide: no dice"`.
- **Rogue Wave:** surge is neither earned nor spent.
- **Deep Sea:** applied in `roll_fish` and `cast_line`.

## 4. Surge: fishing powers the wheel

- Every **manual** catch adds Surge spins:

  | Junk | Common | Uncommon | Rare | Legendary |
  |---|---|---|---|---|
  | 0 | 6 | 15 | 40 | 150 |

  This is scaled by catch quality (`0.5 + size_ratio`) and by Better Bait (+25% per rank).
- **Auto** catches (tick and AFK catch-up) give **×0.25**, rounded, with a minimum of 1 for non-junk.
- Each spin, manual or auto (including the auto-spin catch-up), spends 1 Surge spin while any remain. A Surge spin pays **(win mult + M − 1)** and **(bonus mult + M − 1)**. That is *additive*, not multiplicative: M = 5 for everyone, 25/50/100 with Rich Waters.
- Additive is deliberate. Multiplicative surge × Undertow made the best hybrid 1.8e10 against 1.7e9 for pure Swell (sim run6). Additive brings it to 2.8e9 (run7).
- The UI shows **"🌊 Surge ×M · N spins"** under the wins / losses scoreboard while N > 0.

## 5. Fishing: the Fight

**Flow:** cast → wait (nibbles) → **bite** → tap within 1.8 s to **hook** → **fight** → land or lose.

| Step | Server | Client |
|---|---|---|
| Cast | `POST /api/cast` (unchanged). Bite delay from lure level; Deep Sea ×1.5. | Bobber, nibble wobble |
| Hook | `POST /api/reel` now **hooks**. It checks the bite window, then picks the species from what's biting now and stores `fishing_species` and `fishing_hooked_at`. Returns `{result:'hooked', rarity, fight_s}`. The species is hidden. | Fight starts |
| Fight | — | Stardew-style. The fish swims along the meter; hold (mouse, touch or Space) to push your green reel bar right, release and it drifts left (it bounces a little off the ends). The catch meter starts at 30%, fills at 1/`fight_s` per s while the fish is in the bar and drains 0.20/s while it isn't. Full: landed. Empty: "It slipped the hook." |
| Land | `POST /api/land {landed, quality}`. Elapsed must be ≥ 60% of `fight_s` and ≤ 45 s, otherwise `too_fast` / `timeout`. Quality is clamped to [0, 1]. | Result card: species, kg, record badge, +🐟, +Surge |

- **Fight length by rarity (`fight_s`):** junk 1.5, common 3, uncommon 4.5, rare 6, legendary 8. A perfect fight takes 0.7 × `fight_s`, so it clears the server's 60% floor.
- **Fish movement by rarity** (speed in meter widths/s, new target per s): junk 0.10 / 0.3, common 0.25 / 0.6, uncommon 0.35 / 0.8, rare 0.45 / 1.0, legendary 0.58 / 1.3.
- **Tuning** (simulated player with 0.22 s reaction; a casual to decent skill band): with no Steady Hands, commons land 94–96%, uncommons 75–85%, rares 36–51%, legendaries 4–10%. With Steady Hands 3: rares 90–97%, legendaries 43–70%. Losing must be possible: the old tension fight could not be lost by a player who simply let go.
- **Fish pull strength:** rises with rarity, so legendaries surge harder and more often.
- **Weight:** `kg = min + (max − min) × (0.5 × random + 0.5 × quality)`. `size_ratio = (kg − min)/(max − min)`.
- **Values:**
  - 🐟 value = `fish_value × (0.5 + size_ratio)`, with Lucky Fish ×2 and Catch of the Day ×5 on top.
  - Surge as in §4.
- **Records:** `fish_records[species] = max kg` persists across tides. A new record shows **"🏆 New record!"**.

`ponytail:` quality is client-reported, so a modified client can always send 1.0. The server bounds it (≤ 1, minimum fight duration, server-picked species), so the gain is capped at ×1.5 value. Upgrade to server-side tension simulation only if the leaderboard shows abuse.

**Auto-fish:**
- Unchanged cadence.
- Rolls from the same availability-aware catalog.
- Never catches legendaries, and catches rares only with Old Salt.
- Random size.
- Updates records.
- Surge ×0.25.

## 6. The catalog: 46 species

The 13 original ids are kept and are **always available**. New species have a **window** (London time: dawn 05–09, day 09–17, dusk 17–21, night 21–05) and/or a **tide** (high or low). The tide alternates every 6 h 12 m 30 s from 2026-01-01 00:00 UTC, which counts as high. **Migrants** visit only in their slot (`week_number % 4`), two per tide. A shared emoji is told apart by a CSS `hue-rotate`.

| id | Emoji | Name | Rarity | Spawn w | 🐟 | kg | When | Hint |
|---|---|---|---|---|---|---|---|---|
| old_boot | 👢 | Old Boot | junk | 4 | 0 | 0.5–1.5 | any | "Someone walked home with one shoe." |
| tin_can | 🥫 | Tin Can | junk | 3 | 0 | 0.1–0.4 | any | "Please recycle." |
| minnow | 🐟 | Minnow | common | 14 | 1 | 0.01–0.05 | any | "Everywhere, always." |
| shrimp | 🦐 | Shrimp | common | 7 | 2 | 0.01–0.04 | any | "Small, but it counts." |
| clownfish | 🐠 | Clownfish | common | 7 | 3 | 0.1–0.3 | any | "Lives in the reef." |
| pufferfish | 🐡 | Pufferfish | common | 6 | 3 | 0.2–1.0 | any | "Don't squeeze." |
| sardine | 🐟↻180 | Sardine | common | 7 | 2 | 0.05–0.15 | any | "Swims in thousands." |
| mackerel | 🐟↻90 | Mackerel | common | 6 | 3 | 0.3–1.2 | day | "Bites in daylight." |
| sea_snail | 🐌 | Sea Snail | common | 4 | 2 | 0.02–0.1 | low tide | "Clings to rocks the tide uncovers." |
| hermit_crab | 🐚 | Hermit Crab | common | 4 | 3 | 0.05–0.3 | low tide | "Look in the rock pools." |
| mudskipper | 🐸 | Mudskipper | common | 3 | 4 | 0.05–0.2 | day, low | "Walks the mud flats in the sun." |
| crab | 🦀 | Crab | uncommon | 6 | 8 | 0.5–3 | any | "Sideways and stubborn." |
| squid | 🦑 | Squid | uncommon | 5 | 8 | 0.3–4 | any | "Ink and arms." |
| octopus | 🐙 | Octopus | uncommon | 3 | 12 | 1–15 | any | "Too clever for most lines." |
| moon_jelly | 🎐 | Moon Jelly | uncommon | 3 | 10 | 0.2–2 | night | "Glows after dark." |
| sea_turtle | 🐢 | Sea Turtle | uncommon | 2 | 14 | 20–150 | day, high | "Rides the high tide in daylight." |
| moray_eel | 🐍 | Moray Eel | uncommon | 2 | 12 | 2–30 | night | "Hunts at night." |
| parrotfish | 🐠↻120 | Parrotfish | uncommon | 2.5 | 10 | 1–9 | day | "Crunches coral by day." |
| lionfish | 🐡↻300 | Lionfish | uncommon | 2 | 12 | 0.5–1.4 | dusk | "Comes out as the light goes." |
| flounder | 🐟↻30 | Flounder | uncommon | 2.5 | 9 | 0.5–5 | low tide | "Flat on the sand when the water's shallow." |
| pearl_oyster | 🦪 | Pearl Oyster | uncommon | 2 | 15 | 0.1–0.5 | dawn | "Opens at first light." |
| lobster | 🦞 | Lobster | rare | 3 | 20 | 0.5–9 | any | "Heavy claws." |
| dolphin | 🐬 | Dolphin | rare | 1.5 | 30 | 70–300 | any | "Friendly, fast." |
| shark | 🦈 | Shark | rare | 1.2 | 40 | 50–900 | any | "Bring a bigger rod." |
| grey_seal | 🦭 | Grey Seal | rare | 1.2 | 30 | 100–300 | high tide | "Comes in on the high water." |
| swordfish | 🐟↻200 | Swordfish | rare | 1 | 35 | 50–650 | day | "Fast in the sunlit water." |
| hammerhead | 🦈↻60 | Hammerhead | rare | 0.8 | 45 | 200–500 | dusk | "Patrols at dusk." |
| anglerfish | 🏮 | Anglerfish | rare | 0.8 | 35 | 0.5–50 | night | "Follow the little light." |
| sunken_chest | 🧰 | Sunken Chest | rare | 0.6 | 60 | 5–40 | dawn | "Glints at dawn." |
| message_bottle | 🍾 | Message in a Bottle | rare | 0.8 | 25 | 0.5–1 | dusk | "Drifts in with the evening." |
| orca | 🐳 | Orca | rare | 0.6 | 50 | 3000–6000 | high tide | "Hunts the high tide." |
| whale | 🐋 | Blue Whale | legendary | 0.4 | 75 | 50000–150000 | any | "The biggest thing alive." |
| mermaid | 🧜 | Mermaid | legendary | 0.15 | 120 | 50–90 | any | "Sailors' stories are true." |
| lucky | ⭐ | Lucky Fish | legendary | 0.25 | 100 | 0.1–1 | any | "Doubles your next catch." |
| kraken | 🦑↻330 | Kraken | legendary | 0.12 | 150 | 500–2000 | night, high | "High water, dead of night." |
| sea_dragon | 🐉 | Sea Dragon | legendary | 0.1 | 180 | 100–900 | dawn | "Seen once at sunrise." |
| golden_koi | 🐠↻40 | Golden Koi | legendary | 0.12 | 140 | 2–12 | dusk | "Gold in the last light." |
| ghost_ship | 🏴‍☠️ | Ghost Ship | legendary | 0.08 | 200 | 100000–300000 | night, low | "Low tide, no moon, no crew." |
| narwhal | 🦄 | Narwhal | rare | 0.8 | 45 | 800–1600 | migrant 0 | "Visits every fourth tide." |
| sea_otter | 🦦 | Sea Otter | uncommon | 2 | 14 | 14–45 | migrant 0 | "Visits every fourth tide." |
| leatherback | 🐢↻200 | Leatherback | rare | 0.8 | 40 | 250–700 | migrant 1 | "Visits every fourth tide." |
| penguin | 🐧 | Penguin | uncommon | 2 | 12 | 1–30 | migrant 1 | "Visits every fourth tide." |
| ocean_sunfish | 🌞 | Ocean Sunfish | rare | 0.8 | 45 | 250–1000 | migrant 2 | "Visits every fourth tide." |
| saltwater_croc | 🐊 | Saltwater Croc | rare | 0.6 | 50 | 200–1000 | migrant 2 | "Visits every fourth tide." |
| blue_marlin | 🐟↻220 | Blue Marlin | rare | 0.7 | 45 | 100–800 | migrant 3 | "Visits every fourth tide." |
| coelacanth | 🐟↻260 | Coelacanth | rare | 0.5 | 60 | 30–90 | migrant 3 | "Visits every fourth tide." |

**Encyclopaedia:**
- Every entry shows its hint and its when-icons (🌅 dawn, ☀️ day, 🌇 dusk, 🌙 night, 🌊 high, 🏖️ low, 🧭 migrant).
- Entries biting right now get a **"Biting now"** badge.
- Discovered entries show the record kg.
- A header shows "Discovered N / 46 · Tide: High (turns in 2h 14m)".

## 7. What carries over, and why no one runs away

| Carries across tides | Resets each tide |
|---|---|
| Medals, cosmetics, encyclopaedia (`caught_species`), **records** (`fish_records`) | Wins, Chart, Surge, 🪙 chips, everything functional |

- Carry-over is **horizontal**: knowledge, collection, records.
- Points are equal for everyone on a given day. Nothing bought, grown or caught last tide makes this tide's wheel stronger.
- The race starts level every Friday.
- The ×1000 staking tail is cut (staked jackpot ×5).
- Chips are limited to 3 a day plus the goal's reward, about 31 a tide.
- Bounties pay 🌊 Surge spins (100 / 200 / 300 by position), not chips. Sim: at 52 chips a tide Riptide's median jumps from 1.9e9 to 5.6e10, and at 73 (the old 1/2/3-chip bounties) to 5.9e11. Staking compounds, so chips stay scarce.
- The bounty pool is build-neutral (streaks and fishing only): Catch 10 fish, Reach a 10-spin win streak, Land 5 fish in a fight, Land a rare or legendary fish, Land a trophy fish (top 10% of its size range). Stake, jackpot, bank and double-down bounties were removed, since most builds could never finish them.
- Arming insurance costs a chip and the staked spin costs another, so an insured spin costs 2.
- Inverted mode lets anyone stake (losses, not wins) without Open Water; it still costs a chip. Intended: it's the week's wildcard wheel.
- Charting unequips any class (classes are shop gear no talent grants) and disarms Double Down / insurance whose talent was taken back.

## 8. Balance (sim, `_resolve_spin` directly, 7 days × 28,800 auto-spins, `REGEN_SHIELD_RECHARGE_WINS=25`)

| Build (10 pts) | Median | Min | Max | Seeds |
|---|---|---|---|---|
| No chart | 1.05e7 | 9.7e6 | 1.2e7 | 20 |
| 🌊 Swell full + Spring Tide | 1.67e9 | 1.58e9 | 1.78e9 | 12 |
| 🎣 Angler full (Surge ×100, ~23k surge/day) | 8.6e8 | 7.8e8 | 9.2e8 | 12 |
| 🌀 Riptide full (32 chips @40%) | 1.9e9 | 2.3e8 | 4.3e10 | 12 |
| Hybrid: Undertow 3 + Keel + Breakwater / Rich Waters 3 + Deckhand 2 | 2.8e9 | 2.5e9 | 3.1e9 | 12 |
| Hybrid: Undertow 3 + Rising Tide 2 / Rich Waters 3 + Deckhand 2 | 3.6e8 | 3.2e8 | 3.9e8 | 12 |

**Before** (same harness): Riptide at 6 staked spins a day at 40% with the ×25 staked jackpot went to 1.5e10. 15 a day went to 6e13. Multiplicative surge made the best hybrid 1.8e10, winning 19 of 20 seeds.

**Reading:**
- The three pure builds sit within ×2.2 of each other at the median.
- Riptide trades a lower floor for a 20× ceiling. That is the catch-up lever.
- The best hybrid beats the best pure build by ×1.7. Hybrids should be viable, and "Breakwater + fishing" is a real build.
- Breakwater stays at row 3 so it costs 5 points.

## 9. System count (keep it flat or falling)

| | Before (S9 baseline) | After |
|---|---|---|
| Ways to get stronger | Shop tiers (59 functional items), classes, Lucky Seven, Precise Angler | **Charts** (one panel) |
| Fishing | Tap timing, Precise Angler, fish bucks, exchange both ways | **Fight**, Surge, fish bucks (pot and exchange unchanged) |
| Currencies | wins, losses, fish bucks, tokens | same (tokens become stake chips) |
| New panels | — | Charts (+1), Surge chip (inline) |
| Removed panels | — | functional shop tabs, Lucky Seven counter, class equip, wins→fish exchange |

Net: −3 systems, +2.

## 10. Schema and API

- **Migration 078** (`078_charts_surge_fight.sql`): `talent_alloc JSONB`, `talent_rechart_date DATE`, `surge_spins INT`, `fish_records JSONB`, `fishing_species TEXT`, `fishing_hooked_at TIMESTAMPTZ`.
- **Rollover** resets `talent_alloc='{}'`, `talent_rechart_date`, `surge_spins`, `fishing_species` and `fishing_hooked_at`. `fish_records` persists.
- **New routes** (all CSRF-protected): `GET /api/charts`, `POST /api/charts`, `POST /api/land`. `GET /api/fish-catalog` is read-only.
- **Changed routes:**
  - `/api/reel` (hook).
  - `/api/buy`: 403 for wins items.
  - `/api/spin`: a staked spin costs 1 🪙 chip, and 400 `"Out of 🪙 chips — claim today's 3"` when there are none. `pay_with_tokens` is ignored.
  - `/api/state` adds `surge_spins`, `talent_alloc`, `talent_points` and `fish_records`.
- **Goal reward:** 500 🪙 → **10 🪙**.

## 11. UI copy (exact)

- **Charts panel title:** "🧭 Charts".
- **Charts level line:** "Level {points} / 14 · 1 to start, +1 free each day, {bought} bought · resets with the tide"; "Next level: {wins} / {cost} 🏆"; button "⬆ Level up · {cost} wins"; at cap "Max level · your Chart is full for this tide".
- **Charts subtitle:** "{spent} / {points} points placed".
- **Tree headers:**
  - "🌊 Swell — ride the streak"
  - "🌀 Riptide — bet the tide"
  - "🎣 Angler — read the water"
- **Buttons:**
  - "Set course" (confirms pending changes)
  - "Re-chart" (clears all; label "Re-chart (1 left today)" / "Re-chart tomorrow")
  - "Cancel"
- **Locked row tooltip:** "Needs {n} points in {tree}".
- **Keystone lock tooltip:** "Needs 6 points in {tree} · one keystone only".
- **Surge chip:** "🌊 Surge ×{M} · {N} spins".
- **Fight:**
  - prompt "Hold to reel — keep the line in the green"
  - snap "Snap! The line broke."
  - slack "It slipped the hook."
  - success "{emoji} {name} · {kg} kg"
  - "+{v} 🐟 · +{s} Surge"
  - "🏆 New record!"
- **Shop Chart strip** (top of the shop, opens the Charts panel): "🧭 Chart", "Lv {points}", "{n} to place" / "{spent} / {points} placed" / "Max level", "Open ›", an XP bar toward the next level, and every talent as an icon (lit when ranked, rank badge if max rank > 1, keystones round).
- **What's New card** (replaces the S9 card's lines):
  1. "🧭 Charts: one free point a day, and level up with wins for more, up to 14. Spend them on Swell, Riptide or Angler — you can't have it all."
  2. "🎣 Fishing is a fight now, and every catch charges 🌊 Surge spins for your wheel."
  3. "Every Friday the tide turns: wins and Charts reset; medals, fish and records are forever."
- **Progressive disclosure:**
  - Charts shows from spin 1, with a pulsing dot while points are unspent.
  - The Surge chip shows whenever `surge_spins > 0`.

## 12. Tickets (phases; commit and push each)

| # | Ticket | Acceptance |
|---|---|---|
| D1 | `talents.py`, migration 078, `/api/charts`, points by tide day, re-chart, `/api/buy` 403, rollover reset, keystone rules (Spring Tide stake/dice) | `tests/test_charts.py` |
| D2 | Charts UI | E2E: allocate, lock rules, set course, re-chart |
| D3 | Catalog + availability + `/api/fish-catalog` + records + Surge (catch and spin, AFK both) | `tests/test_catalog.py`, `tests/test_surge.py` |
| D4 | Hook / fight / land + tension minigame | `tests/test_fight.py`; E2E fight with mouse.down/up |
| D5 | Encyclopaedia, shop cleanup, What's New, patch notes, chips | E2E sweep, screenshots |

## 13. Test plan

**Unit / integration** (pytest against `wheeldb_test`):
- **Charts:** points by tide day 0..6 (4..10); add-only allowed repeatedly; refund once a day, then 409; row gates; keystone gate plus one-keystone; `requires`; overspend; unknown id or rank above max → 400; `owned_items` recompute keeps cosmetics and strips ungranted gear; rollover clears.
- **Shop:** every wins item → 403; cosmetics still buy.
- **Spring Tide:** stake forced to 0; dice 403.
- **Rogue Wave:** no surge earned.
- **Chips:** a staked spin costs 1; 0 chips → 400; auto-spin never charges.
- **Staked jackpot:** ×5.
- **Surge:**
  - additive multiplier;
  - decrements per spin, including the tick catch-up;
  - manual vs auto amounts;
  - Better Bait bonus;
  - zero for junk.
- **Catalog:**
  - 46 ids, the 13 originals present;
  - every field valid;
  - availability by window, tide and migrant slot;
  - tide phase math;
  - `roll_fish` never returns an unavailable species;
  - auto never legendary, rare only with level 4;
  - Deep Sea filter.
- **Fight:**
  - hook outside window → miss;
  - hook stores the species;
  - land too fast → `too_fast`;
  - land after 45 s → `timeout`;
  - quality clamped;
  - `landed:false` clears the line;
  - land without a hook → `no_session`;
  - weight bounds;
  - records update only upward;
  - Catch of the Day ×5 universal;
  - Lucky doubles.
- **Exploit:** a wins→fish→wins loop yields no gain, because Surge is not convertible.
- **CSRF:** the new POST routes are listed in `test_csrf_enforcement`.

**E2E** (Playwright, claudeqa1 on staging; state seeded through `wheeldb_staging` only):
1. Charts:
   - allocate 3 points;
   - set course;
   - add-only after the seeded day;
   - re-chart;
   - a second re-chart is blocked.
2. Shop: no functional tab, cosmetic buy works.
3. Fish:
   - cast, hook, hold/release fight, land;
   - result card and record;
   - Surge chip appears;
   - spin consumes Surge.
4. Encyclopaedia: 46 entries, biting badges, hints.
5. Staking with Open Water: chip cost, out-of-chips message.
6. Console has no errors, on mobile and desktop.

## 14. Rollover safety (staging timer Fri 21:00 BST)

- Every talent-granted id is in `SHOP_ITEMS`, so `post_rollover_check` holds.
- The rollover SQL clears the new columns.
- Migration 078 is applied to `wheeldb_staging` before any code that reads it is pushed.
- A pytest runs `advance_season` on a user with a Chart and asserts the post-check conditions.
