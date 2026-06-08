"""
Species physiology for IVIVE scaling and the GI absorption model.

Sources: Davies & Morris 1993 (Qh, body weight); Barter 2007 (MPPGL);
Sohlenius-Sternbeck 2006 (HPGL); standard compartmental GI values.
"""

from dataclasses import dataclass


@dataclass
class Species:
    label: str
    bw: float          # body weight, kg
    Qh: float          # hepatic blood flow, mL/min/kg
    liver_wt: float    # liver weight, g/kg
    MPPGL: float       # mg microsomal protein / g liver
    HPGL: float        # 1e6 hepatocytes / g liver
    V_stomach: float   # gastric fluid volume, mL
    V_si: float        # small-intestinal fluid volume, mL
    Tsi: float         # small-intestinal transit time, h
    kge: float         # gastric emptying rate constant, 1/h
    pH_stomach: float = 2.0
    pH_si: float = 6.5


SPECIES = {
    "mouse": Species("Mouse", bw=0.025, Qh=90, liver_wt=55, MPPGL=45, HPGL=135,
                     V_stomach=0.3, V_si=1.5, Tsi=1.5, kge=6.0),
    "rat":   Species("Rat",   bw=0.25,  Qh=55, liver_wt=40, MPPGL=45, HPGL=117,
                     V_stomach=1.0, V_si=5.0, Tsi=1.5, kge=3.0),
    "dog":   Species("Dog",   bw=10.0,  Qh=31, liver_wt=32, MPPGL=78, HPGL=215,
                     V_stomach=8.0, V_si=45.0, Tsi=2.0, kge=2.0),
    "human": Species("Human", bw=70.0,  Qh=21, liver_wt=21.4, MPPGL=40, HPGL=99,
                     V_stomach=50.0, V_si=250.0, Tsi=3.3, kge=2.0),
}


def get(name: str) -> Species:
    key = name.strip().lower()
    if key not in SPECIES:
        raise KeyError(f"Unknown species '{name}'. Known: {list(SPECIES)}")
    return SPECIES[key]
