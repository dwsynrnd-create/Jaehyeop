"""
Batch CSV import + auto-validation for in-house salt-screening data.

This is the practical path to scaling the validation/usage to many compounds:
labs already generate pH 1.2/4.5/6.8 dissolution for every form, so they can drop
it into one CSV and get predictions + (if observed PK is supplied) an accuracy
report — no Python edits required.

CSV format (one row per FORM; the free base is a row with counterion=free_base):

  drug, moiety, mw, pka, s0_ugml, species, dose_mgkg, caco2, clint, ppb, vss,
  form, counterion, s_salt_ugml,
  d_pH1_2, d_pH4_5, d_pH6_8,        # "min:pct;min:pct" e.g. "15:70;30:88;60:95"
  sol_pH6_8,                        # measured pH6.8 solubility µg/mL (optional)
  obs_auc, obs_cmax,                # observed ratio vs free base (optional)
  grade, cite

Drug-level columns (mw..vss) are read from the free-base row (or any row of the
drug). Predictions are made per form; ratios are vs the same drug's free base.

Usage:
  from salt_pk.batch import run_csv
  rows = run_csv("data/dataset_template.csv")      # -> list of result dicts
  # or:  python -m salt_pk.batch data/dataset_template.csv
"""
import csv
import sys
from collections import defaultdict, OrderedDict

from .solubility import IonizableDrug, SaltForm
from .physiology import get as get_species
from .engine import DrugPK, AbsParams, predict


def _f(v):
    v = (v or "").strip()
    try:
        return float(v)
    except ValueError:
        return None


def _parse_profile(s):
    """'15:70;30:88;60:95' (min:pct) -> [(time_h, frac_0to1), ...] or None"""
    s = (s or "").strip()
    if not s:
        return None
    pts = []
    for chunk in s.replace(",", ";").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        t, p = chunk.split(":")
        pts.append((float(t) / 60.0, float(p) / 100.0))
    return sorted(pts) or None


def load_csv(path):
    """Group CSV rows into {drug: {'drug_kw':..,'pk_kw':..,'forms':[(row, SaltForm)]}}"""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    drugs = OrderedDict()
    for r in rows:
        d = r["drug"].strip()
        drugs.setdefault(d, {"rows": []})["rows"].append(r)

    out = OrderedDict()
    for d, info in drugs.items():
        rws = info["rows"]
        base_row = next((r for r in rws if r.get("counterion", "").strip().lower()
                         in ("free_base", "free base", "freebase", "")), rws[0])
        is_base = base_row.get("moiety", "base").strip().lower() != "acid"
        drug_io = IonizableDrug(mw=_f(base_row["mw"]) or 350,
                                pka=_f(base_row["pka"]) or 7.0,
                                s0_ugml=_f(base_row["s0_ugml"]) or 10.0,
                                is_base=is_base)
        pk = DrugPK(dose_mgkg=_f(base_row["dose_mgkg"]) or 10,
                    caco2=_f(base_row.get("caco2")),
                    clint=_f(base_row.get("clint")),
                    ppb_percent=_f(base_row.get("ppb")),
                    vss=_f(base_row.get("vss")))
        sp = get_species(base_row.get("species", "rat").strip() or "rat")
        forms = []
        for r in rws:
            ci = (r.get("counterion", "").strip().lower().replace(" ", "_") or "free_base")
            php = {}
            for col, ph in (("d_pH1_2", 1.2), ("d_pH4_5", 4.5), ("d_pH6_8", 6.8)):
                p = _parse_profile(r.get(col))
                if p:
                    php[ph] = p
            php = php or None
            ph_sol = {6.8: _f(r.get("sol_pH6_8"))} if _f(r.get("sol_pH6_8")) else None
            if ci in ("free_base",):
                form = SaltForm.free_base(label=r.get("form", "free base"), ph_profiles=php)
                if ph_sol:
                    form.ph_solubility = ph_sol
            else:
                form = SaltForm.of(ci, _f(r.get("s_salt_ugml")) or 1000,
                                   label=r.get("form") or f"{ci} salt",
                                   ph_profiles=php, ph_solubility=ph_sol)
            forms.append((r, form))
        out[d] = dict(drug_io=drug_io, pk=pk, sp=sp, forms=forms,
                      base_label=base_row.get("form", "free base"))
    return out


def run_csv(path, ap=None):
    """Predict every form, compute ratio vs free base, score if obs given."""
    ap = ap or AbsParams()
    data = load_csv(path)
    results = []
    for drug, info in data.items():
        preds = []
        for r, form in info["forms"]:
            res = predict(info["pk"], info["drug_io"], form, info["sp"], ap)
            preds.append((r, form, res))
        ref = next((p for p in preds if p[1].s_salt_ugml is None), preds[0])
        ref_auc, ref_cmax = ref[2]["AUC"], ref[2]["Cmax"]
        for r, form, res in preds:
            if form.s_salt_ugml is None:
                continue
            rA = res["AUC"] / ref_auc if ref_auc else float("nan")
            rC = res["Cmax"] / ref_cmax if ref_cmax else float("nan")
            oA, oC = _f(r.get("obs_auc")), _f(r.get("obs_cmax"))
            results.append(dict(
                drug=drug, form=form.label, grade=(r.get("grade") or "").strip(),
                pred_auc=rA, pred_cmax=rC, obs_auc=oA, obs_cmax=oC,
                acc_auc=(max(0.0, 100*(1-abs(rA-oA)/oA)) if oA else None),
                within2=(max(rA/oA, oA/rA) <= 2.0 if oA else None),
                cite=(r.get("cite") or "").strip()))
    return results


def summary(results):
    scored = [r for r in results if r["obs_auc"]]
    n2 = sum(1 for r in scored if r["within2"])
    macc = sum(r["acc_auc"] for r in scored) / len(scored) if scored else float("nan")
    ndir = sum(1 for r in scored if (r["pred_auc"] > 1.15) == (r["obs_auc"] > 1.15))
    return dict(n=len(results), n_scored=len(scored), within2=n2,
                mean_acc=macc, dir_ok=ndir)


def _main(path):
    results = run_csv(path)
    print(f"{'drug':22}{'form':14}{'grd':>4}{'predAUC':>9}{'obsAUC':>8}{'acc%':>6}{'2fold':>7}")
    print("-" * 72)
    for r in results:
        oa = f"{r['obs_auc']:.2f}" if r["obs_auc"] else "—"
        ac = f"{r['acc_auc']:.0f}" if r["acc_auc"] is not None else "—"
        tf = ("ok" if r["within2"] else "OUT") if r["within2"] is not None else "—"
        print(f"{r['drug'][:22]:22}{r['form'][:14]:14}{r['grade']:>4}"
              f"{r['pred_auc']:9.2f}{oa:>8}{ac:>6}{tf:>7}")
    s = summary(results)
    print("-" * 72)
    print(f"forms={s['n']}  scored={s['n_scored']}  within2={s['within2']}/{s['n_scored']}  "
          f"direction={s['dir_ok']}/{s['n_scored']}  mean_acc={s['mean_acc']:.0f}%")


if __name__ == "__main__":
    _main(sys.argv[1] if len(sys.argv) > 1 else "data/dataset_template.csv")
