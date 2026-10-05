#!/usr/bin/env python3
"""Verify Sage rank coverage and numeric agreement with stock 5875 client rows."""
import csv
import os
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from client_patch import Dbc, generate

ROOT = Path(__file__).resolve().parent.parent
BASE = Path(os.environ.get('SAGE_BASE_DBC', '/home/xe/code/ffxi2adt/out/server/register-xiv/dbc'))


class SageBalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name)
        generate(BASE, cls.out)
        cls.spells = Dbc(cls.out/'Spell.dbc', 173)
        cls.stock = Dbc(BASE/'Spell.dbc', 173)
        cls.generated = {cls.spells.get(r, 0): r for r in cls.spells.rows}
        cls.templates = {cls.stock.get(r, 0): r for r in cls.stock.rows}
        with (ROOT/'sage/spells.tsv').open() as source:
            cls.contract = {int(r['id']): r for r in csv.DictReader(source, delimiter='\t')}
        with (ROOT/'sage/ranks.tsv').open() as source:
            cls.ranks = list(csv.DictReader(source, delimiter='\t'))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_rank_chains_are_complete_and_levels_increase(self):
        families = defaultdict(list)
        for r in self.ranks:
            self.assertIn(int(r['id']), self.contract)
            families[r['family']].append(r)
        for family, ranks in families.items():
            if int(ranks[0]['rank']) == 0:
                continue
            self.assertEqual([int(r['rank']) for r in ranks], list(range(1, len(ranks)+1)), family)
            self.assertEqual([int(r['prev']) for r in ranks], [0]+[int(r['id']) for r in ranks[:-1]], family)
            levels = [int(r['level']) for r in ranks]
            self.assertEqual(sorted(set(levels)), levels, family)
            self.assertTrue(all(r['first'] == ranks[0]['id'] for r in ranks), family)

    def test_standard_actions_match_stock_damage_cost_and_cast_time(self):
        # These columns govern mana, cast time, level growth, and the damage/heal roll.
        columns = [18,27,28,29,32,33,34,35,64,67,70,73,76,156]
        for r in self.ranks:
            if r['family'] not in ('Dosis','Diagnosis','Prognosis','Eukrasian Dosis','Egeiro'):
                continue
            entry = self.contract[int(r['id'])]
            actual = self.generated[int(r['id'])]
            template = self.templates[int(entry['base'])]
            for col in columns:
                self.assertEqual(actual[col*4:col*4+4], template[col*4:col*4+4], (entry['name'],r['rank'],col))

    def test_low_level_characters_do_not_get_endgame_ranks(self):
        expected = {'Dosis':3, 'Diagnosis':3, 'Prognosis':0, 'Eukrasian Dosis':2,
                    'Eukrasian Diagnosis':2, 'Phlegma':1, 'Druochole':0}
        for family, count in expected.items():
            eligible = [r for r in self.ranks if r['family']==family and int(r['level'])<=15]
            self.assertEqual(len(eligible),count,family)
        self.assertEqual(self.spells.get(self.generated[40019],32),60)
        self.assertEqual(self.spells.get(self.generated[40026],32),75)

    def test_all_playable_ranks_have_names_and_sage_book_entries(self):
        abilities = Dbc(self.out/'SkillLineAbility.dbc',15)
        mappings = {abilities.get(r,2):r for r in abilities.rows if 40000<=abilities.get(r,2)<=40099}
        self.assertEqual(len(mappings),len(self.ranks))
        for r in self.ranks:
            spell_id=int(r['id']);entry=self.generated[spell_id]
            self.assertEqual(abilities.get(mappings[spell_id],1),800)
            offset=self.spells.get(entry,129)
            text=self.spells.strings[offset:].split(b'\0')[0].decode()
            self.assertEqual(text, 'Rank '+r['rank'] if int(r['rank']) else '')

    def test_stock_rows_are_unchanged(self):
        for spell_id,row in self.templates.items():
            if not 40000 <= spell_id <= 40099:
                self.assertEqual(self.generated[spell_id],row,spell_id)

    def test_sage_tab_routes_every_race_and_class(self):
        lines = Dbc(self.out/'SkillLine.dbc',22)
        line = next(r for r in lines.rows if lines.get(r,0)==800)
        self.assertEqual(lines.get(line,21),40000)
        routing = Dbc(self.out/'SkillRaceClassInfo.dbc',8)
        rows = [r for r in routing.rows if routing.get(r,1)==800]
        self.assertEqual(len(rows),1)
        route = rows[0]
        self.assertEqual(routing.get(route,2),0)
        self.assertEqual(routing.get(route,3),0)
        self.assertEqual(routing.get(route,4) & 0x80,0)
        abilities = Dbc(self.out/'SkillLineAbility.dbc',15)
        for row in abilities.rows:
            if abilities.get(row,1)==800:
                self.assertEqual(abilities.get(row,3),0)
                self.assertEqual(abilities.get(row,4),0)

    def test_original_ids_and_icons_are_preserved(self):
        for spell_id,name in [(40000,'Dosis'),(40002,'Diagnosis'),(40003,'Prognosis'),(40008,'Phlegma')]:
            self.assertEqual(self.contract[spell_id]['name'],name)
        for r in self.ranks:
            if int(r['rank']):
                top=next(x for x in reversed(self.ranks) if x['family']==r['family'])
                self.assertEqual(self.spells.get(self.generated[int(r['id'])],117),int(top['id']))


if __name__ == '__main__':
    unittest.main()
