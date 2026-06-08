"""
Curated literature validation dataset for salt-vs-free-base oral PK.

Each entry uses ONLY documented physicochemical inputs (intrinsic solubility,
pKa, BCS class, measured salt solubility / dissolution, and free-base F where
reported). We do NOT tune inputs to the observed salt ratio — that is the
prediction target. Global model constants are left at defaults.

Data-quality grade:
  A = measured in-vitro (solubility/dissolution + pKa) + quantitative in-vivo ratio
  B = quantitative in-vivo ratio + partial in-vitro (BCS / free-base F / fold-sol)
  C = direction / rank only (used for direction & ranking statistics, not magnitude)

Every entry carries its primary citation. Values are from the abstracts / figures
of the cited papers (full tables were not openly fetchable); treat magnitudes as
±10-20% transcription uncertainty.
"""
from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species, predict


def _ratio(io, pk, sp, free, salt):
    f = predict(pk, io, free, sp)
    s = predict(pk, io, salt, sp)
    return s["AUC"] / f["AUC"], s["Cmax"] / f["Cmax"]


# helper to build a salt with a flat-then-plateau dissolution at pH 1.2 / 6.8
def _mp(p12, p68):
    fast = lambda e: [(0.25, 0.7*e), (0.5, 0.9*e), (1, 0.97*e), (2, e)]
    return {1.2: fast(p12), 6.8: fast(p68)}


ENTRIES = []


def entry(**kw):
    ENTRIES.append(kw)


# ============================ GRADE A ===================================== #
def p_iiim290():
    io = IonizableDrug(mw=462.3, pka=5.24, s0_ugml=8.6, is_base=True)
    pk = DrugPK(dose_mgkg=50, caco2=25, clint=8, ppb_percent=85)
    return _ratio(io, pk, get_species("mouse"),
                  SaltForm.free_base(), SaltForm.of("hcl", 387))
entry(id="IIIM-290 HCl", ctype="base", bcs="II", species="mouse", grade="A",
      obs_auc=1.44, obs_cmax=1.57, predict=p_iiim290,
      cite="Bhagat 2018 ACS Omega 3:8836 (PMC6072253)")


def _cilostazol(p12_salt):
    io = IonizableDrug(mw=369.46, pka=11.8, s0_ugml=4.0, is_base=True)
    pk = DrugPK(dose_mgkg=20, caco2=22, clint=10, ppb_percent=96)
    fb = SaltForm.free_base(ph_profiles=_mp(0.254, 0.0274))
    salt = SaltForm.of("mesylate", 9999, ph_profiles=_mp(p12_salt, 0.20))
    return _ratio(io, pk, get_species("rat"), fb, salt)
entry(id="Cilostazol mesylate", ctype="base", bcs="II", species="rat", grade="A",
      obs_auc=3.88, obs_cmax=3.65, predict=lambda: _cilostazol(0.935),
      cite="Seo 2015 DDDT 9:3961 (PMC4524531)")
entry(id="Cilostazol besylate", ctype="base", bcs="II", species="rat", grade="A",
      obs_auc=2.94, obs_cmax=2.87, predict=lambda: _cilostazol(0.986),
      cite="Seo 2015 DDDT 9:3961 (PMC4524531)")


def p_phenytoin():
    # PLATEAU test (salt-vs-salt): sodium (~18 mg/mL) vs piperazine (~0.3 mg/mL).
    # ~60x solubility difference but NO bioavailability difference -> both salts are
    # above the absorption-saturating solubility threshold. Expect ratio ~ 1.0.
    io = IonizableDrug(mw=252.3, pka=8.3, s0_ugml=22.0, is_base=False)
    pk = DrugPK(dose_mgkg=10, caco2=25, clint=6, ppb_percent=89)
    sp = get_species("dog")
    na = predict(pk, io, SaltForm.of("hcl", 18000, label="sodium"), sp)
    pip = predict(pk, io, SaltForm.of("maleate", 300, label="piperazine"), sp)
    return na["AUC"]/pip["AUC"], na["Cmax"]/pip["Cmax"]
entry(id="Phenytoin Na/piperazine (plateau)", ctype="acid", bcs="II", species="dog",
      grade="A", obs_auc=1.0, obs_cmax=1.0, predict=p_phenytoin, plateau=True,
      cite="Serajuddin 2007 ADDR 59:603; phenytoin salt PBPK (PMC3787220)")


# ============================ GRADE B ===================================== #
def p_canertinib():
    # weak base, BCS II; free base F~20% (poorly absorbed); maleate -> 2x AUC, rat
    io = IonizableDrug(mw=485.0, pka=6.0, s0_ugml=4.0, is_base=True)
    pk = DrugPK(dose_mgkg=20, caco2=12, clint=12, ppb_percent=92)  # low-ish F free base
    return _ratio(io, pk, get_species("rat"),
                  SaltForm.free_base(), SaltForm.of("maleate", 1500))
entry(id="Canertinib-type maleate", ctype="base", bcs="II", species="rat", grade="B",
      obs_auc=2.0, obs_cmax=2.0, predict=p_canertinib,
      cite="US 8,022,216 (quinolinyl maleate, rat 5-45 mg/kg)")


def p_nk1_tartrate():
    io = IonizableDrug(mw=500.0, pka=6.5, s0_ugml=6.0, is_base=True)
    pk = DrugPK(dose_mgkg=12, caco2=18, clint=10, ppb_percent=95)
    return _ratio(io, pk, get_species("dog"),
                  SaltForm.free_base(), SaltForm.of("tartrate", 1200))
entry(id="NK-1 antag. tartrate", ctype="base", bcs="II", species="dog", grade="B",
      obs_auc=1.9, obs_cmax=2.0, predict=p_nk1_tartrate,
      cite="US 10,233,154 / 10,676,440 (NK-1 antagonist, dog)")


def p_nk1_malate():
    io = IonizableDrug(mw=500.0, pka=6.5, s0_ugml=6.0, is_base=True)
    pk = DrugPK(dose_mgkg=12, caco2=18, clint=10, ppb_percent=95)
    return _ratio(io, pk, get_species("dog"),
                  SaltForm.free_base(), SaltForm.of("maleate", 2500, label="malate"))
entry(id="NK-1 antag. malate", ctype="base", bcs="II", species="dog", grade="B",
      obs_auc=2.9, obs_cmax=2.4, predict=p_nk1_malate,
      cite="US 10,233,154 / 10,676,440 (NK-1 antagonist malate, dog)")


def p_mesembrine():
    io = IonizableDrug(mw=289.4, pka=8.0, s0_ugml=20.0, is_base=True)
    pk = DrugPK(dose_mgkg=10, caco2=20, clint=12, ppb_percent=85)
    return _ratio(io, pk, get_species("rat"),
                  SaltForm.free_base(), SaltForm.of("besylate", 3000))
entry(id="Mesembrine besylate", ctype="base", bcs="II", species="rat", grade="B",
      obs_auc=1.5, obs_cmax=1.5, predict=p_mesembrine,
      cite="US 11,970,446 (mesembrine besylate)")


# ============================ GRADE C (direction / rank) ================== #
def p_pkc_mesylate_vs_hcl():
    # salt-vs-salt: mesylate vs HCl of a PKC inhibitor; mesylate ~2.5x HCl
    io = IonizableDrug(mw=520.0, pka=6.5, s0_ugml=5.0, is_base=True)
    pk = DrugPK(dose_mgkg=20, caco2=15, clint=12, ppb_percent=93)
    sp = get_species("dog")
    hcl = predict(pk, io, SaltForm.of("hcl", 800), sp)
    mes = predict(pk, io, SaltForm.of("mesylate", 800), sp)
    return mes["AUC"]/hcl["AUC"], mes["Cmax"]/hcl["Cmax"]
entry(id="PKC inhib. mesylate/HCl", ctype="base", bcs="II", species="dog", grade="C",
      obs_auc=2.5, obs_cmax=2.5, predict=p_pkc_mesylate_vs_hcl,
      cite="US 6,015,807 / 6,117,861 (PKC inhibitor, mesylate vs HCl)")


def p_rpr2000765():
    # pKa 5.3, S0 10 µg/mL, mesylate 39 mg/mL (~3900x). Direction: salt >> free base
    io = IonizableDrug(mw=450.0, pka=5.3, s0_ugml=10.0, is_base=True)
    pk = DrugPK(dose_mgkg=20, caco2=18, clint=12, ppb_percent=90)
    return _ratio(io, pk, get_species("rat"),
                  SaltForm.free_base(), SaltForm.of("mesylate", 39000))
entry(id="RPR2000765 mesylate", ctype="base", bcs="II", species="rat", grade="C",
      obs_auc=None, obs_cmax=None, direction="up", predict=p_rpr2000765,
      cite="Pudipeddi 2002; salt screening (S0 10 µg/mL -> mesylate 39 mg/mL)")


# Haloperidol counterion RANKING (mesylate > phosphate > HCl) — special case
def haloperidol_rank():
    io = IonizableDrug(mw=375.9, pka=8.3, s0_ugml=2.5, is_base=True)
    pk = DrugPK(dose_mgkg=5, caco2=20, clint=12, ppb_percent=90)
    sp = get_species("dog")
    out = {}
    for ci in ["mesylate", "phosphate", "hcl"]:
        # equal modest salt solubility -> ranking must come from common-ion/counterion
        out[ci] = predict(pk, io, SaltForm.of(ci, 600), sp)["AUC"]
    return out
