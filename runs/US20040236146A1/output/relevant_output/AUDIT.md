# A5 adversarial audit of US20040236146A1

Four independent audits, each in a fresh context, each re-opening the page images.
None of them produced the artifact it audited.

| artifact | records | critical | major | minor | checks passed |
|---|---:|---:|---:|---:|---:|
| `compounds` | 44 | 0 | 6 | 11 | 10 |
| `patent` | 1 | 1 | 1 | 8 | 16 |
| `pathways` | 13 | 0 | 9 | 3 | 14 |
| `reactions` | 13 | 0 | 1 | 12 | 19 |
| **total** | | **1** | **17** | **34** | **59** |

## Acted on

Nothing recorded for US20040236146A1. Every finding below is outstanding.

## Outstanding, by severity

These are recorded and not yet acted on. They are real and a second pass should
work through them.

### critical

1. **[patent]** `fidelity` on `US20040236146A1`
   The only source for this field, input/US20040236146A1-biblio.json, says "multinational_corp", and the record says "sme", so the value was silently downgraded between input and output and Bayer CropScience AG is described as a small or medium enterprise.
   > line 18: (76) Inventor: Hansjorg Lehmann, Wutoschingen (DE)
   fix: "type": "multinational_corp" and tag "assignee_type:multinational_corp". The cause is pipeline/finalise.py ASSIGNEE_TYPE, which has no key for "multinational_corp" and whose lookup ends in .get(kind, 

### major

1. **[compounds]** `precision` on `3-bromomethyl-2-chloro-4-methylsulfonylbenzoic acid`
   The notes carry two molecular formulae and two molecular weights, none of which is printed anywhere in the patent, and this annotation is not permitted to contain formulae or molecular weights.
   > line 124: 121.3 g (88.4% of theory) of 3-bromomethyl-2-chloro4-methylsulfonyl-benzoic acid were obtained.
   fix: Delete the sentence. A1 rule 22 forbids numbers in notes that are not in the text; if the closure is worth recording, record that it closes without quoting formulae, weights or the derived 116.4 g.
2. **[compounds]** `precision` on `3-bromomethyl-2-chloro-4-ethylsulfonylbenzoic acid`
   Same defect on the Example 2 product: two molecular formulae, two molecular weights and two derived numbers (24.8 g, 95.4%) that the patent never prints.
   > line 140: 28.2 g (95.6% of theory) of 3-bromomethyl-2-chloro-4-ethylsulfonylbenzoic acid were obtained.
   fix: Delete the formulae, the molecular weights and the derived masses; keep only the statement that the printed yield reproduces.
3. **[compounds]** `fidelity` on `dibenzoyl peroxide`
   mass_g 2.8 is a computed total (0.7 g plus three further 0.7 g portions). The string 2.8 appears nowhere in the document, and A1 rule 12 forbids computing a quantity.
   > line 140: At room temperature, 17.6 g of N-bromosuccinimide and 0.7 g of dibenzoyl peroxide were added and the mixture was subsequently heated to reflux. After in each ca
   fix: Set mass_g to 0.7, the one charge the text states, and leave the four-portion addition profile described in notes. The per-portion record already lives in reactions.json.
4. **[compounds]** `precision` on `3-bromomethyl-2-chloro-4-methylsulfonylbenzoic acid`
   The record carries the isolated mass 121.3 g and the yield 88.4% of Example 1 but is typed role other, so a yield sits on a compound the artifact does not call a product, against A1 rule 13.
   > line 124: 121.3 g (88.4% of theory) of 3-bromomethyl-2-chloro4-methylsulfonyl-benzoic acid were obtained.
   fix: role should be product. The merge took role from the Novel Compounds of Formula II fragment and the quantity from Example 1; the surviving role must be the one that supports the surviving quantity.
5. **[compounds]** `fidelity` on `3-bromomethyl-2-chloro-4-methylsulfonylbenzoic acid`
   is_section_product is true while section_label is the one section that explicitly excludes this compound, and three of the record's four note fragments state is_section_product is false.
   > line 110: excluding the compound 3-bromomethyl-2-chloro4-methylsulfonylbenzoic acid.
   fix: Either carry section_label Example 1, the section whose product this is and whose mass and yield the record holds, or set is_section_product false to agree with the surviving section_label. As it stan
6. **[compounds]** `precision` on `None`
   Three pairs of records are the same substance under a longer and a shorter spelling, and in each pair the shorter spelling is both the identifier of one record and an alias of the other, yet compounds-equivalence.json is an empty object, so the fragmentation is recorded nowhere.
   > line 53: The invention relates to a process for preparing 3-bromomethylbenzoic acids by brominating the corresponding 3-methylbenzoic acids. It further relates to certai
   fix: Add the three pairs to compounds-equivalence.json. Do not merge the records; the side channel exists so that deliberate fragmentation is recorded rather than undetected, and an empty file asserts ther
7. **[patent]** `precision` on `US20040236146A1`
   Page 1 prints no (73) Assignee at all, only (76) Inventor, yet the record asserts an assignee with no marker anywhere in patent.json that the value comes from a register scrape rather than from the face of the document.
   > line 18: (76) Inventor: Hansjorg Lehmann, Wutoschingen (DE)
   fix: Keep the assignee, since the register fact is real, but make patent.json carry the caveat that the biblio file carries. The honesty currently lives only in biblio_note in an input file that no consume
8. **[pathways]** `schema` on `Background_Step 1`
   components carries three non-skeleton species, including the oxidizing agent that A3 rule 12 names explicitly as a thing components must not contain.
   > line 55: WO 99/06339 discloses a process for preparing substituted benzyl bromides by brominating the corresponding methyl aromatics in the presence of azocarboxylic est
   fix: ["methyl aromatics", "substituted benzyl bromides"] - the reaction record already carries azocarboxylic esters and azonitriles with role reagent and oxidizing agent with role oxidant on compounds[]
9. **[pathways]** `schema` on `Background_Step 2`
   components includes the radical initiator, which the reaction record itself gives role reagent, not reactant.
   > line 55: EP-A 0 292 944 describes the preparation of methyl 3-bromomethyl-2-chloro-4-methylsulfonylbenzoate by radical initiator-induced bromination of methyl 2-chloro-3
   fix: ["methyl 2-chloro-3-methyl-4-methylsulfonylbenzoate", "methyl 3-bromomethyl-2-chloro-4-methylsulfonylbenzoate"]
10. **[pathways]** `schema` on `Claims_Step 1`
   components includes N-bromosuccinimide and the radical initiator, both role reagent on the reaction record, neither contributing the carbon skeleton.
   > line 154: with N-bromosuccimide in the presence of a radical initiator, where, in formulae I and II
   fix: ["3-methylbenzoic acid of formula I", "3-bromomethylbenzoic acid of formula II"]
11. **[pathways]** `schema` on `Claims_Step 2`
   components includes elemental bromine, which the reaction record gives role reagent.
   > line 175: which comprises brominating a 3-methylbenzoic acid of formula I [drawing, formula (I)] with elemental bromine and irradiation with a photolamp
   fix: ["3-methylbenzoic acid of formula I", "3-bromomethylbenzoic acid of formula II"]
12. **[pathways]** `schema` on `Process Conditions_Step 1`
   components includes N-bromosuccinimide, the radical initiator and bromine, all role reagent on the reaction record.
   > line 87: In process variant A), it is appropriate to initially charge a compound of the formula I with N-bromosuccinimide (NBS) and radical initiator in solvent, and the
   fix: ["compound of the formula I", "compound of the formula II"]
13. **[pathways]** `schema` on `Process Conditions_Step 2`
   components includes bromine, role reagent on the reaction record.
   > line 89: In process variant B), it is appropriate to initially charge a compound of the formula I in solvent and then, after heating under irradiation with a photolamp, 
   fix: ["compound of the formula I", "compound of the formula II"]
14. **[pathways]** `schema` on `Summary of the Invention_Step 1`
   components includes N-bromosuccinimide and the radical initiator, both role reagent on the reaction record.
   > line 69: A) N-bromosuccimide in the presence of a radical initiator, or
   fix: ["3-methylbenzoic acids of the formula I", "3-bromomethylbenzoic acids of the formula II"]
15. **[pathways]** `schema` on `Summary of the Invention_Step 2`
   components includes bromine, role reagent on the reaction record.
   > line 71: B) elemental bromine and irradiation with a photolamp,
   fix: ["3-methylbenzoic acids of the formula I", "3-bromomethylbenzoic acids of the formula II"]
16. **[pathways]** `fidelity` on `Example 1_Step 2`
   time_h is 2.0 for a run the text describes as 3 h of bromine metering under irradiation plus a further 2 h, while the parallel Example 2 step summed its stated intervals to 5.0, so the two examples are measured on different clocks.
   > line 130: Under irradiation with a 300 W lamp, II g of bromine were gradually metered in over 3 h, and the mixture boiled under reflux. After a further 2 h of irradiation
   fix: 5.0, or 2.0 kept with an explicit note that only the post-addition interval is counted, applied the same way to Example 2_Step 1. Root cause is conditions.time_h in reactions.json; pathways.json copie
17. **[reactions]** `recall` on `Process Conditions_Step 1`
   Not one of the six solvents [0014] names is carried as a compound on either Process Conditions record, although both records emit solvent_class tags derived from those very solvents and the parallel Claims records do carry their claimed solvents with role solvent.
   > line 83: It has been found that the solvents chlorobenzene and acetonitrile are advantageous for process variant A), and the solvents chlorobenzene, methylene chloride a
   fix: Add chlorobenzene and acetonitrile with role solvent to Process Conditions_Step 1 and chlorobenzene, methylene chloride and 1,2-dichloroethane to Step 2, the way Claims_Step 1 and Claims_Step 2 alread

## Recall estimates

| artifact | items found in text | present in artifact | missing |
|---|---:|---:|---:|
| `compounds` | 44 | 44 | 0 |
| `patent` | 13 | 11 | 2 |
| `pathways` | 12 | 12 | 0 |
| `reactions` | 13 | 13 | 5 |
