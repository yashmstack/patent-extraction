# Per-record audit log — CN112645853A
# One block per reaction object. Written BEFORE the finding is raised.
# Order = array order in reactions.json (index 0..54).

## Method for each record
1. Read the record's every field from reactions.json
2. Read its source_lines from reactions-provenance.json
3. Open input/CN112645853A-enriched-numbered.md at those lines + surrounding block
4. Extract independently what the patent states for THIS transformation
5. Diff: extraction vs patent -> MISSING / WRONG / UNSUPPORTED / INCONSISTENT
6. Write findings to GOLDEN-DATASET-FINDINGS.xlsx

## Index (array order)
 0  Background_Step 1                lines=[137, 142, 143, 147]
 1  Background_Step 2                lines=[132, 137, 143, 145, 147]
 2  Background_Side Reaction         lines=[143, 147]
 3  Claims_Step 1                    lines=[43, 45, 49, 51, 53, 55, 57, 59, 61, 63, 108, 110]
 4  Claims_Step 2                    lines=[43, 47, 65, 67, 69, 71, 73, 75, 77, 79, 81, 83, 85, 90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 112]
 5  Example 1_Step 1                 lines=[275, 286]
 6  Example 1_Step 2a                lines=[292, 293]
 7  Example 1_Step 2b                lines=[294, 295]
 8  Example 10_Step 1                lines=[446, 451]
 9  Example 10_Step 2                lines=[453, 458]
10  Example 11_Step 1                lines=[462, 467]
11  Example 11_Step 2                lines=[469, 477]
12  Example 12_Step 1                lines=[481, 486]
13  Example 12_Step 2                lines=[488, 493]
14  Example 13_Step 1                lines=[497, 502]
15  Example 13_Step 2                lines=[504, 509]
16  Example 14_Step 1                lines=[513]
17  Example 14_Step 2                lines=[515, 517, 520]
18  Example 15_Step 1                lines=[524, 524]
19  Example 15_Step 2                lines=[526, 533]
20  Example 16_Step 1                lines=[537, 537]
21  Example 16_Step 2                lines=[539, 543]
22  Example 17_Step 1                lines=[547, 548]
23  Example 17_Step 2a               lines=[553, 558]
24  Example 17_Step 2b               lines=[549, 560]
25  Example 18_Step 1                lines=[564, 564]
26  Example 18_Step 2a               lines=[571, 571]
27  Example 18_Step 2                lines=[566, 573]
28  Example 19_Step 1                lines=[577, 578]
29  Example 19_Step 2a               lines=[584, 585]
30  Example 19_Step 2                lines=[579, 592]
31  Example 2_Step 1                 lines=[298, 301, 303]
32  Example 2_Alkoxide Preparation   lines=[310]
33  Example 2_Step 2                 lines=[305, 308, 312, 317]
34  Example 20_Step 1                lines=[595, 596]
35  Example 20_Step 2a               lines=[602, 603]
36  Example 20_Step 2                lines=[597, 605]
37  Example 3_Step 1                 lines=[321, 326]
38  Example 3_Step 2                 lines=[327, 332]
39  Example 4_Step 1                 lines=[335, 343]
40  Example 4_Step 2                 lines=[344, 350]
41  Example 5_Step 1                 lines=[353, 359]
42  Example 5_Alkoxide Preparation   lines=[365, 366]
43  Example 5_Step 2                 lines=[360, 371]
44  Example 6_Step 1                 lines=[374, 376, 379]
45  Example 6_Step 2                 lines=[381, 383, 386]
46  Example 7_Step 1                 lines=[390, 396, 398]
47  Example 7_Step 2                 lines=[400, 403, 405]
48  Example 8_Step 1                 lines=[409, 415]
49  Example 8_Step 2                 lines=[423, 424]
50  Example 8_Step 3                 lines=[416, 426]
51  Example 9_Step 1                 lines=[429, 434]
52  Example 9_Step 2                 lines=[435, 440]
53  Summary of the Invention_Step 1  lines=[159, 189, 191, 193, 195, 197, 199, 201, 203, 255]
54  Summary of the Invention_Step 2  lines=[168, 205, 207, 212, 214, 216, 218, 220, 222, 224, 226, 228, 230, 232, 234, 236, 238, 240, 242, 244, 246, 248, 257]

================================================================
## [0] Background_Step 1   -- AUDITED
Whole file read: lines 1-270 in full; lines 271-606 swept by grep for
醇钠/醇钾/CN105601548/CN104292137/US6376429/CN1364160/CN1323292/目标物甲酯/皂化.
Nothing outside 137/143/145/147 adds anything to this step.

PATENT SAYS (my independent extraction):
  L137 [0007] prior art. SM = methyl 2-chloro-3-bromomethyl-4-methanesulfonylbenzoate.
       Reagent EITHER "the corresponding alcohol" under base OR "the corresponding
       sodium alkoxide" directly. Product = 目标物甲酯 the methyl ester of the target.
       Attributed to CN105601548A / CN104292137A / US6376429 / CN1364160A / CN1323292A.
  L143 drawing arrow 1: reactant COC(=O)c1ccc(S(C)(=O)=O)c(CBr)c1Cl, conditions ROH + 碱,
       products [] (generic R, no SMILES possible).
  L145 [0009] R = trifluoroethyl -> tembotrione int.; R = 2-THF-methyl -> tefuryltrione int.
  L147 [0010] methanol byproduct from ester cleavage/transesterification.
  No temperature, time, solvent, charge, yield or purity anywhere. no_conditions correct.

VERIFIED CORRECT (passes):
  reactant identity, product identity, methanol as by_product, reaction_class,
  named_reaction, mechanism_type, scale not_specified, all conditions null,
  no_conditions flag, reagent_written_not_drawn flag, is_complete false,
  step_role first_step, linkage standalone, procedure_text verbatim vs L137.

FLAGGED: F-003 alcohol missing | F-004 sodium alkoxide missing |
         F-005 base not recorded (convention inconsistency) |
         F-006 the two specific alcohols from L145 missing, L145 not cited |
         F-007 prior-art citations have no field
CORRECTED [0]: +2,2,2-trifluoroethanol, +tetrahydrofurfuryl alcohol, +sodium 2,2,2-trifluoroethoxide,
  +sodium (tetrahydrofuran-2-yl)methoxide (all reactant), +basic substance (base).
  reactant_names rebuilt. source_lines +145. reagent_written_not_drawn KEPT (still true).
  F-007 left open - schema decision, not a one-record fix.
CONVENTION ESTABLISHED: A-or-B alternatives are recorded as PARALLEL entries in compounds[],
  matching Claims_Step 2 / Summary_Step 2. Parallel entries do not assert co-charging.

================================================================
## [1] Background_Step 2   -- AUDITED + CORRECTED
Re-read L132-148. Swept whole file for 皂化 / 酸化 / 关键中间体 / the acid product.
  KEY: 皂化 appears ONLY at L137. The 酸化 mentions (L96,98,100,244,246,248) are the
  INVENTION's step 2, NOT prior art -> must not be imported here.

PATENT SAYS: L137 "which is then further saponified to give 2-chloro-3-alkoxymethyl-4-
  methanesulfonylbenzoic acid". L143 arrow 2 conditions = "1) 碱 base", "2) 酸 acid";
  reactants[] and products[] empty (generic R, no SMILES possible). L132 the product is
  the key intermediate. L145 R = trifluoroethyl or 2-THF-methyl. L147 impurity 3-5/8-12%.
  No temperature, time, charge, yield or pH anywhere.

PASSES: reactant, product, by_product impurity, reaction_class hydrolysis,
  named_reaction saponification, precursor_step Step 1 + linkage_confirmed true,
  step_role final_step, workup.steps captures the acid stage, all conditions null,
  no_conditions + reagent_drawn_not_written, procedure_text verbatim vs L137,
  workup.ph_target correctly null (pH 2-3 is the invention's, not this route's),
  product correctly LEFT GENERIC (matches Claims_Step 2 / Summary_Step 2 convention).

FLAGGED+FIXED: F-008 base missing -> +basic substance (base).
               F-009 acid missing -> +acid (acid), kept generic; a1_missing_compound raised.
FLAGGED OPEN:  F-010 compounds.json has no generic acid entry.

================================================================
## [2] Background_Side Reaction   -- AUDITED + CORRECTED
Re-read L147 in full (zh + en). Swept whole file for 甲醇 / 苄溴 / 甲氧基甲基.
  甲醇 as METHANOL occurs ONLY at L147 (all other 甲醇 hits are 四氢呋喃甲醇,
  tetrahydrofurfuryl alcohol - a different compound, do not confuse).
  苄溴 at L147, L182, L187; 182/187 belong to the [0024] counterfactual = OUT OF SCOPE.
  Nothing outside L147 adds to this reaction.

PATENT SAYS (L147): impurity = 2-chloro-3-methoxymethyl-4-methylsulfonylbenzoic acid.
  Level 3-5% (R=trifluoroethyl), up to 8-12% (R=2-THF-methyl).
  Mechanism: 碱性环境中 in the basic environment, the ester of the raw material undergoes
  base cleavage OR transesterification -> methanol as byproduct; methanol then reacts with
  the 苄溴基团 benzyl bromide group of the raw material.
  Consequence: hard to remove, carried into the subsequent reaction, degrades final quality.
  No temperature, time, solvent, charge or yield.

PASSES: both reactants, product identity, reaction_class, named_reaction, mechanism_type,
  scale, all conditions null, no_conditions, precursor_step Step 1 + linkage_confirmed,
  step_role side_reaction, is_complete false, procedure_text verbatim vs L147,
  product_yield_pct / product_purity_pct correctly null (3-5% and 8-12% are impurity
  proportions, not a yield and not a product purity).

FLAGGED+FIXED: F-011 base missing -> +basic substance (base).
NOT ADDED (checked, patent does not state): bromide / HBr leaving group.
NOT CAPTURABLE: impurity levels (F-002); downstream-consequence prose (no field).
NOTE: the patent names the impurity as the ACID while methanol attacks the methyl ESTER.
  The page compresses etherification + later saponification into one sentence. Recorded as
  the patent states it - the acid - since the .md is the source of truth.

================================================================
## [3] Claims_Step 1   -- AUDITED (notes enriched; no compound change)
Re-read claims 1,2,3,4 and claim 10(1) at L44/46/50/52/54/56/58/60/62/64/109/111.
Swept whole file for 酯解反应 / 三级醇 -> restated at L159,189,191,201,203,255,263
  (Summary section - same parameters, belongs to Summary records, not here).

PATENT PARAMETERS FOR STEP (1), checklist:
  SM methyl ester ................................. PRESENT
  tertiary alcohol: t-BuOH / t-amyl / 2-Me-2-pentanol PRESENT (3 solvent entries)
  "or a combination of at least two"................ MISSING -> F-013
  "preferably tert-butanol" ........................ MISSING -> F-014
  solvent 700-3500 mL per 1 mol .................... prose only in molar_ratio_text -> F-015
  SM:base molar ratio 1:(1-1.1) .................... PRESENT (molar_ratio_text)
  base: 8 named options ............................ PRESENT (8 base entries)
  "preferably sodium hydroxide" .................... MISSING -> F-014
  NaOH mass conc 30-96% ............................ PRESENT (conditions.concentration.text)
  KOH mass conc 30-96% ............................. PRESENT (same)
  temperature 25-40 C .............................. PRESENT (min_c 25 / max_c 40)
  TIME 5-12 h ...................................... MISSING -> F-012  <-- biggest
  product = the salt ............................... PRESENT
  workup empty ..................................... CORRECT (claim 10's 脱溶/水稀释/酸化/
                                                     过滤/烘干 belongs to step (2))

ROOT CAUSE of F-012: conditions.temperature has min_c/max_c but time is only a scalar
  time_h. A range cannot be stored, so the 5-12h leaked into molar_ratio_text.
  SCHEMA ASYMMETRY - affects Claims_Step 1/2 and Summary_Step 1/2 (4 records).

F-016 cross-record: Claims_Step 1 reactant_names = [ester] only;
  Summary_Step 1 reactant_names = [ester + 8 bases]. Same content, two projections.
  RULE SET: reactant_names carries role=reactant only. Claims_Step 1 complies -> no change.
  Fix Summary_Step 1 at record [53].

================================================================
## [4] Claims_Step 2   -- AUDITED (flag only, no edits from here on)
Read every claim line governing step (2): L48,66,68,70,72,74,76,78,80,82,84,86,91,93,95,97,99,101,103,105,107,113.

PATENT PARAMETER CHECKLIST FOR STEP (2):
  salt as reactant ................................ PRESENT
  alcohol = TFE or 2-THF-methanol ................. PRESENT (both)
  base = SIX named (claim 6: NaOH,KOH,NaOtBu,KOtBu,NaH,KH) PRESENT, exactly 6
       ^ NOTE: correctly SIX here, not the EIGHT of step (1). Metals excluded. Good.
  ALKALI METAL ALKOXIDE (2nd route) ............... MISSING -> F-017  <-- biggest
       only Na metal / K metal (role other) = the alkoxide's PRECURSORS, not the reagent
  salt:alcohol 1:(1.05-1.35) ...................... PRESENT (molar_ratio_text)
  salt:base 1:(1.2-1.5) ........................... PRESENT (molar_ratio_text)
  salt:alkoxide 1:(1.2-1.5) ....................... PRESENT (molar_ratio_text)
  alkali metal = Na or K .......................... PRESENT
  NaOH/KOH conc 30-96% ............................ PRESENT (conditions.concentration.text)
  addition ORDER both routes ...................... PRESENT (salt addition_profile - good catch
       by the pipeline: covers BOTH the alcohol-route and alkoxide-route orders)
  batch addition time 1-3 h ....................... prose only in addition_profile -> F-022
  solvent = MeCN/DMF/DMSO/THF ..................... PRESENT (all 4)
  "or a combination of at least two" .............. MISSING -> F-020 (not even in notes)
  solvent 700-3500 mL per mol ..................... prose only -> F-021
  acidification -> the acid ....................... PRESENT (workup.steps)
  acid = hydrochloric acid ........................ PRESENT
  pH 2-3 .......................................... workup.ph_target NULL -> F-018
  temperature -5 to 15 C .......................... PRESENT (min_c/max_c)
  TIME 3-6 h ...................................... time_h NULL -> F-019
  claim 10(2) workup: 脱溶/水稀释/酸化/过滤/烘干 ...... PRESENT, all 5 in workup.steps
  product = the acid .............................. PRESENT
  precursor_step Step 1 + linkage_confirmed ....... PRESENT and correct

NO WRONG/HALLUCINATED VALUES FOUND. All 18 compounds are claim-supported.
FLAGGED: F-017 alkoxide reagent missing | F-018 pH range | F-019 time range |
         F-020 solvent combination | F-021 solvent volume | F-022 addition time
SCHEMA ROOT CAUSE (F-012 family): temperature has min_c/max_c, but time_h, ph_target and
  addition time are all SCALARS. Every range the claims give for those leaks into prose.

================================================================
## [5] Example 1_Step 1   -- AUDITED (flag only)
Patent L280+L285/286 (procedure splits across the p08/p09 page break).
PATENT: t-BuOH 200mL; NaOH 8.8g (48%, 0.105mol) dripped in at 室温 room temp; then kettle
  25C; methyl ester 34.8g (98%, 0.1mol) poured in; 碱解反应; 微微放热 slightly exothermic;
  25C; 7h; IPC LC sodium salt 98.2%; 负压脱尽溶剂 strip solvent, used directly next step.

EVERY VALUE CORRECT: solvent 200mL, base 8.8g/105mmol/48%, SM 34.8g/100mmol/98%,
  T=25 exact, time 7h, product purity 98.2 hplc, workup 2 steps + concentration_method,
  process_control hplc + target compound, safety_notes exothermic, reactor flask,
  step_role first_step, precursor null, flags [].
  Two-stage temperature handled correctly: the 室温 stage sits in the base's
  addition_profile, the 25C in conditions.temperature. GOOD.

RECONSIDERED AND WITHDRAWN: molar_ratio_text=null is CORRECT here. The example prints
  0.1mol and 0.105mol but never states a RATIO, so there is no ratio text to carry.
  (I had over-flagged this in the earlier discarded pass - checked again, it is a pass.)

CROSS-RECORD INCONSISTENCIES FOUND FROM THIS RECORD (flagged once, listing all affected):
  F-024 named_reaction: only Ex1+Ex3 carry 'saponification'; 18 others null. Same reaction.
  F-025 reaction_class_confidence: 7 high / 13 medium across the 20 identical step-1 records.
        Does not track evidence: Ex13/Ex14 are bare cross-references and score HIGH,
        Ex5 with a full procedure scores MEDIUM.
  F-026 stirring null on all 48 example records though every example prints 开动搅拌.
  F-027 step-1 product given 100 mmol on Ex2/Ex8/Ex10 only; patent prints that figure only
        where the salt is CHARGED into step (2).
  F-023 MY OWN BUG: Background_Side Reaction has stirring.type and light_source.type set to
        "not_specified" where all 54 others are null. Introduced by my blanking routine.

================================================================
## [6] Example 1_Step 2a (alkoxide prep)   -- AUDITED (flag only)
PATENT L292/293: 50mL trifluoroethanol -> reactor; stirring started; at 室温 room temp
  5.2g sodium hydride (60%, 0.13mol) charged; stirred to complete dissolution; after
  solvent removal, SOLID sodium trifluoroethoxide obtained; 密封备用 sealed for later use.
ALL VALUES CORRECT: TFE 50mL, NaH 5.2g/130mmol/60%, product = sodium trifluoroethoxide,
  T=room_temperature, reactor=reactor (反应釜), workup 3 steps + concentration_method,
  time_h null (patent gives no time - "stirred until dissolution complete") CORRECT,
  named_reaction null CORRECT, step_role intermediate_step, flags [].
FLAGGED: F-028 (NaH role 'base' vs metals role 'reagent' across the 8 alkoxide preps)
         F-032 (this record's product feeds Step 2b but nothing links them)
NOTE: TFE is both the reactant and the neat medium here; recorded as reactant with a
  volume, which is the right call - the patent charges it by volume as the only liquid.

================================================================
## [7] Example 1_Step 2b (etherification)   -- AUDITED (flag only)
PATENT L294/295: 200mL THF -> the sodium trifluoroethoxide; stir to dissolve; kettle 5C;
  salt from step (1) (98.2%, 0.1mol) added 分八次 in EIGHT portions, total charging 3h;
  after charging 保温反应3h hold 3h. Then 负压脱溶 strip solvent; 釜残加水120mL;
  stir to dissolve; 滴加浓盐酸 conc. HCl dropwise to pH 2; 过滤、水淋洗、烘干
  filter, water rinse, dry -> 32.9g; HPLC 98.7%; 两步反应收率93.8% on the methyl ester.

EXCELLENT RECORD. Every value correct and every operation captured:
  T=5 exact, time_h=3.0 (the HOLD, correctly distinguished from the 3h ADDITION which sits
  in addition_profile), salt 100mmol/98.2%/hplc, THF 200mL, water 120mL, HCl acid role,
  product 32.9g/98.7%/hplc, yield 93.8, workup 6 steps, washes, filtration, purification,
  workup.ph_target=2.0, precursor Step 1 + linkage_confirmed, tags catalyst_class:none
  (correct - the alkoxide is the nucleophile, there is no separate base).

FLAGGED (all schema-level, no misreading):
  F-030 product_yield_pct=93.8 is a TWO-STEP yield on the methyl ester; no field says so.
        The notes DO say it explicitly - the pipeline read it right, the schema cannot hold it.
  F-031 分八次 "eight portions" has no numeric field, only addition_profile prose.
  F-032 precursor_step names Step 1 only; the alkoxide from Step 2a cannot be named.

================================================================
## [8] Example 10_Step 1   -- AUDITED (flag only)
PATENT L452: tert-amyl 50mL + tert-butanol 150mL (MIXED SOLVENT); KH 14.0g (30%,0.105mol)
  dripped in at room temp; after KH fully dissolved, vessel 25C; methyl ester 34.8g
  (98%,0.1mol); 碱解; slightly exothermic; 25C; 6h; IPC 98.2% potassium salt; strip, reuse.
ALL VALUES CORRECT. NOTABLE GOOD: the mixed solvent is captured as TWO separate solvent
  entries with their own volumes (50 + 150 mL). This is the claim-2 "combination of at
  least two" case actually occurring, and it is handled properly here - which strengthens
  F-013/F-020, since the CLAIMS records never record that combinations are permitted.
FLAGGED (instances of existing findings): F-027 product mmol=100 asserted;
  F-024 named_reaction null; F-025 confidence medium; F-026 stirring null;
  F-033 safety_notes contains raw Chinese; F-034 reactor_type wording.

================================================================
## [9] Example 10_Step 2   -- AUDITED (flag only)
PATENT L459: DMF 200mL + TFE 13.6g (99%,0.135mol) + KOH 9.9g (85%,0.15mol); 5C;
  potassium salt (98.2%,0.1mol) in 8 portions over 3h; hold 5h; strip; water 120mL;
  conc HCl to pH 3; filter, water rinse, dry -> 32.5g; HPLC 97.1%; two-step yield 91.1%.
ALL VALUES CORRECT: 7 compounds, T=5, time_h=5 (hold), addition 3h in addition_profile,
  workup 6 steps, ph_target=3.0, washes, filtration, purification, precursor Step 1.
FLAGGED: F-030 two-step yield basis; F-031 eight portions; F-034 reactor_type
  ("reaction vessel" here, "reaction flask" on Ex1, same 反应釜/反应瓶 wording).

================================================================
## [10] Example 11_Step 1  /  [11] Example 11_Step 2   -- AUDITED (flag only)
## [12] Example 12_Step 1  /  [13] Example 12_Step 2
PATENT L468 (Ex11-1): t-BuOH 200mL; sodium metal 2.4g (99%,0.105mol) at room temp; after
  it dissolved completely, 25C; methyl ester 34.8g (98%,0.1mol); exothermic; 25C; 6h;
  IPC 98.3% sodium salt.
PATENT L478 (Ex11-2): THF 130mL + 2-THF-methanol 10.8g (99%,0.105mol) + NaOtBu 11.8g
  (98%,0.12mol); 10C; sodium salt (98.3%,0.1mol) 8 portions/3h; hold 4h; water 120mL;
  conc HCl to pH 3; -> 33.0g; HPLC 96.6%; two-step yield 91.4%.
PATENT L487 (Ex12-1): t-BuOH 200mL; metallic potassium 4.1g (99%,0.105mol); 25C; ester
  34.8g (98%,0.1mol); 6h; IPC 98.1% potassium salt.
PATENT L494 (Ex12-2): DMF 130mL + 2-THF-methanol 10.8g (99%,0.105mol) + KOtBu 14.1g
  (95%,0.12mol); 10C; potassium salt (98.1%,0.1mol) 8 portions/3h; hold 4h; pH 3;
  -> 33.0g; HPLC 96.8%; two-step yield 91.8%.

ALL FOUR RECORDS: every mass, volume, mole, purity, temperature, time, pH, product mass,
  assay and yield matches the patent exactly. Ex11/Ex12 step 2 are the first two
  tefuryltrione-intermediate examples and the product identity is correct on both.
  reagent_written_not_drawn on Ex11-1/Ex12-1 is CORRECT: the scheme arrows at L465/L484
  carry only "Na" / "K" while the prose charges 金属钠 / 金属钾.

NEW FINDING F-035 (WRONG, not merely inconsistent):
  Ex11 gives sodium metal role='reagent'; Ex12 gives potassium metal role='reagent'.
  But claim 3 (L55) and [0030] (L195) BOTH list 金属钠 and 金属钾 among the 碱性物质
  basic substances for step (1). And Claims_Step 1 AND Summary_Step 1 both record those
  same two compounds with role='base'. So the file contradicts itself and the patent.
  -> should be role='base'.
F-028 REVISED after this check: in the ALKOXIDE preps the base/reagent split may be
  defensible (claim 6 = hydrides are bases; claim 7 = metals are the "alkali metal"),
  so that one is downgraded to an undocumented inconsistency rather than an error.

================================================================
## [14]-[21] Examples 13, 14, 15, 16 (step 1 delegated + step 2)   -- AUDITED (flag only)
PATENT L510 (Ex13-2): DMF 200mL + THFA 11.8g(99%,0.115) + NaOH 5.4g(96%,0.13); 5C;
  salt(98.2%,0.1mol) 8 portions/3h; hold 6h; pH3; 32.6g; 95.3%; 89.1%.
PATENT L521 (Ex14-2): DMF 200mL + THFA 11.8g(99%,0.115) + KOH 8.6g(85%,0.13); 5C;
  8/3h; hold 5h; pH3; 32.6g; 95.9%; 89.8%.
PATENT L534 (Ex15-2): DMF 160mL + THFA 11.8g(99%,0.115) + NaOH SOLUTION 17.3g(30%,0.13);
  5C; 8/2h; hold 4h; pH3; 32.6g; 94.6%; 88.4%.
PATENT L544 (Ex16-2): DMF 70mL + THFA 12.9g(99%,0.125) + KOH SOLUTION 26.1g(30%,0.14);
  5C; 8/2h; hold 4h; pH2; 32.6g; 94.8%; 88.8%.

STEP-2 RECORDS: every value correct - masses, volumes, moles, temperatures, hold times,
  addition times, pH, product mass, assay and yield. Mass balance recomputed on all four
  (mass x assay / 348.80 / 0.1mol): 89.1, 89.6, 88.4, 88.6 vs printed 89.1, 89.8, 88.4,
  88.8 - all within rounding. No wrong values.

STEP-1 RECORDS (all 4, and the same for Ex17-20): EMPTY.
  F-036 conditions_inherited=true but NOTHING inherited. Ex1's procedure is printed in
  full at L280/L285 and none of it is carried. Substrate has no mass, no mole, no purity.

F-037 base purity dropped: Ex15 and Ex16 leave purity_pct null on the 30% hydroxide
  SOLUTION. Ex13/Ex14 correctly store 96% and 85%. Ex6_Step 2 uses the identical
  "potassium hydroxide solution (30%)" wording and DOES store 30. Also affects Ex3 x2.

F-038 flag split with no evidential basis: Ex13/Ex14 carry cross_reference_unresolved;
  Ex15/Ex16 carry reagent_written_not_drawn instead. Read the four drawings directly -
  L506/L517/L531/L541 all carry the same three condition labels (THFA, NaOH|KOH, HCl).
  Nothing in the evidence explains why the flags differ.

================================================================
## [22]-[30] Examples 17, 18, 19   -- AUDITED (flag only)
PATENT L554 (Ex17-2a): 2-THF-methanol 50mL; NaH 5.2g(60%,0.13mol) at RT; stir to dissolve;
  高真空油泵负压脱溶 HIGH-VACUUM OIL PUMP strip -> solid sodium 2-THF-methoxide, sealed.
PATENT L561 (Ex17-2b): THF 200mL to the alkoxide; 5C; Na salt(98.2%,0.1mol) 8/3h; hold 3h;
  pH3; 33.1g; 97.5%; 92.5%.
PATENT L572 (Ex18-2a): 2-THF-methanol 150mL; KH 20g(30%,0.15mol); high-vacuum -> potassium
  2-THF-methoxide.  L574 (Ex18-2): THF 200mL; 5C; SODIUM salt(98.2%,0.1mol) 8/3h; hold 3h;
  pH3; 33.1g; 97.0%; 92.2%.
PATENT L585 (Ex19-2a): 2-THF-methanol 50mL; Na metal 2.8g(99%,0.12mol); high-vacuum ->
  sodium 2-THF-methoxide.  L587/592 (Ex19-2): DMSO 70mL; -5C; sodium salt 8 portions/2h;
  hold 5h; pH3; 33.4g; 95.5%; 91.5%.

ALL 9 RECORDS: every value correct. Two things done WELL and worth noting:
  1. The 高真空油泵 high-vacuum oil pump detail IS captured in workup.concentration_method
     on Ex17/18/19 2a, and correctly NOT on Ex1/2/5/8 2a which only say 脱溶. Real
     discrimination between two similar procedures.
  2. Ex18 and Ex20 pair a POTASSIUM alkoxide with a SODIUM salt, exactly as printed.
     Recorded correctly - easy thing to "tidy" wrongly and it was not.
  Arithmetic recomputed: Ex17 33.1x97.5/348.80/0.1 = 92.5 (printed 92.5); Ex18 92.1 (92.2);
  Ex19 91.4 (91.5). All clean.

NEW FINDING F-039: four naming schemes for the alkoxide-prep + etherification pair.
  Ex1/Ex17 = Step 2a + Step 2b. Ex2/Ex5 = Alkoxide Preparation + Step 2.
  Ex8 = Step 2 + Step 3 (only example whose product step is numbered 3).
  Ex18/19/20 = Step 2a + Step 2 (prep labelled a sub-step of the reaction that follows it).
INSTANCES OF EXISTING FINDINGS: F-036 (Ex17/18/19 Step 1 all empty);
  F-028 (Ex19_Step 2a sodium metal role=reagent while Ex17/18 hydrides role=base);
  F-031, F-032 (all three step-2 records).

================================================================
## [31]-[36] Examples 2 and 20   -- AUDITED (flag only)
PATENT L304 (Ex2-1): tert-AMYL alcohol 200mL (the only example using it alone); NaOH 8.8g
  (48%,0.105mol) at RT; 25C; ester 34.8g(98%,0.1mol); 7h; IPC 97.8% sodium salt.
PATENT L311 (Ex2-alkoxide): TFE 50mL; metallic sodium 2.8g(99%,0.12mol); 脱溶 (NOT the
  high-vacuum pump) -> sodium trifluoroethoxide.
PATENT L313 (Ex2-2): DMSO 70mL; -5C; salt(97.8%,0.1mol) 8/2h; hold 5h; pH2; 33.3g;
  96.7%; two-step 92.4%.
PATENT L603 (Ex20-2a): 2-THF-methanol 100mL; potassium metal 5.5g(99%,0.14mol);
  high-vacuum -> potassium 2-THF alkoxide.
PATENT L605 (Ex20-2): acetonitrile 130mL; 15C; SODIUM salt(98.2%,0.1mol) 8 portions/1h
  (the shortest addition in the patent); hold 6h; pH2; 32.6g; 97.0%; 90.8%.
ALL SIX RECORDS: every value correct.

NEW FINDING F-040 - recomputed the mass balance on ALL 20 etherifications:
  gap = (mass x assay / MW / 0.1mol) - printed yield
  +0.48 Ex9  NOT FLAGGED      +0.48 Ex2  FLAGGED
  +0.46 Ex4  NOT FLAGGED      +0.41 Ex6  FLAGGED
  +0.43 Ex8  NOT FLAGGED
  +0.43 Ex3  NOT FLAGGED
  remaining 14 examples: -0.22 to +0.02, genuinely clean.
  So the flag catches 2 of 6, and the LARGEST gap (Ex9, tied with Ex2) is unflagged.
  The six gaps are the patent's own arithmetic - the extraction copied every number
  correctly. The defect is purely in which records get the flag.

================================================================
## [37]-[52] Examples 3, 4, 5, 6, 7, 8, 9   -- AUDITED (flag only)
Read L326,332,343,350,359,366,371,380,387,399,406,415,424,426,434,440 (all 16 procedures).
EVERY MASS, VOLUME, MOLE, PURITY, TEMPERATURE, TIME, pH, PRODUCT MASS, ASSAY AND YIELD
IN ALL 16 RECORDS MATCHES THE PATENT. No wrong or invented value anywhere in this block.

Spot values confirmed against the page:
  Ex3-1 t-BuOH 70mL (smallest charge in the patent), NaOH 14g(30%,0.105), 30C, 12h (longest
        step-1 time), IPC 92.5% (lowest step-1 purity in the patent) - all correct.
  Ex4-1 NaOH 4.6g(96%,0.11mol) - the ONLY run at the 1:1.1 top of the claim-3 range - correct.
  Ex6-1 KOH 6.6g(85%,0.1mol) - the ONLY run at the 1:1.0 bottom of the range - correct.
  Ex9-1 2-methyl-2-pentanol 200mL - the only use of the third tertiary alcohol - correct.
  Ex8-3 acetonitrile, 15C, addition 1h, hold 6h - correct.

NEW FINDINGS:
F-041 Ex6_Step 2 and Ex7_Step 2 have NO water and NO hydrochloric acid in compounds[],
      while the other 18 etherifications carry both. Their own workup.steps DESCRIBES
      adding 120 mL water and conc. HCl to pH 2, and workup.ph_target=2.0 is set - so the
      operation was read and only the two chemicals were dropped. 18/20 correct.
F-042 water role split: 17 records 'solvent', Ex4_Step 2 and Claims_Step 2 'other'.
      Claims_Step 2 and Summary_Step 2 disagree with EACH OTHER on the same generic step.
F-043 alkoxide-prep flags: Ex8_Step 2 alone carries reagent_written_not_drawn; the other
      7 carry nothing. No alkoxide preparation is drawn anywhere in the patent, so the
      evidence is identical for all 8.

INSTANCES OF EXISTING FINDINGS IN THIS BLOCK:
  F-037 Ex3_Step 1 and Ex3_Step 2 base purity 30% dropped.
  F-027 Ex8_Step 1 product given 100 mmol.
  F-029 Ex5_Alkoxide tagged transformation:deprotonation (1 of 8).
  F-033 Chinese left in safety_notes on Ex5,6,7 Step 1 and in workup on Ex5_Alkoxide.
  F-040 Ex3, Ex4, Ex8, Ex9 unflagged mass-balance gaps of +0.43 to +0.48.
  F-025 Ex5-Ex9 step 1 all 'medium' confidence while Ex1-Ex4 are 'high'.

CORRECTLY FLAGGED BY THE PIPELINE (verified against the drawings, no action):
  Ex3_Step 2, Ex4_Step 2, Ex5_Step 2, Ex8_Step 3 drawing_text_conflict - the scheme draws
    the wrong counter-ion in each case; prose governs and both readings are preserved.
  Ex7_Step 1 drawing_text_conflict - arrow says NaOH, prose charges sodium tert-butoxide.

================================================================
## [53] Summary of the Invention_Step 1  /  [54] Step 2   -- AUDITED (flag only)
Read L159,189,191,193,195,197,199,201,203,255 and L168,205-248,257.
The Summary restates the claims AND adds material the claims do not have:
  - 使用时先制成水溶液 the hydroxides are MADE UP AS AQUEOUS SOLUTIONS before use ([0031],[0032])
  - worked point values for every range ([0028],[0029],[0031]-[0034],[0048]-[0051],[0054])
  - the addition-order rules ([0044],[0045]) AND the warning at [0046] that the order
    cannot be changed or the benzyl alcohol and double-attachment impurities increase.

TWO EXCELLENT CATCHES BY THE PIPELINE, verified against the page, no action:
  1. The patent's OWN TYPO is caught and preserved, not silently corrected: [0032] and
     [0039] both read 所述氢氧化钾使用时先制成氢氧化钠水溶液 - potassium hydroxide made up as an
     aqueous SODIUM hydroxide solution. Recorded as a printed inconsistency. Exactly right.
  2. WATER is a solvent on the Summary records but absent from the Claims records. That is
     not sloppiness - it is correct discrimination: only the Summary says the hydroxides
     are made up as aqueous solutions. Claims 3 and 6 give the concentration without
     saying that. Genuinely careful reading.
  3. The [0046] addition-order warning IS carried in Summary_Step 2's notes.

FINDINGS:
F-044 Summary_Step 2 has NO hydrochloric acid in compounds[], though [0053] names it and
      the record's own workup.steps says "acidified with hydrochloric acid". Claims_Step 2
      records it correctly.
F-045 Summary_Step 2 has NO alkali metal alkoxide AND no sodium/potassium metal, so one of
      the two routes the patent gives for this step has no reagent at all. Worse than
      F-017: Claims_Step 2 at least carries the two metals.
F-046 Twin records disagree on bookkeeping: Claims 1/2 are is_complete=true with no flags;
      Summary 1/2 are is_complete=false with reagent_written_not_drawn - even though the
      Summary records carry MORE information.
F-047 time_h empty on both (5-12h, 3-6h); workup.ph_target empty on Step 2 (pH 2-3).
F-048 Only the ratio and solvent-volume point-value lists survive, in Chinese inside
      molar_ratio_text. Temperature, time, concentration and pH point values are lost.
INSTANCE: F-016 confirmed - Summary_Step 1 reactant_names has 9 entries including all 8
      bases; Claims_Step 1 has 1. Same content, two projections.

================================================================
## ALL 55 RECORDS AUDITED. Findings F-001 .. F-048 in GOLDEN-DATASET-FINDINGS.xlsx.

################################################################
# VERIFICATION + CORRECTION PASS  2026-08-29
# Re-read the full examples section (L271-440) and L441-606 in Chinese, verified every
# flag against the source characters, then applied every fix with a definite patent value.

VERIFIED AT THE SOURCE BEFORE FIXING:
  L325 "14g氢氧化钠(30％，0.105mol)"          -> F-037 real
  L331 "17.3g氢氧化钠溶液(30％，0.13mol)"      -> F-037 real
  L386 "釜残加水120mL...滴加浓盐酸...酸化至2"   -> F-041 real (Ex6)
  L405 "釜残加水120mL...滴加浓盐酸...酸化至2"   -> F-041 real (Ex7)
  L468 "2.4g金属钠"  L487 "4.1g金属钾"        -> F-035 real, and L55 claim 3 lists
        金属钠/金属钾 among the 碱性物质, so 'base' is the patent's own classification
  L387 Ex6 base IS "氢氧化钾溶液(30％)" and the record already had 30 -> F-037 correctly
        excludes Ex6, so the finding is four misses and not a rule. Confirmed.

APPLIED (27 findings closed):
  F-036  8 records filled from Example 1 - the single biggest gap
  F-017/F-044/F-045  the alkoxide route given reagents on Claims and Summary step 2;
         hydrochloric acid added to Summary step 2
  F-041  water + HCl added to Ex6 and Ex7 step 2
  F-035  metals reagent -> base on Ex11/Ex12 (patent-supported, was the only WRONG value)
  F-037  30 percent strength on 4 bases
  F-040  mass_balance_implausible added to the 4 unflagged cases
  F-024/F-025  named_reaction and confidence made uniform across all 20 step-1 records
  F-027  removed the inferred 100 mmol from 3 step-1 products
  F-029  Ex5 alkoxide tag; F-042 water role; F-016 reactant_names rule
  F-033  all Chinese removed from safety_notes / workup / addition_profile
  F-034  reactor_type six values -> two, by the first vessel word printed
  F-038/F-043  two flags dropped that the corrections above made stale or inapplicable
  F-023  my own stirring.type / light_source.type bug

VERIFIED AFTER: 55 records, provenance aligned, zero schema violations, zero Chinese left
  in reviewer-facing fields, reactor_type = {flask 28, kettle 20, null 7},
  step-1 confidence all medium, step-1 named_reaction all null,
  mass_balance flags on exactly the 6 real cases.
  One deliberate a1_missing_compound remains: the generic 'acid' on Background_Step 2 (F-010).

STILL OPEN (21) - none is a misreading; each needs a schema change or a decision:
  no range fields: F-012 F-018 F-019 F-021 F-022 F-047 (time, pH, per-mole volume, addition time)
  no field at all: F-002 impurity level, F-007 prior-art refs, F-030 yield basis,
                   F-031 portion count, F-032 multiple precursors, F-026 stirring
                   (the enum has no "stated but unspecified"), F-013/F-014/F-020/F-048
                   (solvent combinations, preferred options, worked point values)
  decisions:       F-010 add generic acid to compounds.json, F-028 alkoxide reagent role,
                   F-039 step-label scheme, F-046 is_complete on the Claims/Summary twins
