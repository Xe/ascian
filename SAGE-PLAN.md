# Sage spells in vmangos-ascian: plan

This plan is for an agent that works in this repository. A second agent works on the
client side in `~/code/ffxi2adt` (worktree `.worktrees/xiv-limsa`) at the same time.
The contract between the two agents is one file, `sage/spells.tsv`. Read "Contract"
before you write code.

## Goal

A character on the local realm can learn and cast the FFXIV Sage kit. Each spell does
on the server what the table below says. The class id (a tenth class) is a later
phase and is not part of this plan.

## Ground rules

- This repository is a local fork. Do not push it. Do not add a GitHub remote. The only
  remote is `upstream` (vmangos/core).
- Work on the branch `ascian`. It starts at `0e3ff01e`, the revision that the local
  realm runs. Do not rebase onto a newer upstream revision: the realm database has
  that revision's schema.
- Commit small. Each commit message says what you verified and how.
- The realm is shared with other sessions. Before a world server restart, run
  `pgrep -af 'probe-|target/debug/benilla'`. If a probe runs, wait.
- Do not log in with another session's account. Ask the owner for an account, or use
  `PROBE7003` (identity file `~/code/ffxi2adt/out/server/.probe-identity-xiv`) when
  the client-side agent does not use it.
- Use `uv` for Python dependencies.
- Database changes go in SQL files under `sql/ascian/`, applied in name order. Each
  file clears its own id range first, so it applies again without harm.

## Facts about this code (measured at `0e3ff01e`)

- Spells are data. The server loads every spell from the database table
  `mangos.spell_template` (`src/game/Spells/SpellMgr.cpp`, near line 3707). A new
  spell is a new row. No DBC file on the server holds spells.
- The largest stock spell id is 33392.
- A spell can have code. `SpellScript` and `AuraScript` are in `src/game/ScriptMgr.h`
  (line 138). `SpellScript` has `OnCheckCast`, `OnCast`, `OnHit`, `OnAfterHit` and
  `OnEffectExecute`. A script registers with `newscript->GetSpellScript = ...`; see
  `src/scripts/battlegrounds/battleground.cpp` line 227 for a short example.
- `src/scripts/custom/` holds project scripts. Put the Sage scripts there.
- 1.12 has no "caster must have aura X" field in a spell row. A rule of that kind
  needs `OnCheckCast`.
- The class list is the enum `Classes` in `src/game/SharedDefines.h` (line 87). Id 10
  is free. 285 places switch on a class. That is the later phase.

## Contract: `sage/spells.tsv`

Both agents read this file. The server agent owns it. The client agent builds
`Spell.dbc` rows for the game client from it, so the client shows the name, the icon
and the cast bar. A spell that exists only on the server cannot go on an action bar.

One line for each spell, fields tab apart:

| Field | Meaning |
|---|---|
| `id` | The spell id. Sage spells take 40000 to 40099. |
| `name` | The FFXIV name. |
| `base` | The id of the stock spell whose row is the template. |
| `changes` | `field=value` pairs, `;` apart, that differ from the template. Field names are the `spell_template` column names. |
| `script` | The script name, or `-`. |
| `note` | One sentence: what the spell does. |

Rules for the contract:

- A row is a copy of the `base` row plus `changes`. Do not write a full row by hand.
  The copy keeps the row valid for both the server and the client.
- Do not change an id after the first commit that holds it. The client agent's patch
  holds the same ids.
- Add a spell: append a line. Tell the owner, so the client agent builds its patch
  again.

## The kit, first slice

One rank each. Numbers are for a level 60 character and are a choice of this project:
FFXIV numbers do not fit 1.12 health pools.

| Spell | Template (stock spell) | Server work |
|---|---|---|
| Dosis | Smite (585, top rank) | Row only: new school (nature), name, numbers. |
| Eukrasian Dosis | Shadow Word: Pain (589, top rank) | Row, plus the Eukrasia rule. |
| Diagnosis | Lesser Heal (2050, top rank) | Row only. |
| Prognosis | Prayer of Healing (596, top rank) | Row only. |
| Eukrasia | Inner Focus (14751) | Row: a self-buff of 10 seconds with no other effect. |
| Eukrasian Diagnosis | Power Word: Shield (17, top rank) | Row, plus the Eukrasia rule. Remove the Weakened Soul effect. |
| Eukrasian Prognosis | Power Word: Shield, group target | Row, plus the Eukrasia rule. |
| Kardia | Vampiric Embrace (15286) | Row and script: see "Kardia". |
| Phlegma | Smite, instant, 30 second cooldown | Row only. |
| Icarus | Intercept (20252) | Row: usable on an ally or an enemy, no stun. |
| Egeiro | Resurrection (2006, top rank) | Row only. |
| Addersgall | (new aura) | Script: see "Addersgall". |
| Druochole | Flash Heal, instant | Row, plus the Addersgall rule. Restores mana. |
| Kerachole | A 10% damage reduction aura, group target | Row, plus the Addersgall rule. |

### The Eukrasia rule

An Eukrasian spell casts only while the caster has the Eukrasia aura, and the cast
removes that aura. One `SpellScript` serves all Eukrasian spells: `OnCheckCast`
returns a failure without the aura, and `OnCast` removes it.

### Kardia

Kardia marks one ally. While the mark is on, each damage spell of the caster heals
that ally. Stock Vampiric Embrace heals the caster's party from shadow damage through
the proc system; read how it does that first (`SpellAuras.cpp`, the dummy aura
handler, and `spell_proc_event`). Kardia needs: the mark aura on the ally, a memory on
the caster of who holds the mark, and a heal on that one ally in `OnAfterHit` of each
Sage damage spell. Start with the heal in the Dosis script; move to the proc system
only when that works.

### Addersgall

Addersgall is a stack of 0 to 3 that gains 1 each 20 seconds. Build it as an aura with
3 stacks at most and a periodic dummy tick that adds a stack. An Addersgall spell
casts only with at least 1 stack and removes 1. One `SpellScript` serves all
Addersgall spells, as for Eukrasia.

## Phases

Each phase ends with a check that a person or an agent can run.

1. **Build and run.** Build `mangosd` from this fork. Run it against the realm's
   database in place of the Docker image's binary. The realm is a Docker Compose
   project in `~/code/ffxi2adt/server/compose.yaml`; the image is
   `ghcr.io/mserajnik/vmangos-server`. Find the least invasive way (a bind mount of
   the built binary is the first thing to try). Do not change the compose file of the
   other repository without a word to the owner. *Check:* the world server log shows
   the fork's revision string, and a login works.
2. **One plain spell.** Write `sage/spells.tsv` with Dosis only, the generator that
   turns the file into `sql/ascian/010-sage-spells.sql`, and apply it. *Check:* a GM
   character runs `.learn 40000`, casts it on a target dummy or a creature, and the
   combat log shows the damage. The client needs the client agent's patch for the
   action bar; `.cast 40000` works without it.
3. **The plain spells.** Diagnosis, Prognosis, Phlegma, Icarus, Egeiro. *Check:* each
   one casts and has its effect.
4. **Eukrasia.** The aura, the rule script, the three Eukrasian spells. *Check:* an
   Eukrasian spell fails without Eukrasia, casts with it, and removes it.
5. **Kardia.** *Check:* with the mark on an ally at half health, a Dosis cast heals
   that ally and no other unit.
6. **Addersgall.** *Check:* the stack grows to 3 and stops; Druochole removes 1 and
   fails at 0.
7. **Trainer.** Give the spells to the NPC "Yuki Mikoshi" (creature entry 99000) as a
   trainer list. Her row comes from `~/code/ffxi2adt` (`scripts/register-xiv.sh`);
   agree the trainer id with the client agent first. *Check:* her window lists the
   spells and teaches one.

## What the client agent does at the same time

- A `Spell.dbc` patcher that reads `sage/spells.tsv` and writes the rows into
  `patch-4.MPQ`, each a copy of the template row with the same changes.
- Icons and spell names for the client.
- The NPC "Yuki Mikoshi" and her trainer flags, once phase 7 has a trainer id.

## Later, not in this plan

- The class itself (id 10): the `Classes` enum, the class masks, `playercreateinfo`,
  level stats, start gear, and the client tables for a class.
- Talents, more ranks, level-by-level numbers.
- The nouliths (the floating weapon) as a visual.

## Risks

- **Schema drift.** A newer upstream revision can change `spell_template`. Stay on
  `0e3ff01e` until the owner says to move.
- **Field meaning.** A `spell_template` column name is not always the DBC field name
  that the client agent expects. Record each column you change in `sage/README.md`
  with the DBC field it maps to.
- **Shared realm.** A crash of the world server stops the other sessions. Test a
  risky script on a second world server first, when you can run one.
