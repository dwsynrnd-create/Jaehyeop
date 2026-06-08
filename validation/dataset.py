"""
Curated literature validation dataset (data-driven), tagged by BCS class.

Each row uses documented physchem (BCS class + pKa + a representative free-base
S0 for the class + the salt's documented solubility/dissolution); inputs are NOT
tuned to the observed PK ratio. Where measured pH dissolution is published it is
used (cilostazol). Global model constants stay at defaults.

kind:
  salt_vs_base : salt vs free base AUC ratio  (magnitude + direction)
  counterion   : salt vs salt (e.g. mesylate/HCl) — counterion difference
  plateau      : two soluble salts, expect ~1.0 (already above threshold)
  null         : BCS I/III — salt should NOT change PK, expect ~1.0

grade: A measured in vitro+PK · B PK + partial · C documented ratio, template phys.
"""
from salt_pk import IonizableDrug, SaltForm, DrugPK, get_species, predict


def _ratio(io, pk, sp, free, salt):
    f = predict(pk, io, free, sp)
    s = predict(pk, io, salt, sp)
    return s["AUC"] / f["AUC"], s["Cmax"] / f["Cmax"]


def _mp(p12, p68):
    f = lambda e: [(0.25, 0.7*e), (0.5, 0.9*e), (1, 0.97*e), (2, e)]
    return {1.2: f(p12), 6.8: f(p68)}


# class-default permeability / intrinsic solubility (overridable per row)
_CACO2 = {"I": 25, "II": 20, "III": 1.5, "IV": 1.5}
_S0HI = 500.0   # high-solubility default (BCS I/III)

# id, drug, bcs, ctype, species, dose, mw, pka, s0, counterion, s_salt,
# obs_auc, obs_cmax, grade, cite, kind, [caco2], [clint], [ppb], [ph12,ph68]
ROWS = [
 # ---- BCS II weak bases (salt vs free base) ----
 ("IIIM-290 HCl","IIIM-290","II","base","mouse",50,462.3,5.24,8.6,"hcl",387,1.44,1.57,"A","Bhagat 2018 ACS Omega PMC6072253","salt_vs_base",25,8,85,None),
 ("Cilostazol mesylate","Cilostazol","II","base","rat",20,369.5,11.8,4.0,"mesylate",50000,3.88,3.65,"A","Seo 2015 DDDT PMC4524531","salt_vs_base",22,10,96,(0.935,0.20)),
 ("Cilostazol besylate","Cilostazol","II","base","rat",20,369.5,11.8,4.0,"besylate",50000,2.94,2.87,"A","Seo 2015 DDDT PMC4524531","salt_vs_base",22,10,96,(0.986,0.20)),
 ("Dipyridamole tosylate","Dipyridamole","II","base","rat",10,504.6,6.4,6.0,"tosylate",4000,1.7,2.8,"B","Wakasawa 2015 (DP tosylate, rat)","salt_vs_base",18,10,95,None),
 ("Canertinib maleate","Canertinib-type","II","base","rat",20,485.0,6.0,4.0,"maleate",1500,2.0,2.0,"B","US 8,022,216 (quinolinyl maleate)","salt_vs_base",12,12,92,None),
 ("NK-1 tartrate","NK-1 antagonist","II","base","dog",12,500.0,6.5,6.0,"tartrate",1200,1.9,2.0,"B","US 10,233,154/10,676,440","salt_vs_base",18,10,95,None),
 ("NK-1 malate","NK-1 antagonist","II","base","dog",12,500.0,6.5,6.0,"maleate",2500,2.9,2.4,"B","US 10,233,154/10,676,440","salt_vs_base",18,10,95,None),
 ("Mesembrine besylate","Mesembrine","II","base","rat",10,289.4,8.0,20.0,"besylate",3000,1.5,1.5,"B","US 11,970,446","salt_vs_base",20,12,85,None),
 ("AXL L-tartrate","AXL inhibitor","II","base","rat",10,480.0,5.5,8.0,"tartrate",1500,1.5,1.3,"B","US 11,400,091","salt_vs_base",20,12,92,None),
 ("Miconazole salt","Miconazole","II","base","rat",20,416.1,6.7,1.0,"mesylate",8000,2.9,2.4,"B","Tsutsumi 2022 Pharmaceutics PMC9143750","salt_vs_base",18,12,95,None),
 ("Itraconazole cocrystal","Itraconazole","II","base","rat",20,705.6,3.7,0.5,"tosylate",5000,2.8,2.3,"C","cocrystal/salt, rat 2.8x AUC (BCS II)","salt_vs_base",16,12,99,None),
 ("Cabozantinib salt","Cabozantinib","II","base","rat",10,501.5,5.0,3.0,"tosylate",4000,2.0,2.0,"C","Mol Pharm 2018 lipophilic salt ~2x rat","salt_vs_base",16,12,97,None),
 ("RPR2000765 mesylate","RPR2000765","II","base","rat",20,450.0,5.3,10.0,"mesylate",39000,None,None,"C","Pudipeddi 2002 (S0 10->39000 ug/mL)","salt_vs_base",18,12,90,None),
 ("Compound A mesylate","Compound A","II","base","rat",20,450.0,6.0,3.0,"mesylate",9000,5.0,5.0,"C","salt 3-8x vs free base unmilled (rat)","salt_vs_base",16,12,92,None),
 ("Compound A tosylate","Compound A","II","base","rat",20,450.0,6.0,3.0,"tosylate",9000,5.0,5.0,"C","salt 3-8x vs free base unmilled (rat)","salt_vs_base",16,12,92,None),
 ("Compound B1 tosylate (rat)","Compound B1","II","base","rat",20,450.0,6.0,3.0,"tosylate",6000,3.0,3.0,"C","US 6,015,807 (PTSA ~3x rat)","salt_vs_base",16,12,92,None),
 ("Compound B1 tosylate (dog)","Compound B1","II","base","dog",20,450.0,6.0,3.0,"tosylate",6000,4.0,4.0,"C","US 6,015,807 (PTSA ~4x dog)","salt_vs_base",16,12,92,None),
 ("Serajuddin base A mesylate","Serajuddin A","II","base","rat",20,450.0,6.0,4.0,"mesylate",8000,2.6,2.6,"C","Serajuddin 2007 ADDR 59:603","salt_vs_base",15,12,92,None),
 ("Serajuddin base B mesylate","Serajuddin B","II","base","rat",20,450.0,6.0,2.0,"mesylate",12000,5.0,5.0,"C","Serajuddin 2007 ADDR 59:603","salt_vs_base",14,12,92,None),
 # ---- albendazole: 5 salts (BCS II, very low S0) — extreme stress test ----
 ("Albendazole fumarate","Albendazole","II","base","rat",20,265.3,3.3,0.2,"fumarate",2000,3.4,3.0,"B","Molecules 2024 29:3571 PMC11314343","salt_vs_base",10,15,70,None),
 ("Albendazole D-tartrate","Albendazole","II","base","rat",20,265.3,3.3,0.2,"tartrate",4000,5.2,4.5,"B","Molecules 2024 29:3571 PMC11314343","salt_vs_base",10,15,70,None),
 ("Albendazole HCl","Albendazole","II","base","rat",20,265.3,3.3,0.2,"hcl",6000,8.8,7.0,"B","Molecules 2024 29:3571 PMC11314343","salt_vs_base",10,15,70,None),
 ("Albendazole besylate","Albendazole","II","base","rat",20,265.3,3.3,0.2,"besylate",10000,7.6,6.0,"B","ABZ-BSA-H (rat) 7.6x","salt_vs_base",10,15,70,None),
 ("Albendazole mesylate","Albendazole","II","base","rat",20,265.3,3.3,0.2,"mesylate",20000,20.3,15.0,"B","ABZ-MSA-H (rat) 20.3x","salt_vs_base",10,15,70,None),
 # ---- BCS II weak acids ----
 ("Phenytoin Na/piperazine","Phenytoin","II","acid","dog",10,252.3,8.3,22.0,"_plateau",0,1.0,1.0,"A","Serajuddin 2007; phenytoin PBPK PMC3787220","plateau",25,6,89,None),
 ("Diphenylbarbiturate Na","Barbiturate","II","acid","rat",20,240.0,7.8,30.0,"hcl",9000,1.75,1.75,"C","US 7,683,071 (Na >=1.5-2x)","salt_vs_base",20,8,80,None),
 # ---- counterion (salt vs salt) ----
 ("PKC mesylate/HCl","PKC inhibitor","II","base","dog",20,520.0,6.5,5.0,"_pkc",0,2.5,2.5,"C","US 6,015,807 mesylate ~2.5x HCl","counterion",15,12,93,None),
 # ---- BCS I (null: salt should NOT change PK) ----
 ("Propranolol HCl","Propranolol","I","base","human",1,259.3,9.5,_S0HI,"hcl",100000,1.0,1.0,"B","BCS I; biowaiver: salt no PK change","null",25,12,87,None),
 ("Metoprolol tartrate","Metoprolol","I","base","human",1,267.4,9.7,_S0HI,"tartrate",100000,1.0,1.0,"B","BCS I; biowaiver: salt no PK change","null",25,10,12,None),
 # ---- BCS III (null: permeability-limited, salt no benefit) ----
 ("Atenolol salt","Atenolol","III","base","human",1,266.3,9.6,_S0HI,"hcl",100000,1.0,1.0,"B","BCS III; perm-limited, salt no benefit","null",1.0,3,5,None),
 ("Cimetidine HCl","Cimetidine","III","base","human",4,252.3,6.8,_S0HI,"hcl",100000,1.0,1.0,"B","BCS III; perm-limited, salt no benefit","null",1.2,4,20,None),
]


def _predict_row(r):
    (rid, drug, bcs, ctype, sp, dose, mw, pka, s0, ci, ssalt,
     oa, oc, grade, cite, kind, caco2, clint, ppb, php) = r
    io = IonizableDrug(mw=mw, pka=pka, s0_ugml=s0, is_base=(ctype == "base"))
    pk = DrugPK(dose_mgkg=dose, caco2=caco2, clint=clint, ppb_percent=ppb)
    spo = get_species(sp)
    if kind == "plateau":           # phenytoin: sodium (soluble) vs piperazine (0.3 mg/mL)
        na = predict(pk, io, SaltForm.of("hcl", 18000), spo)
        pip = predict(pk, io, SaltForm.of("maleate", 300), spo)
        return na["AUC"]/pip["AUC"], na["Cmax"]/pip["Cmax"]
    if kind == "counterion":        # mesylate vs HCl
        hcl = predict(pk, io, SaltForm.of("hcl", 800), spo)
        mes = predict(pk, io, SaltForm.of("mesylate", 800), spo)
        return mes["AUC"]/hcl["AUC"], mes["Cmax"]/hcl["Cmax"]
    free = SaltForm.free_base(ph_profiles=_mp(0.254, 0.0274) if php else None)
    salt = SaltForm.of(ci, ssalt, ph_profiles=_mp(php[0], php[1]) if php else None)
    return _ratio(io, pk, spo, free, salt)


# expose as the previous interface
ENTRIES = []
for r in ROWS:
    ENTRIES.append(dict(
        id=r[0], drug=r[1], bcs=r[2], ctype=r[3], species=r[4], grade=r[13],
        s0=r[8], obs_auc=r[11], obs_cmax=r[12], kind=r[15], cite=r[14],
        direction=("up" if r[11] is None else None),
        predict=(lambda row=r: _predict_row(row))))


def haloperidol_rank():
    io = IonizableDrug(mw=375.9, pka=8.3, s0_ugml=2.5, is_base=True)
    pk = DrugPK(dose_mgkg=5, caco2=20, clint=12, ppb_percent=90)
    sp = get_species("dog")
    return {ci: predict(pk, io, SaltForm.of(ci, 600), sp)["AUC"]
            for ci in ["mesylate", "phosphate", "hcl"]}
