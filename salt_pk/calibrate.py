"""
Calibrate the global absorption constants to in-house data.

Given a CSV of compounds with observed salt/free-base AUC ratios (see
salt_pk.batch format), grid-search kd0, kprecip, salt_wettability to minimise the
geometric (fold) error, then report before/after accuracy and the tuned constants.

This is how a lab moves the tool from "screening" toward "decision" grade: fit
once on >=10 reference compounds, then use the tuned constants for ranking.

Usage:
  python -m salt_pk.calibrate data/your_data.csv
"""
import math
import sys

from .engine import AbsParams
from .batch import run_csv


def _fold_err(results):
    errs = [abs(math.log(r["pred_auc"] / r["obs_auc"]))
            for r in results if r["obs_auc"] and r["pred_auc"] > 0]
    return sum(errs) / len(errs) if errs else float("inf")


def _mean_acc(results):
    a = [r["acc_auc"] for r in results if r["acc_auc"] is not None]
    return sum(a) / len(a) if a else float("nan")


def calibrate(path, kd0s=(0.3, 0.5, 0.8), kprecips=(0.5, 1, 2, 4, 8),
              wets=(2, 4, 6, 8), verbose=True):
    base = run_csv(path, AbsParams())
    base_err, base_acc = _fold_err(base), _mean_acc(base)
    best = (base_err, AbsParams(), base_acc)
    for kd0 in kd0s:
        for kp in kprecips:
            for w in wets:
                ap = AbsParams(kd0=kd0, kprecip=kp, salt_wettability=w)
                res = run_csv(path, ap)
                err = _fold_err(res)
                if err < best[0]:
                    best = (err, ap, _mean_acc(res))
    err, ap, acc = best
    if verbose:
        print("Calibration (geometric fold-error minimisation)")
        print("-" * 60)
        print(f"  default : fold-err {base_err:.3f}  mean-acc {base_acc:.0f}%  "
              f"(kd0={AbsParams().kd0}, kprecip={AbsParams().kprecip}, wet={AbsParams().salt_wettability})")
        print(f"  tuned   : fold-err {err:.3f}  mean-acc {acc:.0f}%  "
              f"(kd0={ap.kd0}, kprecip={ap.kprecip}, wet={ap.salt_wettability})")
        impr = acc - base_acc
        print(f"  -> mean accuracy {('+' if impr>=0 else '')}{impr:.0f} %p  "
              f"(fold-err {base_err:.3f} -> {err:.3f})")
        if base_err - err < 0.02:
            print("  (default already near-optimal on this set)")
    return ap, dict(default_err=base_err, tuned_err=err,
                    default_acc=base_acc, tuned_acc=acc)


if __name__ == "__main__":
    calibrate(sys.argv[1] if len(sys.argv) > 1 else "data/dataset_template.csv")
