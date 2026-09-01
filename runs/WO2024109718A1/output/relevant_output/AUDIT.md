# A5 adversarial audit of WO2024109718A1

Four independent audits, each in a fresh context, each re-opening the page images.
None of them produced the artifact it audited.

| artifact | records | critical | major | minor | checks passed |
|---|---:|---:|---:|---:|---:|
| `compounds` | 137 | 0 | 13 | 10 | 14 |
| `patent` | 1 | 0 | 1 | 9 | 13 |
| `pathways` | 27 | 1 | 8 | 6 | 12 |
| `reactions` | 71 | 0 | 6 | 15 | 20 |
| **total** | | **1** | **28** | **40** | **59** |

## Acted on

Nothing recorded for WO2024109718A1. Every finding below is outstanding.

## Outstanding, by severity

These are recorded and not yet acted on. They are real and a second pass should
work through them.

### critical

1. **[pathways]** `drawings` on `Claims pathway ksm CSc1cccc(Cl)c1C -> tembotrione via Claims`
   Claim 9 and claim 10 draw step (vi) as four arrows from the aryl bromide (aryl bromide -> benzoic acid -> benzoyl chloride -> enol ester -> tembotrione), but the pathway carries it as a single step (IV)+CO+H2O -> tembotrione, so the benzoic acid, the benzoyl chloride and the enol ester are absent from intermediates and chain_length is 5 where the page draws 8 arrows.
   > line 616: [权利要求 10] 根据权利要求9所述的方法，其中步骤(vi)、和(vi′)分别为如下步骤：
   fix: Split Claims_Step (vi) into the four arrows drawn on p27 so the pathway carries 8 steps and adds CS(=O)(=O)c1ccc(C(=O)O)c(Cl)c1COCC(F)(F)F, CS(=O)(=O)c1ccc(C(=O)Cl)c(Cl)c1COCC(F)(F)F and CS(=O)(=O)c1c

### major

1. **[compounds]** `fidelity` on `式(V)化合物`
   The record for the formula (V) carboxylic acid is role product yet carries mass_g 1.5, which is the amount charged as a REACTANT in Example 8, while both yields printed for it as a product (81.13% and 67.57%) are dropped, and the record's own notes assert the opposite of what it emits.
   > line 493: 得到式(V)化合物，收率81.13％，熔点155-157℃。
   fix: yield_pct: 81.13 (Example 6, line 493) with the 67.57% of Example 7 (line 506) recorded in notes; mass_g should not carry the Example 8 charge of 1.5 g on a product record.
2. **[compounds]** `fidelity` on `hydrochloric acid`
   mass_g records the mass of a 5.1% aqueous solution as though it were the mass of HCl charged, overstating the reagent by roughly twentyfold.
   > line 428: 在20℃下将5.1％盐酸1165g加入到四口瓶中
   fix: Either leave mass_g null and keep "1165 g of 5.1% hydrochloric acid" in notes, or record the solution strength in a dedicated field. The notes already say the value is the solution mass; the numeric f
3. **[compounds]** `fidelity` on `NaNO2`
   mass_g is the mass of a 20% aqueous solution, not of NaNO2 (about 50.3 g of NaNO2 is contained).
   > line 428: 在0℃进一步滴加20％NaNO2水溶液251.41g
   fix: mass_g null with the solution charge in notes, or a field that distinguishes solution mass from solute mass. Same judgement call as the hydrochloric acid finding.
4. **[compounds]** `fidelity` on `CH3SNa`
   mass_g is the mass of a 20% aqueous solution, not of sodium methanethiolate (about 54.6 g contained).
   > line 433: 称量20％CH3SNa水溶液273g和32％NaOH水溶液26.62g置于另一四口烧瓶中
   fix: mass_g null with the solution charge kept in notes.
5. **[compounds]** `fidelity` on `NaOH`
   mass_g is the mass of a 32% aqueous solution, not of NaOH (about 8.5 g contained).
   > line 433: 称量20％CH3SNa水溶液273g和32％NaOH水溶液26.62g置于另一四口烧瓶中
   fix: mass_g null with the solution charge kept in notes.
6. **[compounds]** `fidelity` on `hydrogen peroxide`
   mass_g is the mass of a 23% aqueous solution, not of H2O2 (about 51.5 g contained); the contained value is what makes the patent's own stated molar ratio of 2-3 come out right.
   > line 453: 升温至80℃，滴加23％的双氧水224g
   fix: mass_g null with the solution charge kept in notes. 146 g of formula (I) is 0.580 mol; 224 g of 23% H2O2 is 1.51 mol, ratio 2.6, inside the 2-3 the patent states at line 275, which confirms 224 g is t
7. **[compounds]** `translation` on `compound of formula (VI)`
   The identifier is the English of the EN convenience line; the patent prints only the Chinese 式(VI)化合物, which is carried by a SECOND record, so one compound occupies two records with two different join keys.
   > line 433: 分层，收集有机层，蒸馏，得到式(VI)化合物。
   fix: One record with identifier 式(VI)化合物 as the Chinese prints it, English as an alias. If the split is kept, it must appear in compounds-equivalence.json, and it does not.
8. **[compounds]** `translation` on `compound of formula (A)`
   Same defect for the Markush parent: the English rendering of the EN line is a separate record from the Chinese 式(A)所示的化合物, and neither is listed in the equivalence file.
   > line 624: [权利要求 11] 下式(A)所示的化合物：
   fix: One record keyed on the Chinese as printed, English as an alias.
9. **[compounds]** `precision` on `palladium(II) chloride / PdCl2 / PdCl₂`
   One catalyst occupies three records under three spellings, with three different masses attached (0.5 g, 0.4 g, 0.4 g), and compounds-equivalence.json does not list the group, so the fragmentation is undetected rather than recorded.
   > line 493: PdCl₂催化剂0.4g
   fix: Add the three-way group to compounds-equivalence.json. The subscript variant PdCl₂ differs from PdCl2 only in Unicode and is the clearest case.
10. **[compounds]** `precision` on `cyclohexane-1,3-dione / 1,3-cyclohexanedione / O=C1CCCC(=O)C`
   One molecule occupies three records: the vision-read name, the Chinese-derived name, and the bare SMILES, all cross-referenced in aliases but absent from the equivalence file.
   > line 525: 1,3-环己二酮29.41g
   fix: Add the group to compounds-equivalence.json.
11. **[compounds]** `precision` on `式(VIII)化合物 / 式(VIII)的酯化合物 / (VIII)酯化合物`
   The formula (VIII) ester occupies three records because the patent spells its label three ways; the 80% yield sits on only one of them and the equivalence file records none of the three.
   > line 525: 70℃烘干固体，得到(VIII)酯化合物，收率为80％。
   fix: Add the group to compounds-equivalence.json.
12. **[compounds]** `precision` on `CS(=O)(=O)c1ccc(Br)c(Cl)c1COCC(F)(F)F and nine other SMILES-`
   Ten records are keyed on a raw SMILES string read from the drawings and each duplicates a compound that another record keys on its formula label, so a benchmark counts these molecules twice; none of the ten pairs appears in compounds-equivalence.json.
   > line 233: [IMAGE_EXTRACT: {"molecules": [{"smiles": "CSc1ccc(Br)c(Cl)c1C", ...}, {"smiles": "CS(=O)(=O)c1ccc(Br)c(Cl)c1COCC(F)(F)F", ...}]}]
   fix: Keep the drawing-only records (A1 rule 4f requires them) but list every SMILES/label pair in compounds-equivalence.json so the duplication is recorded rather than silent.
13. **[compounds]** `drawings` on `式(A)所示的化合物`
   The formula (A) drawing is legible on page p07 (a benzene bearing Br, Cl, R1 and R2 on four consecutive ring positions) but the vision read returned an empty molecule list, and the artifact records the scaffold as unavailable rather than as read off the page.
   > line 219: [IMAGE_EXTRACT: {"molecules": []}]
   fix: Keep resolved:false, but record in notes what page p07 actually draws: Br at C1, Cl at C2, R1 at C3, R2 at C4 of a benzene ring. With the four R1/R2 pairs at lines 223-229 that scaffold enumerates exa
14. **[patent]** `fidelity` on `WO2024109718A1`
   Two reactions are counted as pilot scale when every example in the patent is a bench run in a four-necked flask or a laboratory autoclave, and the two so counted are smaller than Example 1, which is counted as lab.
   > line 443: 将式(VI)化合物100.75g、400g二氯甲烷置于四口圆底烧瓶中，于10℃左右滴加溴素98.4g。
   fix: Reclassify Example 2_Step 1 and Example 3_Step 1 in reactions.json from pilot to lab (Example 3 at line 453 is likewise 146 g in a 四口烧瓶), so the recomputed rollup reads lab 15, pilot 0. Example 1 at l
15. **[pathways]** `drawings` on `Claims pathway ksm CSc1cccc(Cl)c1C -> tembotrione via Claims`
   Step (vi') is drawn on p27 as two arrows (aryl bromide plus 1,3-cyclohexanedione and CO -> enol ester, then enol ester -> tembotrione) but the pathway records one step, so the enol ester intermediate that the page draws is missing from intermediates.
   > line 605: [权利要求 9] 根据权利要求7或8所述的方法，进一步包括如下步骤：
   fix: Add the enol ester CS(=O)(=O)c1ccc(C(=O)OC2=CC(=O)CCC2)c(Cl)c1COCC(F)(F)F as the fifth intermediate and record the rearrangement as a separate terminal step.
16. **[pathways]** `drawings` on `Summary of the Invention pathway ksm CSc1cccc(Cl)c1C -> temb`
   The scheme at [0021] on p06 draws benzoic acid -> benzoyl chloride -> enol ester, but Summary of the Invention_Scheme Step 7 merges those two arrows into acid plus 1,3-cyclohexanedione -> enol ester, so the benzoyl chloride is missing from the pathway's intermediates even though the same drawing read in the Claims section did record it.
   > line 149: [0021] (8)根据上述(7)所述的方法，其中步骤(vi)和(vi′)分别为如下步骤：
   fix: Split Summary of the Invention_Scheme Step 7 at the drawn benzoyl chloride and insert CS(=O)(=O)c1ccc(C(=O)Cl)c(Cl)c1COCC(F)(F)F into intermediates, matching the Claims read of the identical scheme.
17. **[pathways]** `recall` on `None`
   p17 carries two complete drawn routes for [0102] separated by 或; only the first (via the benzoic acid and the benzoyl chloride, nine arrows) became Preparation Routes and General Embodiments_Scheme Step 1-9, and the second (aniline through to tembotrione with CO plus 1,3-cyclohexanedione straight to the enol ester, seven arrows) has no scheme derived pathway at all.
   > line 409: [0102] 在更具体的实施方式中，本发明新方法包括如下步骤：
   fix: Emit a second Scheme pathway for the 或 alternative drawn on p17: aniline -> (VI) -> (I) -> (II) -> (III) -> (IV) -> enol ester -> tembotrione, 7 steps.
18. **[pathways]** `linkage` on `Example 3 pathway ksm 式(I)化合物 -> 式(II)化合物`
   Example 3 consumes 式(I)化合物, the exact identifier string Example 2 produces, and the same exact match holds for Example 4 (式(II)化合物), Example 5 (式(III)化合物), Examples 6, 7, 9, 10 and 11 (式(IV)化合物) and Example 8 (式(V)化合物), yet every one of these precursor_step values is null, so the worked route is fragmented into nine one-step pathways and no pathway carries the example yields.
   > line 453: [0115] 将式(I)化合物146g、二水合钨酸钠1.91g和冰醋酸600mL加入到四口烧瓶中，升温至80℃，滴加23％的双氧水224g，通过高效液相色谱监测反应完成后，停止反
   fix: Set the cross section precursor_step form the A2 prompt defines (Example 2::Step 1 and so on) so the examples assemble into one pathway; A2 rule 24 is satisfied because the identifier strings match ex
19. **[pathways]** `linkage` on `Example 2 pathway ksm 式(VI)化合物 -> 式(I)化合物`
   Example 1 prepares the same compound Example 2 consumes, but the two records spell it in different languages (product 'compound of formula (VI)' against ksm '式(VI)化合物'), the link is left null, and compounds-equivalence.json records only the phosphine ligand pair, so this fragmentation is not captured in the side channel either.
   > line 439: [0110] 实施例2 式(I)化合物的制备
   fix: Use the Chinese identifier 式(VI)化合物 on both, link Example 2 to Example 1, and add the pair to compounds-equivalence.json if the two spellings are kept.
20. **[pathways]** `precision` on `all 27 records, 40 of the 71 reactions they project`
   A3 rule 12 restricts components to the step's reactants plus its product and names reagents, oxidants, bases, catalysts and solvents as excluded, but components carries them on 40 of 71 steps, and on Background_Scheme B Step 4 it also carries the two byproducts 卤仿 and sodium chloride, which are neither reactant nor product.
   > line 76: [0006] 然而，上述方法一共有11步，步骤多；乙酰氯发生的F-C反应刺激性大，后处理产生大量含有催化剂三氯化铝的废水，后面的次氯酸钠卤仿反应也是在水相进行，反应过程中会生成卤仿并产生大量含有氯化钠的废水，污染严重；另外，分子中通过F-C
   fix: Rebuild components as the identifiers whose compounds[] role is reactant plus the is_product entry, dropping every reagent, oxidant, base, catalyst, solvent and byproduct.
21. **[pathways]** `precision` on `12 reactions, among them Claims_Step (vi), Example 5_Step 1,`
   A3 rule 11 requires compounds to be copied verbatim from the reaction record and forbids re-classifying, but 12 reactions carry roles in pathways.json that do not exist in reactions.json for the same step: reactant becomes intermediate on Claims_Step (vi) and (vi') and Example 1_Step 1, other becomes byproduct, initiator, quenching_agent or workup_agent, and solvent becomes wash.
   > line 483: [0124] 在-5～5℃将60％氢化钠9.2g溶于80mL无水四氢呋喃中，往该溶液中滴加三氟乙醇24g的20mL无水四氢呋喃溶液，滴加完毕后，进一步滴加式(III)化合物83g的400mL无水四氢呋喃溶液，滴加时控制反应物温度不超过15℃
   fix: Copy compounds[] byte for byte from the reaction record; if the roles are wrong, fix them in reactions.json so both artifacts agree.
22. **[pathways]** `recall` on `the four Claims pathways and the two Summary of the Inventio`
   These six pathways start from the compound of formula (VI), which the patent itself says has to be prepared from 3-chloro-2-methylaniline, so the chain does not reach a purchasable starting material, yet none of them carries truncated_chain while the Example 2 pathway with the very same ksm does.
   > line 252: [0059] 作为原料的式(VI)化合物可以参照例如专利文献CN106631941A等中记载的公知方法通过如下反应制备：
   fix: Add truncated_chain to the four Claims pathways and the two Summary of the Invention pathways.
23. **[reactions]** `drawings` on `Summary of the Invention_Scheme Step 7`
   Scheme (vi) on page p06 is drawn as five structures and four arrows, the third structure being the acid chloride, but this record merges arrows two and three into one acid-plus-dione step, so the acid chloride and its own step exist nowhere in the Summary section; the record's notes assert the opposite of what the page shows, calling it 'one arrow read as two halves'.
   > line 141: {"step_id": 2, "reactants": [{"smiles": "CS(=O)(=O)c1ccc(C(=O)O)c(Cl)c1COCC(F)(F)F"}], "conditions": [], "products": []}, {"step_id": 3, "reactants": [], "condi
   fix: split into two records, acid to acid chloride and acid chloride plus dione to enol ester, as the Preparation Routes section already does for the same route (Scheme Step 7 and Scheme Step 8) and as the
24. **[reactions]** `recall` on `Claims_Step (vi)`
   A2 rule 5d requires one record per arrow for an overview scheme; this single record carries a four-arrow scheme, so three transformations get no record, and the acid, acid chloride and enol ester, which are the scheme's own intermediates, are given role 'reactant' alongside the true starting material.
   > line 616: [权利要求 10] 根据权利要求9所述的方法，其中步骤(vi)、和(vi′)分别为如下步骤：
   fix: four records in drawing order, each with its own reactant and product; the intermediates must be a product of one record and a reactant of the next, not co-reactants of one. The record's notes give a 
25. **[reactions]** `recall` on `Claims_Step (vi')`
   Same defect on the shorter claim scheme: two arrows drawn on p27, one record emitted, and the enol ester is listed as a reactant of the step that makes it.
   > line 616: [权利要求 10] 根据权利要求9所述的方法，其中步骤(vi)、和(vi′)分别为如下步骤：
   fix: two records: ArBr plus dione under CO to the enol ester, then the enol ester to tembotrione
26. **[reactions]** `recall` on `Preparation Routes and General Embodiments_Step 7`
   The paragraph prints a reaction time of 10 to 20 h and the record leaves time_h null, so a printed condition is absent from the artifact.
   > line 320: 通入CO，在80～120℃、优选80～90℃反应10～20h
   fix: record the printed time; time_h holds one float, so 10.0 with the 10 to 20 h range spelled out in notes, rather than a silent null
27. **[reactions]** `vocabulary` on `Example 7_Step 1`
   Examples 6 and 7 are the same palladium hydroxycarbonylation of the formula (IV) bromide, differing only in ligand and solvent, but Example 6 is classed other_cross_coupling and Example 7 other; the two records' notes reach opposite conclusions on identical chemistry.
   > line 506: 向高压釜中加入式(IV)化合物40g、水20g、三乙胺26.49g、PdCl2催化剂0.4g、配体1,3-双(二苯基膦)丙烷3.95g、溶剂四氢呋喃400g
   fix: one value on both records
28. **[reactions]** `precision` on `Summary of the Invention_Scheme Step 1`
   Seventeen records in the Summary, Claims and Preparation Routes sections carry SMILES strings in product_name and in compounds[].identifier instead of names, so the same molecule appears as CSc1ccc(Br)c(Cl)c1C here and as 式(I)化合物 in the Preparation Routes and Example records, and compounds-equivalence.json binds neither pair.
   > line 103: [IMAGE_EXTRACT: {"reactions": [{"step_id": 1, "reactants": [{"smiles": "CSc1cccc(Cl)c1C", ...}], "conditions": [], "products": [{"smiles": "CSc1ccc(Br)c(Cl)c1C"
   fix: the label the patent gives the structure, 式(I)化合物, or the IUPAC name the Background records already use for named structures; A2 rule 8 says the SMILES belongs on the A1 compound record's aliases. Sta

## Recall estimates

| artifact | items found in text | present in artifact | missing |
|---|---:|---:|---:|
| `compounds` | 114 | 137 | 0 |
| `patent` | 22 | 22 | 0 |
| `pathways` | 29 | 25 | 4 |
| `reactions` | 76 | 71 | 5 |
