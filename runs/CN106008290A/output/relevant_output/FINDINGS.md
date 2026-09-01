# What is wrong with CN106008290A

Produced by annotating the patent by hand, against the scanned pages rather than
against anyone's OCR. Every item below is a defect in the **patent**, not in the
annotation. The annotation records them and changes nothing.

- 18 reactions extracted, of which 18 carry at least one flag
- 51 unique compounds, 9 pathways
- 11 discrepancies raised by the page-vision pass

## Flags raised, by kind

| flag | count | what it means |
|---|---:|---|
| `molar_mass_inconsistent` | 9 | a stated mass/mole pair implies a molecular weight that is not the named compound's |
| `no_conditions` | 6 | no reaction conditions stated at all |
| `mass_balance_implausible` | 5 | stated product mass cannot be reconciled with the stated input moles and yield |
| `scale_discontinuity` | 4 | a step charges more material than the previous step produced |
| `a1_missing_compound` | 4 |  |
| `missing_product` | 2 |  |
| `missing_reactant` | 2 |  |

## The headline findings

No hand-written analysis exists for CN106008290A. The generated sections above and below are complete; this section is not, and is omitted rather than filled with another patent's findings.

## Everything the page-vision pass raised

- **[p02.png]** Equation (1) writes the two byproducts explicitly; the prose of step a mentions no byproduct at all.
  - drawing: product II is accompanied by + CH3OH + NaBr
  - text: 在反应溶剂中进行反应，获得2-氯-3-三氟乙氧甲基-4-甲磺基苯甲酸 (nothing about CH3OH or NaBr)
- **[p02.png]** The bromide byproduct in the drawing is specifically the sodium salt, while the text lets M be any of three alkali metals.
  - drawing: NaBr
  - text: M为Li、Na、K离子中的一种
- **[p02.png]** MOH/M2CO3 is set with a subscript in the drawing but flat in the prose, so the prose reading of the stoichiometry is not typographically determined.
  - drawing: MOH/M2CO3 above the arrow, with a subscript 2 on M
  - text: 加入MOH或M2CO3 and, in claim 3, MOH/M2CO3, both printed without subscripts
- **[p02.png]** Equation (2) writes water as a byproduct of the condensation; the prose of step b does not.
  - drawing: product IV is accompanied by + H2O
  - text: 在反应溶剂中进行缩合反应，获得环磺酮 (no byproduct named)
- **[p02.png]** The locants of the trifluoroethoxy group come only from the drawing; the Chinese name omits them.
  - drawing: CH2OCH2CF3, i.e. a (2,2,2-trifluoroethoxy)methyl group
  - text: 三氟乙氧甲基, with no locants on the trifluoroethoxy
- **[p04.png]** Scheme (1) draws by-products that the prose does not mention.
  - drawing: + CH3OH + NaBr on the product side of equation (1)
  - text: [0007] names only compound II as the product of step a
- **[p04.png]** Scheme (2) draws water as a by-product that the prose does not mention.
  - drawing: + H2O on the product side of equation (2)
  - text: [0009] names only huanhuangtong (compound IV) as the product of step b
- **[p04.png]** The prose names the step b substrate 1,3-环己二酮 while the drawing shows the ring without any numbering.
  - drawing: a six-membered carbocycle with two ketone oxygens in a 1,3 relationship as drawn
  - text: 1,3-环己二酮 (1,3-cyclohexanedione), compound III
- **[p04.png]** The background section describes a prior-art route in prose only; no prior-art scheme is drawn on this page.
  - drawing: both drawn schemes are the invention's route, introduced as 具体化学反应式 for steps a and b
  - text: [0002] describes the trifluoroethanol / potassium tert-butoxide plus acyl chlorination and rearrangement route as the existing industrial method
- **[p05.png]** Example 1 step a runs at a temperature outside the range the summary gives for step a.
  - drawing: no drawing on this page
  - text: [0014] gives step a as 0-5℃; [0025] holds step a at 30℃ for 5 hours.
- **[p05.png]** The prose names two different oxidation-state forms of the key intermediate.
  - drawing: no drawing on this page
  - text: [0021] calls the key intermediate 2-氯-3-三氟乙氧甲基-4-甲磺基苯甲酸 (the free acid), while [0025] starts from the methyl ester 2-氯-3-溴甲基-4-甲磺基苯甲酸甲酯 and gives compound II with no name.
