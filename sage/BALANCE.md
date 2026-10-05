# Sage balance and ranks

The initial kit used level-60 spell rows at every character level.
Ronfaure was level 15 but still knew those rows.
The flat damage and healing values bypassed the normal rank progression.
Several mana costs were also much lower than the comparable stock spells.

The new kit uses the stock 5875 realm data as its baseline.
Dosis copies Smite ranks. Diagnosis copies Lesser Heal and Flash Heal ranks.
Prognosis copies Prayer of Healing ranks.
Each copy keeps the stock mana cost, cast time, damage range, level growth, and spell-power coefficient.
Nature damage and the Sage names remain custom.

## Rank progression

| Action | Learn levels | Stock baseline |
|---|---|---|
| Dosis | 1, 6, 14, 22, 30, 38, 46, 54 | Smite |
| Diagnosis | 1, 4, 10, 20, 26, 32, 38, 44, 50, 56 | Lesser Heal, then Flash Heal |
| Prognosis | 30, 40, 50, 60 | Prayer of Healing |
| Eukrasian Dosis | 4, 10, 18, 26, 34, 42, 50, 58 | Shadow Word: Pain |
| Eukrasian Diagnosis | 6, 12, 18, 24, 30, 36, 42, 48, 54, 60 | Power Word: Shield |
| Eukrasian Prognosis | 30, 40, 50, 60 | 65% of the matching Prayer of Healing average roll |
| Phlegma | 10, 16, 22, 28, 34, 40, 46, 52, 58 | Mind Blast, instant with a 30-second cooldown |
| Egeiro | 10, 22, 34, 46, 58 | Resurrection |
| Druochole | 20, 26, 32, 38, 44, 50, 56 | Flash Heal, instant and charge-limited |

Kardia and Addersgall unlock at level 1. Eukrasia unlocks at level 4.
Icarus unlocks at level 20. Kerachole unlocks at level 30.

A character becomes eligible for Sage progression when they know any Dosis rank.
The server grants eligible ranks on login, on a level change, and when the character learns Dosis.
This automatic progression replaces the missing Sage trainer for now.
The server removes over-level Sage spells from the original kit.
It replaces over-level action-bar bindings with an eligible rank when that action has one.
It clears bindings for actions that the character cannot learn yet.
It preserves deliberate downranking and all stock action-bar bindings.

`ranks.tsv` defines the rank chains and learn levels.
The SQL generator also produces the server rank table, the Dosis passive dependency, and the C++ level table.
The original spell IDs remain the highest ranks. New lower ranks use IDs 40017–40072.
New ranks reuse the existing icons for their action family.

## Representative values

These ranges include the stock growth through the indicated level.
They exclude gear bonuses, critical hits, talents, resistances, and overhealing.
Fractional rolls round through the engine, so endpoints can differ by one point.

| Level | Action | Base result | Mana | Cast time |
|---|---|---|---|---|
| 15 | Dosis rank 3 | About 55–63 damage | 60 | 2.5 seconds |
| 15 | Diagnosis rank 3 | 143–165 health | 75 | 2.5 seconds |
| 60 | Dosis rank 8 | About 385–429 damage | 280 | 2.5 seconds |
| 60 | Diagnosis rank 10 | About 829–975 health | 380 | 1.5 seconds |
| 60 | Prognosis rank 4 | 939–991 health per party member | 1030 | 3 seconds |
| 60 | Eukrasian Dosis rank 8 | 852 damage over 18 seconds | 470 | Instant, after Eukrasia |
| 60 | Eukrasian Diagnosis rank 10 | 942 damage absorbed | 500 | Instant, after Eukrasia |
| 60 | Eukrasian Prognosis rank 4 | 627 damage absorbed per party member | 1185 | Instant, after Eukrasia |
| 60 | Phlegma rank 9 | About 508–536 damage | 350 | Instant |
| 60 | Druochole rank 7 | About 829–975 health | One Addersgall charge | Instant |

Prognosis starts at level 30, like Prayer of Healing.
Low-level characters retain Diagnosis for single-target healing.
Eukrasia now starts the normal 1.5-second global cooldown.
Eukrasian actions also use the normal global cooldown.

## Gear and resource scaling

Dosis, Diagnosis, Prognosis, and Eukrasian Dosis retain each stock rank's coefficient.
This also preserves the stock penalties for spells learned before level 20.
Phlegma uses the matching Mind Blast coefficient, capped at 0.429 for its instant cast.
Single-target shields gain 10% of healing power, like stock Power Word: Shield.
Party shields gain 5% of healing power per target.
The shield script applies the normal level penalty to that bonus.

Kardia heals for 20% of actual Sage damage, including periodic damage after mitigation.
Its triggered heal gains no extra healing-power bonus.
A tiny low-rank damage spell therefore cannot produce a full endgame heal.
The old fixed heal generated 1020 health from one six-tick Eukrasian Dosis.
The new top-rank version generates about 170 health before damage bonuses and mitigation.

Addersgall still gains one charge each 20 seconds and stops at three.
Druochole and Kerachole restore 3% of base mana per charge.
Intellect gear does not increase that refund.
Druochole gains no healing-power bonus because it already provides an instant, mana-free heal.
Kerachole retains 10% damage reduction for 15 seconds and its 30-second cooldown.

## Checks

Run the data and client checks:

```sh
UV_CACHE_DIR=/tmp/sage-uv uv run --no-project sage/generate.py --check
UV_CACHE_DIR=/tmp/sage-uv uv run --no-project sage/test_balance.py
```

The tests compare stock action values directly with their source DBC rows.
They also cover rank chains, level-15 availability, original IDs, icons, names, and spellbook mappings.
The full `mangosd` build checks the server progression and combat scripts.
Live checks must cover login rank migration, a level change, damage, Kardia healing, and the mana refund.
