# Sage kit

The shared contract is `spells.tsv`. IDs 40000–40013 are playable spells.
IDs 40014–40016 are internal resource, link, and heal spells.
The current base class is Priest. A dedicated Sage class is a later phase.

## Server

Generate the repeatable SQL:

```sh
UV_CACHE_DIR=/tmp/sage-uv uv run --no-project sage/generate.py
```

Apply `sql/ascian/010-sage-spells.sql` to the realm's `mangos` database.
Build the fork with `sage/build.sh`. Restart it with `sage/restart.sh`.
The restart command stops if a client probe runs.
The Compose override uses the existing realm config and data mounts.
It adds the compiled binary and its runtime libraries.

Addersgall uses a timer aura and a separate charge aura.
The timer, charge and Kardia link auras have no spell visual.
The visual of Inner Focus, their template, loops a sound while the aura is on.
The charge aura disappears at zero. The timer continues and restores one charge each 20 seconds.
Kardia stores its ally GUID in an aura on the caster.
Direct damage heals that ally after a successful damaging hit.
Eukrasian Dosis heals that ally after each periodic tick while the target remains alive.

## Client

The client needs `Spell.dbc` rows and `SkillLineAbility.dbc` mappings.
The Sage tab also needs `SkillLine.dbc` and `SkillRaceClassInfo.dbc` rows.
The current mappings put the playable spells in a separate Sage tab.
Skill line 800 and a copy of the Priest Holy routing row define this tab.
Each spell names a `SpellIcon.dbc` row with its own id (`spellIconId`).
The `ffxi2adt` tool makes those rows and the icon files from the FFXIV install.
It packs them in `patch-4.MPQ` (`ffxi2adt spells --xiv`).

Generate the client tables and pack the archive:

```sh
UV_CACHE_DIR=/tmp/sage-uv uv run --no-project sage/client_patch.py /home/xe/code/ffxi2adt/out/server/register-xiv/dbc build/client-dbc
CARGO_TARGET_DIR="$PWD/build/sage-mpq" cargo build --offline --manifest-path sage/mpq/Cargo.toml
build/sage-mpq/debug/sage-mpq pack build/client-dbc build/patch-5.MPQ
```

Copy `build/patch-5.MPQ` to the client's `Data` directory.
Close and reopen the client to load the patch.
The separate archive preserves `patch-4.MPQ`, which contains the maps.

`patch-4.MPQ` can carry the same tables: `ffxi2adt spells --skill-tables build/client-dbc`
takes the three skill tables from here and makes `Spell.dbc` from the same contract.
The 17 spell rows of both generators are equal on every field and text.
Use one archive or both; `patch-5.MPQ` wins when both hold a table.

## Field mapping

`client_patch.py` defines the zero-based 5875 DBC column for each supported server field.
`Spell.dbc` has 173 fields of four bytes each.
The generator copies a stock row, then applies the contract changes.
It clears the rank text and replaces all eight localized names and descriptions.

| Server column | DBC column or field |
|---|---|
| `entry` | ID, column 0 |
| `school` | School, column 1 |
| `category` | Category, column 2 |
| `attributes`, `attributesEx`, `attributesEx2`, `attributesEx3`, `attributesEx4` | Attributes, columns 6–10 |
| `stances`, `stancesNot` | Stances, columns 11–12 |
| `castingTimeIndex` | CastingTimeIndex, column 18 |
| `recoveryTime`, `categoryRecoveryTime` | RecoveryTime, columns 19–20 |
| `procFlags`, `procCharges` | ProcFlags, column 24, and ProcCharges, column 26 |
| `maxLevel`, `baseLevel`, `spellLevel` | Level fields, columns 27–29 |
| `durationIndex` | DurationIndex, column 30 |
| `powerType`, `manaCost` | PowerType, column 31, and ManaCost, column 32 |
| `rangeIndex` | RangeIndex, column 36 |
| `stackAmount` | StackAmount, column 39 |
| `effect1`–`effect3` | Effect array, columns 61–63 |
| `effectDieSides1`–`effectDieSides3` | EffectDieSides array, columns 64–66 |
| `effectRealPointsPerLevel1`–`effectRealPointsPerLevel3` | Float array, columns 73–75 |
| `effectBasePoints1`–`effectBasePoints3` | Signed base points, columns 76–78 |
| `effectMechanic1`–`effectMechanic3` | EffectMechanic array, columns 79–81 |
| `effectImplicitTargetA1`–`effectImplicitTargetA3` | Target A array, columns 82–84 |
| `effectImplicitTargetB1`–`effectImplicitTargetB3` | Target B array, columns 85–87 |
| `effectRadiusIndex1`–`effectRadiusIndex3` | Radius array, columns 88–90 |
| `effectApplyAuraName1`–`effectApplyAuraName3` | Aura array, columns 91–93 |
| `effectAmplitude1`–`effectAmplitude3` | Period array, columns 94–96 |
| `effectMiscValue1`–`effectMiscValue3` | MiscValue array, columns 106–108 |
| `effectTriggerSpell1`–`effectTriggerSpell3` | TriggerSpell array, columns 109–111 |
| `name`, `nameSubtext`, `description`, `auraDescription` | String offsets at columns 120, 129, 138, 147 |
| `spellVisual1`, `spellVisual2` | SpellVisual, columns 115–116 |
| `spellIconId` | SpellIconID, column 117 |
| `startRecoveryCategory`, `startRecoveryTime` | Global cooldown fields, columns 157–158 |
| `spellFamilyName`, `spellFamilyFlags` | Family, column 160, and 64-bit flags, columns 161–162 |
| `effectBonusCoefficient1` | Server field only. No 5875 DBC equivalent. |
| `build`, `script_name` | Server fields only. No DBC equivalent. |

## Verification status

- The compatible Docker image and the complete `mangosd` target compiled successfully.
- The spell SQL applied twice without duplicate rows.
- The live world server loaded all 17 spell rows and reached healthy status.
- The client patch generated all 17 names and 14 Sage spellbook mappings.
- The MPQ packer read all four tables back and compared their bytes with the generated tables.
- The installed archive matches the generated archive.

Combat behavior, the rendered spellbook, and the trainer window still need live checks.
Trainer ID coordination remains pending. No trainer migration exists yet.
