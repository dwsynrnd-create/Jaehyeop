"""
Literature validation dataset for salt-screening PK prediction.

Each record cites a primary source and the in vitro inputs / in vivo observations
used. Where exact in vitro tables were not openly accessible, values are taken
from the abstract / figures and flagged `approx`. Validation focuses on the
quantities that salt screening actually needs:

  * pHmax (exact, analytical)            -> Tier A
  * common-ion suppression (mechanistic) -> Tier A
  * salt-vs-free-base AUC / Cmax ratio   -> Tier B (2-fold acceptance, IVIVE std)
  * BCS-class behaviour & supersaturation-> Tier C (qualitative)

Because the salt/free-base exposure ratio is governed by Fa (disposition cancels),
Tier B is robust to the absolute disposition inputs.
"""

# ---------------------------------------------------------------------------
# Drug-level in vitro inputs (free-base properties shared by all forms)
# ---------------------------------------------------------------------------

IIIM_290 = dict(
    name="IIIM-290 (CDK inhibitor, rohitukine derivative)",
    source=("Bhagat et al., 'Selection of a Water-Soluble Salt Form of a "
            "Preclinical Candidate, IIIM-290', ACS Omega 2018, 3(8):8836-8845. "
            "PMC6072253 / PMID 30087943"),
    mw=450.0,            # approx (rohitukine-derived); affects only common-ion molarity
    pka=5.24,            # derived from reported pHmax: 3.59 = pKa + log10(S0/S_salt)
    s0_ugml=8.6,         # reported free-base aqueous solubility
    is_base=True,
    s_salt_hcl_ugml=387.0,   # 45-fold improvement over free base (reported)
    pHmax_hcl_calc=3.59,     # paper calculated value
    pHmax_hcl_exp=3.0,       # paper experimental value
    # in vivo: BALB/c mouse, 50 mg/kg PO, free base vs HCl
    species="mouse", dose_mgkg=50.0, caco2=15.0, clint=25.0, ppb=85.0,
    obs={"free base": dict(Cmax=656.0, AUC=2570.0),
         "HCl":       dict(Cmax=1030.0, AUC=3710.0)},
)

# Haloperidol — classic model weak base for the COMMON-ION effect on salt
# dissolution (Li, Doherty, Serajuddin and co-workers).
HALOPERIDOL = dict(
    name="Haloperidol (model weak base)",
    source=("Li, Doherty, Serajuddin et al., 'Effect of Chloride ion on "
            "Dissolution of Different Salt Forms of Haloperidol', J. Pharm. Sci.; "
            "and Clin. Pharmacokinet. salt-form reviews."),
    mw=375.9, pka=8.3, s0_ugml=2.5, is_base=True,
    # measured dissolution-rate ranking in 0.01 M HCl (gastric-like, chloride present)
    obs_dissolution_rank=["mesylate", "phosphate", "hcl"],   # mesylate >> phosphate > HCl
)

# Counterion-acidity principle (mechanistic reference).
COUNTERION_ACIDITY = dict(
    source=("Elder, Holm, et al., 'The Selection of a Pharmaceutical Salt — The "
            "Effect of the Acidity of the Counterion on Its Solubility and "
            "Potential Biopharmaceutical Performance', J. Pharm. Sci. 2017, "
            "106(10). PMID 29107790"),
    principle=("A weaker-acid (non-chloride) counterion gives higher solubility "
               "in the chloride-rich stomach because it avoids the common-ion "
               "penalty that suppresses HCl-salt solubility."),
)

# Clofazimine — supersaturation / de-supersaturation in biorelevant media.
CLOFAZIMINE = dict(
    name="Clofazimine (antimycobacterial weak base, BCS II/IV)",
    source=("Bannigan et al., 'Role of Biorelevant Dissolution Media in the "
            "Selection of Optimal Salt Forms of Oral Drugs ... Clofazimine', "
            "ACS Omega 2017, 2(11):8210-8218. DOI 10.1021/acsomega.7b01454"),
    # FaSSIF: salt apparent solubility rises to ~10 µg/mL then falls to ~5 µg/mL
    # over 60 min -> spring-and-parachute de-supersaturation.
    obs_supersat=dict(peak_ugml=10.0, plateau_ugml=5.0, window_min=60),
)

# Cilostazol — BCS II, has BOTH measured dissolution AND in vivo PK ratios
# (best dataset for quantitative accuracy in measured-profile mode).
CILOSTAZOL = dict(
    name="Cilostazol (BCS II, antiplatelet)",
    source=("Seo, Kim et al., 'Improved oral absorption of cilostazol via "
            "sulfonate salt formation with mesylate and besylate', "
            "Drug Des. Devel. Ther. 2015;9:3961-3968. PMC4524531 / PMID 26251575"),
    mw=369.46, pka=11.8, s0_ugml=4.0, is_base=True,    # pKa 11.8 -> ~neutral in GI
    species="rat", dose_mgkg=20.0,
    # REAL compendial multi-pH dissolution, cumulative % at 6 h:
    diss_multipH_freebase={1.2: 0.254, 4.5: 0.0854, 6.8: 0.0274},  # clear weak-base pH dependence
    diss_pH1_2_salt={"mesylate": 0.935, "besylate": 0.986},        # pH 1.2 at 6 h
    # observed PK ratios vs free base:
    obs_ratio={"mesylate": dict(AUC=3.88, Cmax=3.65),
               "besylate": dict(AUC=2.94, Cmax=2.87)},
)
