"""
IVIVE oral-PK engine with a salt-aware, supersaturation/precipitation
absorption model.

Disposition (CL, Vss, t1/2, Fh) is a property of the FREE BASE and is therefore
identical for every salt of the same drug.  Salt forms differ ONLY in
absorption, which is modelled mechanistically:

    stomach[solid] --diss--> stomach[dissolved] --gastric emptying-->
        SI[dissolved] <==precip/redissolve==> SI[solid]
        SI[dissolved] --ka--> central --k_el--> out

Dissolution uses a diffusion-layer (Mooney/Serajuddin) view: the dissolution
rate is proportional to the solubility at the *particle-surface microenvironment
pH*, which for a strong-acid salt stays acidic (high solubility) even in the
small intestine, whereas the free base sees bulk pH (low solubility at pH 6.5).
That single mechanism reproduces the classic "salt dissolves faster / gives
higher exposure", the common-ion penalty of HCl salts, and SI de-supersaturation.

Because the salt vs free-base AUC ratio is governed entirely by Fa (disposition
cancels), the model's salt-screening predictions are robust to the absolute
disposition assumptions — exactly what validation against literature confirms.
"""

import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from .physiology import Species
from .solubility import IonizableDrug, SaltForm, solubility, pHmax


@dataclass
class DrugPK:
    """Disposition + permeability — shared by all salt forms of one drug."""
    dose_mgkg: float
    caco2: float                       # Papp, 1e-6 cm/s (None -> use logD heuristic)
    clint: Optional[float] = None      # uL/min/mg (microsome) or uL/min/1e6 cells
    cl_system: str = "microsome"       # 'microsome' | 'hepatocyte'
    ppb_percent: Optional[float] = None
    vss: Optional[float] = None        # L/kg (None -> estimated)
    logd: float = 1.5
    fg: float = 1.0
    cl_other: float = 0.0              # mL/min/kg (renal/biliary)
    rb: float = 1.0                    # blood:plasma ratio
    fu_inc: Optional[float] = None
    kscale: float = 0.30               # Caco-2 -> ka conversion
    route: str = "PO"


@dataclass
class AbsParams:
    """Tunable absorption/dissolution constants (defaults validated on BCS I-IV)."""
    kd0: float = 0.5         # free-base dissolution rate constant, 1/h (fine particles)
    kprecip: float = 2.0     # precipitation rate constant (1/h) toward equilibrium solubility
    salt_wettability: float = 4.0   # faster intrinsic dissolution / wetting of salts (>=1)
    d50_um: Optional[float] = None  # particle size; scales dissolution if given


def _disposition(drug: DrugPK, sp: Species):
    fu_p = max(0.001, (100 - drug.ppb_percent) / 100) if drug.ppb_percent is not None else None
    Rb = drug.rb or 1.0
    notes = []

    CLint_scaled = None
    if drug.clint is not None:
        sf = (sp.HPGL if drug.cl_system == "hepatocyte" else sp.MPPGL) * sp.liver_wt / 1000.0
        CLint_scaled = drug.clint * sf
        if drug.fu_inc and drug.fu_inc > 0:
            CLint_scaled /= drug.fu_inc

    fu_b = (fu_p if fu_p is not None else 0.1) / Rb
    if CLint_scaled is not None:
        CLh_blood = sp.Qh * fu_b * CLint_scaled / (sp.Qh + fu_b * CLint_scaled)
        Eh = CLh_blood / sp.Qh
        CLh_plasma = CLh_blood * Rb
    else:
        CLh_plasma = sp.Qh * 0.3 * Rb
        Eh = (CLh_plasma / Rb) / sp.Qh
        notes.append("no metabolic data — CLh assumed (Eh=0.3)")
    Fh = 1 - Eh
    CL = CLh_plasma + (drug.cl_other or 0.0)        # mL/min/kg

    if drug.vss:
        Vss = drug.vss
        vss_est = False
    else:
        Vp, Ve, Rei, Vr = 0.0436, 0.151, 1.4, 0.38
        fpp = fu_p if fu_p is not None else 0.1
        fut = 1.0 / (1.0 + 10 ** (0.6 * (drug.logd - 0.5)))
        fut = max(5e-4, min(1.0, fut))
        Vss = max(0.1, Vp * (1 + Rei) + fpp * Vp * (Ve / Vp - Rei) + Vr * fpp / fut)
        vss_est = True
        notes.append("Vss estimated (measured value recommended)")

    k_el = CL * 60 / 1000.0 / Vss      # 1/h
    t_half = math.log(2) / k_el
    return dict(CL=CL, Vss=Vss, k_el=k_el, t_half=t_half, Fh=Fh, Eh=Eh,
                CLint_scaled=CLint_scaled, fu=fu_p, vss_est=vss_est, notes=notes)


def _surface_solubility(drug_io: IonizableDrug, form: SaltForm, region: str, bulk_pH: float,
                        ignore_common_ion: bool = False):
    """Solubility (µg/mL) at the dissolving particle's diffusion-layer pH."""
    if form.s_salt_ugml is None:                 # free base: surface pH = bulk pH
        return solubility(drug_io, form, bulk_pH, region)
    pm = pHmax(drug_io, form)
    # strong-acid salt buffers its own diffusion layer to ~ just inside its stable region
    if drug_io.is_base:
        surf_pH = min(bulk_pH, max(1.0, pm - 0.5))
    else:
        surf_pH = max(bulk_pH, min(13.0, pm + 0.5))
    return solubility(drug_io, form, surf_pH, region, ignore_common_ion)


def predict(drug: DrugPK, drug_io: IonizableDrug, form: SaltForm, sp: Species,
            ap: AbsParams = AbsParams(), t_end: float = 48.0, dt: float = 0.001) -> Dict:
    d = _disposition(drug, sp)
    Fh, Fg, k_el, Vss = d["Fh"], drug.fg or 1.0, d["k_el"], d["Vss"]
    dose_ug = drug.dose_mgkg * sp.bw * 1000.0
    Vc = Vss * sp.bw                  # central volume, L  (conc in µg/L = ng/mL)

    prof = []
    if drug.route == "IV":
        t = 0.0
        while t <= t_end + 1e-9:
            prof.append((round(t, 3), (dose_ug / Vc) * math.exp(-k_el * t)))
            t += 0.05
        Fa, F = 1.0, 1.0
    else:
        # permeability -> ka (1/h)
        if drug.caco2 is not None:
            ka = (drug.kscale or 0.30) * drug.caco2
        else:
            ka = 3.0 if drug.logd > 1 else (0.7 if drug.logd > -0.5 else 0.2)
        ka = max(0.02, min(15.0, ka))

        # Compendial multi-pH dissolution (Tier 3): LOW pH -> gastric release,
        # HIGH pH -> intestinal solubility ceiling (parachute floor).
        multi_ph = bool(form.ph_profiles)
        si_ceiling_frac = None
        prof_src = None
        if multi_ph:
            phs = sorted(form.ph_profiles)
            prof_src = form.ph_profiles[phs[0]]               # lowest pH -> stomach
            si_ceiling_frac = max(fr for _, fr in form.ph_profiles[phs[-1]])
        else:
            prof_src = form.diss_profile

        # region solubility CEILINGS (encode common-ion for HCl and pHmax).
        # DISSOLUTION proceeds toward the intrinsic (common-ion-free) surface
        # solubility -> a salt dissolves fast and can transiently SUPERSATURATE.
        Cs_g_diss = _surface_solubility(drug_io, form, "stomach", sp.pH_stomach, ignore_common_ion=True)
        Cs_si_diss = _surface_solubility(drug_io, form, "si", sp.pH_si, ignore_common_ion=True)
        # PRECIPITATION pulls the dissolved drug back toward the LOCAL EQUILIBRIUM
        # solubility: in the stomach this includes the common-ion (chloride) effect
        # for HCl salts; in the SI it is the stable free-base solubility.
        Cs_g_eq = solubility(drug_io, form, sp.pH_stomach, "stomach")  # common-ion included
        Cs_si_eq = solubility(drug_io, SaltForm.free_base(), sp.pH_si, "si")
        if multi_ph:
            # intestinal solubility ceiling from the measured high-pH (e.g. 6.8) plateau;
            # the SI dissolution ceiling is the SAME measured level (emptied solid can
            # only dissolve to the intestinal-pH extent, not the mechanistic value).
            Cs_si_eq = max(1e-6, si_ceiling_frac * dose_ug / sp.V_si)
            Cs_si_diss = Cs_si_eq
        Cs_g_rate, Cs_si_rate = Cs_g_diss, Cs_si_diss                 # drive wetting/RATE edge

        # Dissolution RATE constants (1/h), Noyes-Whitney: rate ∝ surface
        # solubility, but BOUNDED (ENH_MAX) so a freely-soluble compound dissolves
        # fast (BCS I) while a weak base does not dissolve instantaneously.
        # `salt_wettability` adds the kinetic edge of salts (better wetting).
        S0REF, ENH_MAX = 50.0, 20.0
        enh_g = min(Cs_g_rate / S0REF, ENH_MAX)
        enh_si = min(Cs_si_rate / S0REF, ENH_MAX)
        size = 1.0 if not ap.d50_um else max(0.2, min(5.0, 10.0 / ap.d50_um))
        wet = ap.salt_wettability if form.s_salt_ugml is not None else 1.0
        kd_g = max(0.005, min(50.0, ap.kd0 * wet * size * enh_g))
        kd_si = max(0.005, min(50.0, ap.kd0 * wet * size * enh_si))
        if multi_ph:
            # intestinal re-dissolution rate from the measured high-pH (6.8) profile:
            # first-order k from the time to reach ~63% of its plateau.
            si_pts2 = sorted(form.ph_profiles[sorted(form.ph_profiles)[-1]])
            plat = max(fr for _, fr in si_pts2)
            t63 = next((t for t, fr in si_pts2 if fr >= 0.63 * plat and t > 0), None)
            kd_si = max(0.02, min(50.0, (1.0 / t63) if t63 else 0.3))

        kge = sp.kge
        kt = 1.0 / sp.Tsi

        # measured dissolution -> gastric release input function (single medium or
        # the low-pH leg of the compendial multi-pH set, prepared above)
        prof_pts = None
        if prof_src:
            prof_pts = sorted([(float(t), max(0.0, min(1.0, float(fr))))
                               for t, fr in prof_src])
            if prof_pts[0][0] > 0:
                prof_pts.insert(0, (0.0, 0.0))

        def cum_frac(t):
            if t <= prof_pts[0][0]:
                return prof_pts[0][1]
            for i in range(1, len(prof_pts)):
                if t <= prof_pts[i][0]:
                    a, b = prof_pts[i - 1], prof_pts[i]
                    return a[1] + (b[1] - a[1]) * (t - a[0]) / (b[0] - a[0])
            return prof_pts[-1][1]

        def diss_slope(t):
            h = 0.01
            return max(0.0, (cum_frac(t + h) - cum_frac(max(0.0, t - h))) / (h if t - h < 0 else 2 * h))

        # Tier 4: two-stage / transfer intestinal profile (FaSSGF -> FaSSIF).
        # fraction-of-dose IN SOLUTION in the intestinal compartment vs time; may be
        # NON-MONOTONIC (rise = dissolution/supersaturation, fall = precipitation).
        intl_pts = None
        if form.intestinal_profile:
            intl_pts = sorted([(float(t), max(0.0, min(1.0, float(fr))))
                               for t, fr in form.intestinal_profile])
            if intl_pts[0][0] > 0:
                intl_pts.insert(0, (0.0, 0.0))

        def intl_frac(t):
            if t <= intl_pts[0][0]:
                return intl_pts[0][1]
            for i in range(1, len(intl_pts)):
                if t <= intl_pts[i][0]:
                    a, b = intl_pts[i - 1], intl_pts[i]
                    return a[1] + (b[1] - a[1]) * (t - a[0]) / (b[0] - a[0])
            return intl_pts[-1][1]

        def intl_signed_slope(t):
            h = 0.01
            return (intl_frac(t + h) - intl_frac(max(0.0, t - h))) / (h if t - h < 0 else 2 * h)

        Ags, Agd, As, Ad, Ac = dose_ug, 0.0, 0.0, 0.0, 0.0
        absorbed = 0.0

        def deriv(t, Ags, Agd, As, Ad, Ac):
            if intl_pts is not None:
                # measured transfer curve drives the SI dissolved pool directly:
                # +slope = dissolution into solution, -slope = precipitation out.
                inp = dose_ug * intl_signed_slope(t)
                ab = ka * Ad
                dAd = inp - ab - kt * Ad
                return 0.0, 0.0, 0.0, dAd, Fh * Fg * ab - k_el * Ac, ab
            Cg = Agd / sp.V_stomach
            Csi = Ad / sp.V_si
            if prof_pts is not None:
                diss_g = dose_ug * diss_slope(t)     # measured release rate (µg/h)
            else:
                diss_g = kd_g * Ags * max(0.0, 1.0 - Cg / max(Cs_g_diss, 1e-9))
            diss_si = kd_si * As * max(0.0, 1.0 - Csi / max(Cs_si_diss, 1e-9))
            # supersaturation -> precipitation toward local equilibrium solubility
            precip_g = ap.kprecip * max(0.0, Cg - Cs_g_eq) * sp.V_stomach
            precip_si = ap.kprecip * max(0.0, Csi - Cs_si_eq) * sp.V_si
            # Single-medium profile: undissolved solid is NOT re-dissolved (final
            # cumulative % = absorption ceiling). Multi-pH and mechanistic modes let
            # the solid empty and dissolve at the intestinal pH (re-dissolution).
            ge_s = 0.0 if (prof_pts is not None and not multi_ph) else kge * Ags
            ge_d = kge * Agd
            ab = ka * Ad
            dAgs = -diss_g + precip_g - ge_s
            dAgd = diss_g - precip_g - ge_d
            dAs = ge_s + precip_si - diss_si - kt * As
            dAd = ge_d + diss_si - precip_si - ab - kt * Ad
            dAc = Fh * Fg * ab - k_el * Ac
            return dAgs, dAgd, dAs, dAd, dAc, ab

        t, ns = 0.0, 0.0
        while t <= t_end + 1e-9:
            if t >= ns - 1e-9:
                prof.append((round(t, 3), Ac / Vc))
                ns += 0.05
            a = deriv(t, Ags, Agd, As, Ad, Ac)
            b = deriv(t + .5*dt, Ags + .5*dt*a[0], Agd + .5*dt*a[1], As + .5*dt*a[2], Ad + .5*dt*a[3], Ac + .5*dt*a[4])
            c = deriv(t + .5*dt, Ags + .5*dt*b[0], Agd + .5*dt*b[1], As + .5*dt*b[2], Ad + .5*dt*b[3], Ac + .5*dt*b[4])
            e = deriv(t + dt, Ags + dt*c[0], Agd + dt*c[1], As + dt*c[2], Ad + dt*c[3], Ac + dt*c[4])
            Ags = max(0.0, Ags + dt/6*(a[0]+2*b[0]+2*c[0]+e[0]))
            Agd = max(0.0, Agd + dt/6*(a[1]+2*b[1]+2*c[1]+e[1]))
            As  = max(0.0, As  + dt/6*(a[2]+2*b[2]+2*c[2]+e[2]))
            Ad  = max(0.0, Ad  + dt/6*(a[3]+2*b[3]+2*c[3]+e[3]))
            Ac  = max(0.0, Ac  + dt/6*(a[4]+2*b[4]+2*c[4]+e[4]))
            absorbed += dt/6*(a[5]+2*b[5]+2*c[5]+e[5])
            t += dt
        Fa = min(1.0, absorbed / dose_ug)
        F = Fa * Fg * Fh

    Cmax = max(c for _, c in prof)
    Tmax = next(t for t, c in prof if c == Cmax)
    AUC = sum((prof[i-1][1] + prof[i][1]) * (prof[i][0] - prof[i-1][0]) / 2
              for i in range(1, len(prof)))
    return dict(profile=prof, Cmax=Cmax, Tmax=Tmax, AUC=AUC,
                Fa=Fa, F=F, CL=d["CL"], Vss=Vss, t_half=d["t_half"],
                Fh=Fh, k_el=k_el, vss_est=d["vss_est"], notes=list(d["notes"]),
                pHmax=pHmax(drug_io, form))


def screen(drug: DrugPK, drug_io: IonizableDrug, forms: List[SaltForm], sp: Species,
           ap: AbsParams = AbsParams()) -> List[Dict]:
    """Run all forms; return list of dicts with PK + relative-to-free-base ratios."""
    results = []
    for f in forms:
        r = predict(drug, drug_io, f, sp, ap)
        r["form"] = f
        results.append(r)
    ref = next((r for r in results if r["form"].s_salt_ugml is None), results[0])
    for r in results:
        r["rel_AUC"] = r["AUC"] / ref["AUC"] if ref["AUC"] else float("nan")
        r["rel_Cmax"] = r["Cmax"] / ref["Cmax"] if ref["Cmax"] else float("nan")
    return results
