-- Dosis owns the Addersgall passive. Player::AddSpell applies passive
-- dependencies during login and learning; RemoveSpell removes them on unlearn.
DELETE FROM spell_learn_spell WHERE entry = 40000 AND SpellID = 40011;
INSERT INTO spell_learn_spell (entry, SpellID, Active, build_min, build_max)
VALUES (40000, 40011, 1, 5875, 5875);
