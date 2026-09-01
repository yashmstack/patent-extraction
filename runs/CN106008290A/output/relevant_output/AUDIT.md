# A5 adversarial audit of CN106008290A

Four independent audits, each in a fresh context, each re-opening the page images.
None of them produced the artifact it audited.

| artifact | records | critical | major | minor | checks passed |
|---|---:|---:|---:|---:|---:|
| `compounds` | 54 | 1 | 9 | 7 | 13 |
| `patent` | 1 | 0 | 4 | 6 | 14 |
| `pathways` | 9 | 0 | 7 | 13 | 14 |
| `reactions` | 18 | 0 | 4 | 12 | 15 |
| **total** | | **1** | **24** | **38** | **56** |

## Acted on

Nothing recorded for CN106008290A. Every finding below is outstanding.

## Outstanding, by severity

These are recorded and not yet acted on. They are real and a second pass should
work through them.

### critical

1. **[compounds]** `drawings` on `sodium trifluoroethoxide`
   The record asserts that scheme (1) does not depict this substrate, and pages p02 and p04 show it drawn on the reactant side of the arrow as + CF3CH2ONa, so the annotation carries a statement about the drawing that the drawing refutes.
   > line 98: "conditions": [{"text": "MOH/M2CO3"}]
   fix: Delete the clause 'and the scheme does not depict this substrate'. On p02 (scheme (1), immediately after structure I) and on p04 (the same scheme under [0008]) the page prints '+ CF3CH2ONa' to the lef

### major

1. **[compounds]** `drawings` on `None`
   The vision read of scheme (1) on lines 49 and 98 lists one reactant and one product, while the page draws three further species: the co-reactant CF3CH2ONa left of the arrow and the by-products CH3OH and NaBr right of it; scheme (2) on lines 53 and 103 likewise omits the drawn by-product H2O.
   > line 49: "reactants": [{"smiles": "COC(=O)c1ccc(S(C)(=O)=O)c(CBr)c1Cl"
   fix: Re-read the two schemes on p02 and p04. Scheme (1) reads: I + CF3CH2ONa, over the arrow MOH/M2CO3, giving II + CH3OH + NaBr. Scheme (2) reads: II + III, over the arrow 缩合剂 and under it 碱催化剂, giving IV
2. **[compounds]** `recall` on `None`
   Sodium bromide is drawn as a by-product of scheme (1) on pages p02 and p04 and has no record in compounds.json, although A1 rule 4f requires a compound that exists only as a drawing to be extracted and reactions.json already carries it.
   > line 49: "products": [{"smiles": "CS(=O)(=O)c1ccc(C(=O)O)c(Cl)c1COCC(F)(F)F"
   fix: Add one record, identifier 'sodium bromide', role by_product, section_label Claims and Summary of the Invention, quantity all null, noted as drawing only. reactions.json has it as Summary of the Inven
3. **[compounds]** `recall` on `tembotrione`
   The final product of the patent carries purity_pct 96.3 but mass_g and yield_pct null, although the text prints an isolated mass and yield for it in all five examples and raw-compounds.json holds every one of them.
   > line 180: 干燥得到成品环磺酮(化合物IV)355.5g，纯度96.3％，收率83.9％
   fix: Keep the last populated quantity the way the scalar fields are kept: mass_g 355.5 and yield_pct 83.9 alongside purity_pct 96.3. The cause is in pipeline/finalise.py merge_compound: the guard 'v not in
4. **[compounds]** `recall` on `1,3-cyclohexanedione`
   Thirteen further records lose every printed quantity to the same merge overwrite, so a compound charged with a mass and a mole figure in five examples reads as quantity-free in the artifact.
   > line 140: 含1.2mol(117.6g)1,3-环己二酮(化合物III)
   fix: Same one-line fix as the previous finding: in merge_compound, merge quantity field by field instead of replacing the dict, so a later all-null dict cannot erase an earlier populated one. Reported sepa
5. **[compounds]** `translation` on `sodium 2,2,2-trifluoroethoxide`
   Four identifiers carry 2,2,2- locants that no Chinese line in the document prints; the only 2,2,2 in the source is inside the machine-translated EN gloss on line 129, so the artifact followed the English where it must follow the Chinese.
   > line 47: 以2-氯-3-溴甲基-4-甲磺基苯甲酸甲酯与三氟乙醇钠为反应底物
   fix: Resolve without the locants, as the sibling record 'sodium trifluoroethoxide' already does and says in its own notes ('Chinese 三氟乙醇钠 prints no locants; resolved as the sodium salt of trifluoroethanol 
6. **[compounds]** `precision` on `化合物II`
   Every isolated mass and yield of the step a intermediate sits on the unresolved local label 化合物II while all five English-named records for the same molecule are quantity-empty, and compounds-equivalence.json does not group the local label with them, so this fragmentation is the one the side channel does not record.
   > line 138: 干燥得化合物II，称重得314.8g，收率91％
   fix: Leaving 化合物II unresolved is defensible inside an example that never restates the name, but the equivalence side channel must then list it with the five named spellings, since its normaliser groups onl
7. **[compounds]** `arithmetic` on `tembotrione`
   The printed step b mass and yield fail to close in all five examples, by 2.3 to 4.6 percentage points, and the notes record the mismatch for Example 4 only.
   > line 140: 得到成品环磺酮(化合物IV)366.4g，纯度96.5％，收率86.3％
   fix: Flag all five. From 1 mol of compound II, C17H16ClF3O6S at 440.82 gives 440.82 g at 100 per cent, so 366.4 g is 83.1 per cent against a printed 86.3, 362.5 g is 82.2 against 86.0, 375.4 g is 85.2 agai
8. **[compounds]** `arithmetic` on `化合物II`
   Step a produces less than 1 mol of compound II in all five examples and step b charges 1 mol in all five, and only the Example 4 note calls the two figures inconsistent; the other four notes describe them as coming from different steps without saying they cannot both hold.
   > line 140: 取1mol上述反应所得的化合物II
   fix: State the discontinuity in all five notes. 314.8 g, 321.7 g, 311.4 g, 321.7 g and 318.3 g of C11H10ClF3O5S at 346.70 are 0.908, 0.928, 0.898, 0.928 and 0.918 mol, and each step b then takes 1 mol. rea
9. **[compounds]** `fidelity` on `sodium 2,2,2-trifluoroethoxide`
   The notes assert that the Example 2 mass and mole pair disagrees with the molecular weight the name implies, and it agrees exactly, so the artifact reports an inconsistency the document does not contain.
   > line 149: 取1.2mol(146.4g)三氟乙醇钠
   fix: Remove the claim. 146.4 divided by 1.2 is 122.0 g per mol, and CF3CH2ONa is 122.02, so the pair is consistent, exactly as the same record's Example 1, 4 and 5 notes say of 1.1mol(134.2g). A false inco
10. **[patent]** `fidelity` on `CN106008290A`
   The assignee is typed as an SME, which is neither printed on the cover sheet nor present in the biblio file that A4 rule 5 says finalise.py takes this value from.
   > line 18: （71）申请人 安徽久易农业股份有限公司
   fix: "type": "company", matching input/CN106008290A-biblio.json, with the tag corrected to assignee_type:company. 股份有限公司 on p01 says joint stock limited company and says nothing about size.
11. **[patent]** `precision` on `CN106008290A`
   2,2,2-trifluoroethanol is listed as a key starting material of this patent, but the document charges it in no step and names it only as the prior-art reagent this invention replaces.
   > line 85: 其工业制备方法主要是三氟乙醇、叔丁醇钾法制备关键中间体2-氯-3-三氟乙氧甲基-4-甲磺基苯甲酸
   fix: Drop 2,2,2-trifluoroethanol from key_starting_materials. output/compounds-sections.json confirms it is seen only in Background and Beneficial Effects, so the rollup is promoting a background reagent i
12. **[patent]** `fidelity` on `CN106008290A`
   The compound count of 54 includes three identifiers that are not distinct compounds but transcription residue, each of which is already present under its proper name.
   > line 159: 溶解在1000mL的二氯乙烷中 ... 然后水洗、减压浓缩加甲、醇打浆、过滤、干燥
   fix: 52 or fewer. output/compounds.json carries 化合物II (the document's own label for the intermediate, already recorded under four chemical names), 二氯乙烷 (already recorded as 1,2-dichloroethane) and 甲、醇 (an 
13. **[patent]** `drawings` on `None`
   The vision read of both drawn equations drops species that are printed on the page: equation (1) draws a second reactant and two byproducts, equation (2) draws a byproduct, and none of the four appear in the extracted reactants or products.
   > line 49: [IMAGE_EXTRACT: {"reactions": [{"step_id": 1, "reactants": [{"smiles": "COC(=O)c1ccc(S(C)(=O)=O)c(CBr)c1Cl", ...}], "conditions": [{"text": "MOH/M2CO3"}], ...
   fix: Equation (1) on p02 and p04 is drawn as ester I + CF3CH2ONa, arrow labelled MOH/M2CO3, giving acid II + CH3OH + NaBr. Equation (2) is drawn as II + III giving IV + H2O. Add CF3CH2ONa as a reactant of 
14. **[pathways]** `recall` on `None`
   No pathway is emitted for the Claims section, although claim 1 recites the whole two step route in words and carries both drawn schemes, and the reference run CN104292137A emits a Claims scoped pathway.
   > line 47: 步骤a：以2-氯-3-溴甲基-4-甲確基苯甲酸甲酯与三氟乙醇钠为反应底物，加入MOH或M2CO3，在反应溶剂中进行反应，获得2-氯-3-三氟乙氧甲基-4-甲確基苯甲酸
   fix: Emit a section pathway for Claims over the claim 1 steps a and b and their two drawn schemes. The exclusion originates upstream: output/00-sections.json sets contains_procedure false for Claims to avo
15. **[pathways]** `fidelity` on `Example 2_Step a`
   This step records only the etherification, but the material it isolates is 化合物II, which line 95 defines as the free benzoic acid, so the methyl ester cleavage happened in the same pot and is not recorded anywhere; the identical step in Example 1 records it with is_one_pot true and transformation:hydrolysis.
   > line 149: 取1.2mol(146.4g)三氟乙醇钠,1.2mol(67.2g)氢氧化钾,1.0mol(318g)2-氯-3-溴甲基-4-甲確基苯甲酸甲酯(化合物I)…干燥得化合物II,称重得321.7g,收率93%。
   fix: is_one_pot true with the two transformations in one_pot_steps and reaction_class from the final one, as Example 1_Step a already does. Three independent pieces of evidence: line 95 defines 化合物II as 2-
16. **[pathways]** `fidelity` on `Example 3_Step a`
   This step records only the etherification, but the material it isolates is 化合物II, which line 95 defines as the free benzoic acid, so the methyl ester cleavage happened in the same pot and is not recorded anywhere; the identical step in Example 1 records it with is_one_pot true and transformation:hydrolysis.
   > line 157: 取1.1mol(134.2g)三氟乙醇钠,1.2mol(129.6g)碳酸钠,1.0mol(318g)2-氯-3-溴甲基-4-甲確基苯甲酸甲酯(化合物I)…干燥得化合物II,称重得311.4g,收率90%。
   fix: is_one_pot true with the two transformations in one_pot_steps and reaction_class from the final one, as Example 1_Step a already does. Three independent pieces of evidence: line 95 defines 化合物II as 2-
17. **[pathways]** `fidelity` on `Example 4_Step a`
   This step records only the etherification, but the material it isolates is 化合物II, which line 95 defines as the free benzoic acid, so the methyl ester cleavage happened in the same pot and is not recorded anywhere; the identical step in Example 1 records it with is_one_pot true and transformation:hydrolysis.
   > line 165: 取1.1mol(134.2g)三氟乙醇钠,1.2mol(166.8g)碳酸钾,1.0mol(318g)2-氯-3-溴甲基-4-甲確基苯甲酸甲酯(化合物I)…干燥得化合物II,称重得321.7g,收率93%。
   fix: is_one_pot true with the two transformations in one_pot_steps and reaction_class from the final one, as Example 1_Step a already does. Three independent pieces of evidence: line 95 defines 化合物II as 2-
18. **[pathways]** `fidelity` on `Example 5_Step a`
   This step records only the etherification, but the material it isolates is 化合物II, which line 95 defines as the free benzoic acid, so the methyl ester cleavage happened in the same pot and is not recorded anywhere; the identical step in Example 1 records it with is_one_pot true and transformation:hydrolysis.
   > line 173: 取1.1mol(134.2g)三氟乙醇钠,1.2mol(28.8g)氢氧化钬,1.0mol(318g)2-氯-3-溴甲基-4-甲確基苯甲酸甲酯(化合物I),1000mL N,N-二甲基甲酰胺加入到反应器
   fix: is_one_pot true with the two transformations in one_pot_steps and reaction_class from the final one, as Example 1_Step a already does. Three independent pieces of evidence: line 95 defines 化合物II as 2-
19. **[pathways]** `arithmetic` on `Example 3_Step b`
   The step charges 1 mol of 化合物II while the preceding step isolated 311.4 g, which is 0.898 mol of the free acid, and no scale_discontinuity flag is raised, although Examples 1, 2 and 4 raise it on the same arithmetic.
   > line 159: 步骤b:取1mol上述反应所得的化合物II,溶解在1000mL的二氯乙烷中
   fix: Add scale_discontinuity to Example 3_Step b validation_flags and scale_discontinuity_in_chain to the Example 3 pathway honest_uncertainty_flags. 311.4 g / 346.70 g/mol = 0.898 mol against 1 mol charge
20. **[pathways]** `arithmetic` on `Example 5_Step b`
   The step charges 1 mol of 化合物II while the preceding step isolated 318.3 g, which is 0.918 mol of the free acid, and no scale_discontinuity flag is raised, although Examples 1, 2 and 4 raise it on the same arithmetic.
   > line 180: 步骤b：取1mol上述反应所得的化合物II，溶解在1000mL的环己烷中
   fix: Add scale_discontinuity to Example 5_Step b validation_flags and scale_discontinuity_in_chain to the Example 5 pathway honest_uncertainty_flags. 318.3 g / 346.70 g/mol = 0.918 mol against 1 mol charge
21. **[reactions]** `arithmetic` on `Example 3_Step b`
   scale_discontinuity is absent although step a of the same example isolated 311.4 g of 化合物II, which at the free acid C11H10ClF3O5S = 346.70 is 0.8982 mol, while this step charges 1 mol of that same material, a deficit of 0.1018 mol that is the largest of the five examples and larger than the 0.0721 mol deficit on which Example 2_Step b does raise the flag.
   > line 159: 步骤b:取1mol上述反应所得的化合物II,溶解在1000mL的二氯乙烷中
   fix: add 'scale_discontinuity' to validation_flags and record the comparison (step a output 311.4 g at 90％ of 1.0 mol, about 0.90 mol, against a 1 mol charge here); change no printed number
22. **[reactions]** `arithmetic` on `Example 5_Step b`
   scale_discontinuity is absent although step a of the same example isolated 318.3 g of 化合物II, which is 0.9181 mol at 346.70, while this step charges 1 mol of that material, a deficit of 0.0819 mol, larger than the 0.0721 mol deficit flagged on Example 2_Step b and Example 4_Step b.
   > line 180: 步骤b：取1mol上述反应所得的化合物II，溶解在1000mL的环己烷中
   fix: add 'scale_discontinuity' to validation_flags and record the comparison (step a output 318.3 g at 92％ of 1.0 mol against a 1 mol charge here)
23. **[reactions]** `recall` on `Example 2_Step a`
   The ester cleavage that turns 化合物I (a methyl benzoate) into 化合物II (a benzoic acid) is not recorded: is_one_pot is false, one_pot_steps is empty and reaction_class is nucleophilic_substitution, while Example 1_Step a and Summary of the Invention_Step 1 record the same procedure as one-pot with two transformations, and equation (1) as drawn on p04 and p02 writes CH3OH and NaBr as by-products, so the drawing itself says the methyl group leaves.
   > line 149: 干燥得化合物II,称重得321.7g,收率93％
   fix: record the ester cleavage in one_pot_steps and set is_one_pot true, as Example 1_Step a does, or record both readings in notes; the same applies to Example 3_Step a, Example 4_Step a and Example 5_Ste
24. **[reactions]** `fidelity` on `Summary of the Invention_Step 1`
   Two records of the same one-pot pair of transformations carry different reaction_class values on mutually contradictory readings of A2 rule 5: this record takes the class from the ether-forming substitution because it says the final transformation cannot be identified, while Example 1_Step a takes hydrolysis because it says the final transformation is the ester cleavage. Both are is_one_pot true for the identical chemistry, so a scored extractor is penalised whichever value it produces.
   > line 95: 步骤a：以2-氯-3-溴甲基-4-甲磺基苯甲酸甲酯（化合物I）与三氟乙醇钠为反应底物，加入MOH或M2CO3，在反应溶剂中进行反应，获得2-氯-3-三氟乙氧甲基-4-甲磺基苯甲酸（化合物II）
   fix: settle on one reading of rule 5 for step a and apply it to every record of that step, or state in both notes that the two records disagree and why

## Recall estimates

| artifact | items found in text | present in artifact | missing |
|---|---:|---:|---:|
| `compounds` | 43 | 39 | 4 |
| `patent` | 14 | 12 | 2 |
| `pathways` | 10 | 9 | 1 |
| `reactions` | 22 | 18 | 6 |
