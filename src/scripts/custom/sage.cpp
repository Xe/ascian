// Local Ascian Sage kit. Spell data and identifiers live in sage/spells.tsv.
#include "scriptPCH.h"
#include "SpellAuras.h"
#include "Map.h"

namespace
{
enum SageSpells
{
    EUKRASIAN_DOSIS = 40001,
    EUKRASIA = 40004,
    KARDIA = 40007,
    ADDERSGALL_CHARGE = 40014,
    KARDIA_LINK = 40015,
    KARDIA_HEAL = 40016,
};

// Keep the link on the unit, rather than in a global map that outlives players.
struct KardiaLinkScript : AuraScript
{
    ObjectGuid ally;
};

KardiaLinkScript* GetKardiaLink(Unit* caster)
{
    SpellAuraHolder* holder = caster->GetSpellAuraHolder(KARDIA_LINK);
    return holder ? static_cast<KardiaLinkScript*>(holder->GetAuraScript()) : nullptr;
}

void HealKardia(Unit* caster)
{
    if (!caster)
        return;
    KardiaLinkScript* link = GetKardiaLink(caster);
    if (!link)
        return;
    Unit* ally = caster->GetMap()->GetUnit(link->ally);
    if (ally && ally->IsAlive() && caster->IsWithinDistInMap(ally, 40.0f) &&
        ally->GetSpellAuraHolder(KARDIA, caster->GetObjectGuid()))
        caster->CastSpell(ally, KARDIA_HEAL, true);
}

struct SageDamageScript : SpellScript
{
    void OnAfterHit(Spell* spell) const override
    {
        if (spell->GetTotalDamage() > 0)
            HealKardia(spell->m_casterUnit);
    }
};

struct EukrasiaScript : SpellScript
{
    SpellCastResult OnCheckCast(Spell* spell, bool) const override
    {
        return spell->m_casterUnit && spell->m_casterUnit->HasAura(EUKRASIA) ?
            SPELL_CAST_OK : SPELL_FAILED_CASTER_AURASTATE;
    }

    void OnCast(Spell* spell) const override
    {
        spell->m_casterUnit->RemoveAurasDueToSpell(EUKRASIA);
    }
};

struct EukrasianDosisAuraScript : AuraScript
{
    void OnPeriodicTickEnd(Aura* aura) override
    {
        if (aura->GetTarget()->IsAlive())
            HealKardia(aura->GetCaster());
    }
};

struct KardiaScript : SpellScript
{
    void OnAfterHit(Spell* spell) const override
    {
        Unit* caster = spell->m_casterUnit;
        Unit* ally = spell->GetUnitTarget();
        if (!caster || !ally || !ally->GetSpellAuraHolder(KARDIA, caster->GetObjectGuid()))
            return;
        if (!GetKardiaLink(caster))
            caster->CastSpell(caster, KARDIA_LINK, true);
        KardiaLinkScript* link = GetKardiaLink(caster);
        if (!link)
            return;
        if (link->ally != ally->GetObjectGuid())
            if (Unit* previous = caster->GetMap()->GetUnit(link->ally))
                previous->RemoveAurasByCasterSpell(KARDIA, caster->GetObjectGuid());
        link->ally = ally->GetObjectGuid();
    }
};

struct KardiaAuraScript : AuraScript
{
    void OnAfterApply(Aura* aura, bool apply) override
    {
        if (apply)
            return;
        if (Unit* caster = aura->GetCaster())
            if (KardiaLinkScript* link = GetKardiaLink(caster))
                if (link->ally == aura->GetTarget()->GetObjectGuid())
                    link->ally.Clear();
    }
};

struct AddersgallTimerScript : AuraScript
{
    void OnBeforeApply(Aura* aura, bool apply) override
    {
        if (apply)
            aura->SetPeriodicTimer(20 * IN_MILLISECONDS);
    }

    void OnAfterApply(Aura* aura, bool apply) override
    {
        if (!apply)
            aura->GetTarget()->RemoveAurasDueToSpell(ADDERSGALL_CHARGE);
    }

    void OnPeriodicDummy(Aura* aura) override
    {
        Unit* caster = aura->GetTarget();
        if (!caster->IsAlive())
            return;
        SpellAuraHolder* charges = caster->GetSpellAuraHolder(ADDERSGALL_CHARGE);
        if (!charges)
            caster->CastSpell(caster, ADDERSGALL_CHARGE, true);
        else if (charges->GetStackAmount() < 3)
            charges->ModStackAmount(1);
    }
};

struct AddersgallSpellScript : SpellScript
{
    SpellCastResult OnCheckCast(Spell* spell, bool) const override
    {
        SpellAuraHolder* charges = spell->m_casterUnit ?
            spell->m_casterUnit->GetSpellAuraHolder(ADDERSGALL_CHARGE) : nullptr;
        return charges && charges->GetStackAmount() > 0 ?
            SPELL_CAST_OK : SPELL_FAILED_CASTER_AURASTATE;
    }

    void OnCast(Spell* spell) const override
    {
        Unit* caster = spell->m_casterUnit;
        caster->RemoveAuraHolderFromStack(ADDERSGALL_CHARGE);
        caster->EnergizeBySpell(caster, spell->m_spellInfo->Id,
                               caster->GetMaxPower(POWER_MANA) * 7 / 100, POWER_MANA);
    }
};

template<class T> SpellScript* SpellFactory(SpellEntry const*) { return new T; }
template<class T> AuraScript* AuraFactory(SpellEntry const*) { return new T; }

void RegisterSage(char const* name, SpellScript* (*spell)(SpellEntry const*),
                  AuraScript* (*aura)(SpellEntry const*) = nullptr)
{
    Script* script = new Script;
    script->Name = name;
    script->GetSpellScript = spell;
    script->GetAuraScript = aura;
    script->RegisterSelf();
}
}

void AddSC_sage()
{
    RegisterSage("spell_sage_damage", &SpellFactory<SageDamageScript>);
    RegisterSage("spell_sage_eukrasia", &SpellFactory<EukrasiaScript>);
    RegisterSage("spell_sage_eukrasian_dosis", &SpellFactory<EukrasiaScript>, &AuraFactory<EukrasianDosisAuraScript>);
    RegisterSage("spell_sage_kardia", &SpellFactory<KardiaScript>, &AuraFactory<KardiaAuraScript>);
    RegisterSage("spell_sage_kardia_link", nullptr, &AuraFactory<KardiaLinkScript>);
    RegisterSage("spell_sage_addersgall_timer", nullptr, &AuraFactory<AddersgallTimerScript>);
    RegisterSage("spell_sage_addersgall", &SpellFactory<AddersgallSpellScript>);
}
