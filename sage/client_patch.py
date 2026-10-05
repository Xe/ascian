#!/usr/bin/env python3
"""Copy stock 5875 client rows and apply sage/spells.tsv changes."""
import argparse
import csv
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Zero-based Spell.dbc column numbers, client build 5875 (173 fields).
FIELDS = dict(school=1, category=2, castUI=3, dispel=4, mechanic=5,
              attributes=6, attributesEx=7, attributesEx2=8, attributesEx3=9,
              attributesEx4=10, stances=11, stancesNot=12, targets=13,
              targetCreatureType=14, requiresSpellFocus=15, casterAuraState=16,
              targetAuraState=17, castingTimeIndex=18, recoveryTime=19,
              categoryRecoveryTime=20, interruptFlags=21, auraInterruptFlags=22,
              channelInterruptFlags=23, procFlags=24, procChance=25, procCharges=26,
              maxLevel=27, baseLevel=28, spellLevel=29, durationIndex=30,
              powerType=31, manaCost=32, manCostPerLevel=33, manaPerSecond=34,
              manaPerSecondPerLevel=35, rangeIndex=36, speed=37, modelNextSpell=38,
              stackAmount=39, manaCostPercentage=156, startRecoveryCategory=157,
              startRecoveryTime=158, maxTargetLevel=159, spellFamilyName=160,
              maxAffectedTargets=163, dmgClass=164, preventionType=165,
              spellIconId=117)
ARRAYS = dict(effect=61, effectDieSides=64, effectBaseDice=67,
              effectDicePerLevel=70, effectRealPointsPerLevel=73,
              effectBasePoints=76, effectMechanic=79, effectImplicitTargetA=82,
              effectImplicitTargetB=85, effectRadiusIndex=88,
              effectApplyAuraName=91, effectAmplitude=94, effectMultipleValue=97,
              effectChainTarget=100, effectItemType=103, effectMiscValue=106,
              effectTriggerSpell=109, effectPointsPerComboPoint=112,
              dmgMultiplier=167)
FLOATS = {"speed", "effectDicePerLevel", "effectRealPointsPerLevel",
          "effectMultipleValue", "effectPointsPerComboPoint", "dmgMultiplier"}
SERVER_ONLY = {"customFlags", "minTargetLevel", "effectBonusCoefficient1",
               "effectBonusCoefficient2", "effectBonusCoefficient3"}
for field, start in ARRAYS.items():
    for i in range(3):
        FIELDS[f"{field}{i+1}"] = start+i


class Dbc:
    def __init__(self, path, fields):
        data = path.read_bytes()
        magic, count, self.fields, size, strings = struct.unpack_from('<4s4I', data)
        if magic != b'WDBC' or self.fields != fields or size != 4*fields:
            raise ValueError(f"unexpected 5875 DBC layout: {path}")
        self.rows = [bytearray(data[20+i*size:20+(i+1)*size]) for i in range(count)]
        self.strings = bytearray(data[20+count*size:20+count*size+strings])
        if len(self.strings) != strings:
            raise ValueError(f"truncated DBC: {path}")

    @staticmethod
    def get(row, col):
        return struct.unpack_from('<I', row, col*4)[0]

    @staticmethod
    def put(row, col, value, floating=False):
        struct.pack_into('<f' if floating else '<I', row, col*4,
                         float(value) if floating else int(value) & 0xffffffff)

    def text(self, row, col, value):
        offset = len(self.strings) if value else 0
        if value:
            self.strings.extend(value.encode('utf-8') + b'\0')
        for locale in range(8):
            self.put(row, col+locale, offset)

    def write(self, path):
        self.rows.sort(key=lambda row: self.get(row, 0))
        path.write_bytes(struct.pack('<4s4I', b'WDBC', len(self.rows), self.fields,
                                     self.fields*4, len(self.strings)) +
                         b''.join(self.rows) + self.strings)


def generate(base, out):
    spells = Dbc(base/'Spell.dbc', 173)
    abilities = Dbc(base/'SkillLineAbility.dbc', 15)
    lines = Dbc(base/'SkillLine.dbc', 22)
    routing = Dbc(base/'SkillRaceClassInfo.dbc', 8)
    sage_line = 800
    # Clone Holy's tab and race/class routing, then give Sage its own name.
    lines.rows = [r for r in lines.rows if lines.get(r, 0) != sage_line]
    routing.rows = [r for r in routing.rows if routing.get(r, 1) != sage_line]
    line = next(r for r in lines.rows if lines.get(r, 0) == 56).copy()
    lines.put(line, 0, sage_line)
    lines.text(line, 3, 'Sage')
    lines.text(line, 12, 'Sage damage, healing, shields, and resources.')
    lines.rows.append(line)
    route = next(r for r in routing.rows if routing.get(r, 1) == 56
                 and routing.get(r, 3) == 16).copy()
    routing.put(route, 0, 60000)
    routing.put(route, 1, sage_line)
    routing.rows.append(route)
    templates = {spells.get(row, 0): row for row in spells.rows}
    # Regeneration clears only this project's rows.
    spells.rows = [row for row in spells.rows if not 40000 <= spells.get(row, 0) <= 40099]
    abilities.rows = [row for row in abilities.rows if not 40000 <= abilities.get(row, 2) <= 40099]
    with (ROOT/'sage/spells.tsv').open(newline='') as source:
        for entry in csv.DictReader(source, delimiter='\t'):
            spell_id, base_id = int(entry['id']), int(entry['base'])
            row = templates[base_id].copy()
            spells.put(row, 0, spell_id)
            for change in entry['changes'].split(';'):
                field, value = change.split('=', 1)
                if field in SERVER_ONLY:
                    continue
                if field == 'spellFamilyFlags':
                    spells.put(row, 161, int(value) & 0xffffffff)
                    spells.put(row, 162, int(value) >> 32)
                    continue
                if field not in FIELDS:
                    raise ValueError(f"unmapped server field: {field}")
                spells.put(row, FIELDS[field], value, field.rstrip('123') in FLOATS)
            spells.text(row, 120, entry['name'])
            spells.text(row, 129, '')
            spells.text(row, 138, entry['note'])
            spells.text(row, 147, '')
            if spell_id <= 40013:
                assert spells.get(row, 6) & 0xa0 == 0 and spells.get(row, 3) == 0, entry['name']
                # Copy Smite's ability and move it into the Sage skill line.
                template = next(a for a in abilities.rows if abilities.get(a, 2) == 10934)
                ability = template.copy()
                for column, value in {0:60000+spell_id-40000, 1:sage_line, 2:spell_id, 3:0,
                                      4:16, 7:0, 8:0, 9:0}.items():
                    abilities.put(ability, column, value)
                abilities.rows.append(ability)
            spells.rows.append(row)
    out.mkdir(parents=True, exist_ok=True)
    spells.write(out/'Spell.dbc')
    abilities.write(out/'SkillLineAbility.dbc')
    lines.write(out/'SkillLine.dbc')
    routing.write(out/'SkillRaceClassInfo.dbc')
    print('Generated 17 spell rows and a Sage tab with 14 playable spells.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    generate(args.base, args.out)
