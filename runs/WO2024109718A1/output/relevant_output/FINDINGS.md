# What is wrong with WO2024109718A1

Produced by annotating the patent by hand, against the scanned pages rather than
against anyone's OCR. Every item below is a defect in the **patent**, not in the
annotation. The annotation records them and changes nothing.

- 79 reactions extracted, of which 67 carry at least one flag
- 137 unique compounds, 23 pathways
- 65 discrepancies raised by the page-vision pass

## Flags raised, by kind

| flag | count | what it means |
|---|---:|---|
| `no_conditions` | 58 | no reaction conditions stated at all |
| `reagent_written_not_drawn` | 7 | a reagent in the procedure appears on no arrow |
| `reagent_drawn_not_written` | 7 | a reagent on an arrow appears in no procedure |
| `cross_reference_unresolved` | 3 |  |
| `a1_missing_compound` | 2 |  |
| `missing_product` | 1 |  |

## The headline findings

No hand-written analysis exists for WO2024109718A1. The generated sections above and below are complete; this section is not, and is omitted rather than filled with another patent's findings.

## Everything the page-vision pass raised

- **[p01.png]** The abstract states the method comprises any one of the following steps but names no reagents, while the two drawn arrows also carry no reagents, so nothing on this page says how either transformation is effected.
  - drawing: Two bare arrows, no reagents above or below either.
  - text: 本发明提供一种制备环磺酮的方法，其特征在于，包括如下的任意一个步骤。
- **[p01.png]** Neither drawn product on the front page is cyclosulfonone itself; both are intermediates, although the title and abstract present the page as a method for preparing cyclosulfonone.
  - drawing: A benzoic acid (v) and its 3-oxocyclohex-1-en-1-yl ester (v'), each still carrying the SO2CH3 and CH2OCH2CF3 groups.
  - text: 环磺酮的制备方法和中间体 / METHOD FOR PREPARING CYCLOSULFONONE, AND INTERMEDIATES
- **[p03.png]** Paragraph [0006] says the route has 11 steps, but only 11 structures and 11 arrows are drawn on this page with the first arrow starting from 3-chloro-2-methylaniline; the count of drawn arrows is 11, so this is consistent, but the prose refers to the route as a whole ('上述方法'), which may include material on the preceding page.
  - drawing: 11 arrows drawn on this page, from 3-chloro-2-methylaniline to the final 2-aroylcyclohexane-1,3-dione
  - text: 上述方法一共有11步 (the above method has 11 steps in total)
- **[p03.png]** The prose criticises an aluminium trichloride catalyst in the Friedel-Crafts acetylation, but no AlCl3 is written above or below the CH3COCl arrow in the drawing.
  - drawing: CH3COCl only above the arrow
  - text: 后处理产生大量含有催化剂三氯化铝的废水 (work-up produces waste water containing the catalyst aluminium trichloride)
- **[p03.png]** The final rearrangement arrow carries no reagent in the drawing, while such a step normally requires a cyanide or base catalyst; nothing is written, so nothing is recorded.
  - drawing: bare arrow, no reagents above or below
  - text: no corresponding reagent named in the prose on this page
- **[p04.png]** The generic schemes (v) and (v') carry no reagents on the arrow, while their specific counterparts (v-1) and (v'-1) do.
  - drawing: Scheme (v) and scheme (v') have bare arrows; scheme (v-1) has H2O above / CO below and scheme (v'-1) has CO above / cyclohexane-1,3-dione below.
  - text: [0012] says only that steps (v) and (v') are 'respectively the following steps', without naming any reagent.
- **[p04.png]** Paragraph [0013] promises steps (i) to (iv) but only step (i) is drawn on this page.
  - drawing: One scheme, labelled (i).
  - text: [0013]: 如下所示的(i)～(iv)中任意一个或两个以上的中间体制备步骤 (any one or more of the intermediate preparation steps (i) to (iv) shown below).
- **[p04.png]** Step (i) is drawn as a bromination but no brominating agent appears anywhere on the page.
  - drawing: Bare arrow; Br appears in the product only.
  - text: No reagent stated on this page.
- **[p05.png]** The three schemes at the top of the page carry no reagents on their arrows, while the corresponding (i')-(iv') schemes lower on the same page do.
  - drawing: Schemes (ii), (iii), (iv) show bare arrows between the same pairs of structures.
  - text: [0014] introduces the (i')-(iv') schemes as the specific form of steps (i)-(iv), and those arrows carry Br2, H2O2, 溴代试剂 and CF3CH2OM.
- **[p05.png]** The bottom [0016] scheme draws five structures joined by four bare arrows and names no reagent for any step.
  - drawing: Four unlabelled arrows.
  - text: [0014] and [0015] name Br2, H2O2, a brominating reagent (bromine, NBS, or HBr with H2O2) and CF3CH2ONa/CF3CH2OK for the same four transformations.
- **[p05.png]** Step (i) of the (i)-(iv) list is not present on this page.
  - drawing: The page opens mid-list with scheme (ii).
  - text: [0014] refers to steps (i) to (iv) as a complete set; step (i) must appear on the preceding page.
- **[p06.png]** The brominating agent in the [0017] scheme is written in Chinese on the arrow rather than as a formula, and the prose in [0018] enumerates the options.
  - drawing: 溴代试剂 above the third arrow
  - text: [0018] 溴代试剂为溴素、N-溴代丁二酰亚胺、或者溴化氢与双氧水的组合，优选为溴素
- **[p06.png]** Third structure of schemes (vi) and (vi-1) is drawn as an ester with nothing attached to the ester oxygen; no prose on this page names that intermediate.
  - drawing: Ar-C(=O)-O with a bare O atom
  - text: nothing on this page identifies the group on that oxygen
- **[p06.png]** Neither the two-step/one-pot distinction stated in [0020] nor the step labels are marked on the drawings themselves beyond the (vi)/(vi') tags.
  - drawing: unlabelled dotted arrows throughout schemes (vi) and (vi')
  - text: [0020] 其中步骤(vi′)以分离中间体酯化合物的分步方式实施、或以不分离中间体酯化合物的一锅法方式实施。
- **[p08.png]** Paragraphs [0049]-[0052] list the R1/R2 pairs in the reverse of the order the corresponding structures are drawn after [0053].
  - drawing: (I) = CH3 + SCH3, (II) = CH3 + SO2CH3, (III) = CH2Br + SO2CH3, (IV) = CH2OCH2CF3 + SO2CH3
  - text: [0049] CF3CH2OCH2 + CH3SO2 (matches IV), [0050] BrCH2 + CH3SO2 (matches III), [0051] CH3 + CH3SO2 (matches II), [0052] CH3 + CH3S (matches I)
- **[p08.png]** The [0054] scheme arrow carries no reagent at all, while the sentence it illustrates says only 'can be prepared by the following route'. The reagent appears only in the repeated scheme under [0055].
  - drawing: bare arrow from 式（VI） to 式（I）
  - text: [0055] names 式(VI) and 溴素 (bromine) as the starting materials
- **[p08.png]** The position of the newly introduced Br in formula (I) is fixed only by the drawing; the prose never states which ring position is brominated.
  - drawing: Br enters the ring vertex adjacent to Cl and para to SCH3 (the upper-left vertex, previously unsubstituted)
  - text: [0054] and [0055] give no position
- **[p09.png]** The first scheme's reagents appear only in the drawing; the prose that introduces it names no reagent at all.
  - drawing: NaNO2 and CH3SNa above the arrow, HCl below it
  - text: [0059] only says the compound of formula (VI) can be prepared by known methods described in e.g. CN106631941A
- **[p09.png]** The catalyst and solvent described in prose for the formula (I) to formula (II) oxidation are not drawn on either of its two schemes.
  - drawing: third scheme carries only H2O2 above the arrow; second scheme carries nothing
  - text: [0063] tungstate/metatungstate/vanadate/metavanadate salts, preferably sodium tungstate dihydrate, as catalyst; [0064] glacial acetic acid or formic acid as solvent
- **[p09.png]** The bromination of formula (VI) to formula (I) is described in prose on this page but is not drawn anywhere on it.
  - drawing: no scheme for formula (VI) to formula (I)
  - text: [0056] bromine is added dropwise to the compound of formula (VI) to give the compound of formula (I)
- **[p10.png]** The arrow in the first drawing carries no reagent, while the prose immediately after it names the brominating reagent.
  - drawing: bare arrow from 式（II） to 式（III）
  - text: [0068] 上述路线以式(II)化合物和溴代试剂为原料; [0070] names 溴素, N-溴代丁二酰亚胺, or HBr + H2O2
- **[p10.png]** The arrow in the third drawing carries no reagent, and no reagent for the III to IV step is written anywhere on this page.
  - drawing: bare arrow from 式（III） to 式（IV）
  - text: [0074] only says the compound of formula (IV) can be prepared by the following route; details presumably continue on the next page
- **[p10.png]** The initiators and solvents in [0071] and [0072] appear nowhere in any drawing on the page.
  - drawing: no initiator or solvent labels on any arrow
  - text: [0071] BPO, AIBN as initiators; [0072] dichloromethane, dichloroethane, carbon tetrachloride as solvents
- **[p11.png]** The catalyst, ligand and acid-binding agent required by the prose for the (v-1) carbonylation are not drawn on the scheme.
  - drawing: Arrow carries only H2O above and CO below.
  - text: [0082] charges 式(IV) compound, water, an acid-binding agent (缚酸剂), a catalyst, a ligand and a first solvent, then introduces CO.
- **[p11.png]** The first scheme draws the alkoxide only as the generic CF3CH2OM; the prose names the two specific salts.
  - drawing: CF3CH2OM above the arrow.
  - text: [0075]/[0076] specify 三氟乙醇钠 or 三氟乙醇钾, i.e. CF3CH2ONa or CF3CH2OK.
- **[p11.png]** Solvent for the 式(III) to 式(IV) step is stated in prose but absent from the scheme.
  - drawing: No solvent written above or below the arrow.
  - text: [0078] tetrahydrofuran, 1,4-dioxane or diethyl ether, preferably anhydrous THF.
- **[p12.png]** The prose specifies a palladium catalyst, a phosphine ligand, an acid-binding agent and a solvent for this carbonylation, but the drawn arrow carries only CO above and cyclohexane-1,3-dione below.
  - drawing: above arrow: CO; below arrow: cyclohexane-1,3-dione only
  - text: [0083]-[0087]: noble metal (preferably PdCl2) catalyst, phosphine ligand, acid-binding agent, first solvent
- **[p12.png]** Cyclohexane-1,3-dione is drawn as a co-reactant below the arrow but is not named anywhere in the prose on this page.
  - drawing: cyclohexane-1,3-dione structure below the arrow
  - text: [0090] describes only a carbonyl-insertion reaction converting formula (IV) into the ester of formula (VIII)
- **[p13.png]** The unnumbered paragraph above the first scheme names acetone cyanohydrin as the preferred catalyst for the rearrangement, but no catalyst is written on the rearrangement arrow in the drawing.
  - drawing: bare arrow from the enol ester (3rd structure) to the 2-aroylcyclohexane-1,3-dione (4th structure), no text above or below
  - text: 优选使用氰类催化剂，特别优选使用丙酮氰醇作为催化剂
- **[p13.png]** [0094] describes the (IV) to (V) transformation as proceeding by CO carbonyl insertion, but the scheme after [0096] draws that step with no CO or catalyst written on the arrow.
  - drawing: 式（IV）aryl bromide to 式（V）benzoic acid over a bare arrow labelled （v）
  - text: 上述(v-1)和(v′－1)的反应中，列举了通过CO插羰的方式
- **[p14.png]** Paragraph [0099] announces intermediate steps (i) to (iv), but only steps (i) and (ii) are drawn on this page.
  - drawing: two schemes, labelled (i) and (ii)
  - text: 如下(i)～(iv)中任意一个或两个以上的中间体制备步骤
- **[p14.png]** The reagents drawn on the arrows of schemes (v-1) and (v'-1) are not written anywhere in the prose on this page.
  - drawing: H2O above / CO below for (v-1); CO above / cyclohexane-1,3-dione structure below for (v'-1)
  - text: [0098] only says the more specific embodiments of these steps are as described above (前文所述), giving no reagents on this page
- **[p14.png]** Steps (i) and (ii) are drawn with bare arrows carrying no reagents at all.
  - drawing: unlabelled solid arrows
  - text: no reagents given in [0099]
- **[p15.png]** Paragraph [0100] promises steps (i') through (v') but only four primed schemes are drawn on this page.
  - drawing: (i'), (ii'), (iii'), (iv') only; the (iv') scheme is closed with a full-width period, so the sequence appears to end here.
  - text: 上述(i)～(iv)可以是如下所示的(i')～(v')步骤
- **[p15.png]** Paragraph [0100] refers to unprimed steps (i) to (iv), but only (iii) and (iv) are drawn on this page; (i) and (ii) are on an earlier page.
  - drawing: schemes (iii) and (iv) appear at the top of the page, continuing from the previous page
  - text: 上述(i)～(iv)
- **[p16.png]** Neither scheme labels any arrow with a reagent, solvent, catalyst or condition, and the only prose on the page does not describe any step, so nothing on this page can be cross-checked between drawing and text.
  - drawing: Nine (first scheme) and seven (second scheme) bare arrows with no text above or below any of them.
  - text: Only [0102], which announces that the steps follow, without naming any of them.
- **[p16.png]** The two schemes drawn one after the other under 或 differ in length; the difference is drawn but not commented on anywhere on this page.
  - drawing: First scheme: aryl bromide ether -> carboxylic acid -> acid chloride -> enol ester (three arrows). Second scheme: aryl bromide ether -> enol ester (one arrow).
  - text: Nothing on this page distinguishes the two routes; only the character 或 ("or") separates them.
- **[p17.png]** The brominating agent is named in the prose but drawn only as a generic Chinese label on the arrow.
  - drawing: 溴代试剂 above the row-2 arrow of scheme 1 (illegible in scheme 2)
  - text: [0103] 溴代试剂为溴素、N-溴代丁二酰亚胺、或者溴化氢与双氧水的组合，优选为溴素
- **[p17.png]** CF3CH2OM is drawn as a generic reagent; the prose defines M.
  - drawing: CF3CH2OM above the arrow in both schemes
  - text: [0103] CF3CH2OM为CF3CH2ONa或CF3CH2OK
- **[p17.png]** Acetone cyanohydrin appears only on the drawing, never in the prose on this page.
  - drawing: 丙酮氰醇 above the last arrow of scheme 1
  - text: nothing on this page mentions 丙酮氰醇
- **[p17.png]** Scheme 1 makes the benzoic acid and its acid chloride as isolated intermediates; scheme 2 goes from the aryl bromide straight to the enol ester with CO plus cyclohexane-1,3-dione. The two routes are offered as alternatives with 或 and the page prose does not describe either sequence in words.
  - drawing: two different carbonylation/esterification sequences
  - text: no prose description of either sequence on this page
- **[p18.png]** The bromination scheme shows only Br2 over the arrow; the prose adds a solvent that is not drawn.
  - drawing: Br2
  - text: [0111] 400g dichloromethane as solvent, around 10 degrees C, then a 32% NaOH quench and washes
- **[p18.png]** The oxidation scheme shows only H2O2 over the arrow; the prose adds a catalyst and a solvent that are not drawn.
  - drawing: H2O2
  - text: [0115] 1.91 g sodium tungstate dihydrate, 600 mL glacial acetic acid, 80 degrees C, 224 g of 23% hydrogen peroxide
- **[p19.png]** The first scheme labels the reagent generically while the prose names two specific brominating systems.
  - drawing: 溴代试剂 (brominating agent) above the arrow, nothing below it
  - text: [0119] bromine (溴素) 52.8 g with benzoyl peroxide 3.58 g in 1,2-dichloroethane; [0120] N-bromosuccinimide 64.1 g with benzoyl peroxide 3.58 g in carbon tetrachloride
- **[p19.png]** The initiator and solvent given in the prose are not drawn on the first scheme.
  - drawing: no initiator or solvent shown above or below the arrow
  - text: 过氧化苯甲酰 (benzoyl peroxide) initiator; 1,2-二氯乙烷 or 四氯化碳 as solvent
- **[p20.png]** The scheme labels the arrow with only H2O and CO, while the prose gives a full palladium carbonylation charge.
  - drawing: H2O above the arrow, CO below the arrow
  - text: [0128] water, triethylamine, PdCl2 catalyst, ligand 1,4-bis(diphenylphosphino)butane, solvent 1,4-dioxane, CO at about 1-4 MPa, 80℃, about 12 h
- **[p21.png]** The reagent above the third arrow of the [0133] scheme cannot be read; the corresponding prose names acetone cyanohydrin.
  - drawing: [illegible] label above the third arrow
  - text: [0135] 往上述得到的式(VIII)化合物溶液中加入0.1mL丙酮氰醇 (0.1 mL acetone cyanohydrin)
- **[p21.png]** Triethylamine and the dioxane solvent are written in the prose but not drawn anywhere in the [0133] scheme.
  - drawing: second arrow carries only the drawn cyclohexane-1,3-dione
  - text: [0134] 0.5g 1,3-环己二酮溶于15mL二氧六环中，加入0.44g三乙胺
- **[p21.png]** The prose prints the formula label with an internal space where the drawing does not.
  - drawing: 式（VIII）
  - text: [0134] 得到式(V III)化合物的溶液
- **[p22.png]** The first scheme draws only CO and cyclohexane-1,3-dione; the triethylamine, palladium catalyst and dioxane solvent from the text are not drawn.
  - drawing: CO above the arrow, cyclohexane-1,3-dione below it
  - text: [0138] also lists 三乙胺27.83g, 双[(4-N,N-二甲氨基)苯基]二叔丁基膦二氯化钯3g and 溶剂二氧六环250g
- **[p22.png]** The second scheme draws only CO, cyclohexane-1,3-dione and acetone cyanohydrin; the triethylamine, PdCl2, dppb ligand and dioxane from the text are not drawn.
  - drawing: CO above the arrow, cyclohexane-1,3-dione and acetone cyanohydrin below it
  - text: [0143] also lists 三乙胺37.95g, PdCl2催化剂0.4g, 配体1,4-双(二苯基膦)丁烷3.98g and 溶剂1,4-二氧六环300g
- **[p22.png]** The second scheme draws no cyclohexane-1,3-dione quantity and shows the dione as a co-reagent, but paragraph [0143] never states a charge of cyclohexane-1,3-dione for the one-pot run.
  - drawing: cyclohexane-1,3-dione is a reagent below the arrow
  - text: [0143] lists formula (IV), triethylamine, PdCl2, ligand, dioxane and acetone cyanohydrin, with no mass given for cyclohexane-1,3-dione
- **[p24.png]** The catalyst and phosphine ligand required by claim 3 for steps (v-1) and (v'-1) are not drawn on any arrow.
  - drawing: Arrow for (v-1) carries only H2O above and CO below; arrow for (v'-1) carries only CO above.
  - text: [权利要求 3]: the reaction of step (v-1) or (v'-1) is carried out in the presence of a noble metal catalyst and a phosphine ligand or a salt thereof.
- **[p24.png]** The claim 1 schemes carry no reagents at all, while the claim 2 schemes for the same two transformations do.
  - drawing: Claim 1 arrows (v) and (v') are bare; claim 2 arrows (v-1) and (v'-1) carry H2O/CO and CO.
  - text: [权利要求 2]: steps (v) and (v') are respectively the following steps, i.e. the claim 1 steps are the generic form of the claim 2 steps.
- **[p24.png]** Cyclohexane-1,3-dione appears as an explicit reactant only in the claim 2 version of the step.
  - drawing: Scheme (v'-1) draws 式（IV） + cyclohexane-1,3-dione; scheme (v') draws 式（IV） alone.
  - text: Neither claim names cyclohexane-1,3-dione in prose; it appears only in the drawing.
- **[p25.png]** Steps (i) to (iv) are drawn with bare arrows carrying no reagents, while the prose of claim 5 promises the steps 'shown below' without naming any reagent either; the reagent Br2 appears only in the redrawn step (i') under claim 6.
  - drawing: arrows in (i)-(iv) are unlabelled; the arrow in (i') carries Br2 above it
  - text: claim 5 text names no reagents; claim 6 text says the steps are 'each independently the following steps' and then defers entirely to the drawing
- **[p25.png]** Claim 6 as printed depends on claim 4, but the steps (i) to (iv) it refers to are introduced in claim 5.
  - drawing: n/a
  - text: 根据权利要求4所述的方法，所述步骤(i)~(iv)分别独立地为以下步骤：
- **[p26.png]** Scheme (ii') and the claim 8 scheme draw H2O2 as the oxidant for SCH3 to SO2CH3, but no prose on this page names the oxidant.
  - drawing: H2O2 above the arrow
  - text: nothing about the oxidant on this page
- **[p26.png]** Scheme (i')-equivalent first arrow: the claim 8 scheme draws Br2 for the ring bromination, but no prose on this page defines that reagent.
  - drawing: Br2 above the first arrow
  - text: nothing about the ring-bromination reagent on this page
- **[p26.png]** The claim 7 scheme carries no reagents at all, while the claim 8 scheme adds them; claim 8 is the narrowing dependent claim, so this is expected rather than a conflict.
  - drawing: claim 7 arrows bare, claim 8 arrows labelled Br2 / H2O2 / 溴代试剂 / CF3CH2OM
  - text: claim 8 recites 所述中间体制备步骤如下 (the intermediate preparation steps are as follows)
- **[p27.png]** Schemes (vi) and (vi′) carry no reagent text on any arrow, while their redrawn counterparts (vi-1) and (vi′-1) on the same page do.
  - drawing: (vi) and (vi′): all arrows bare. (vi-1): H2O above and CO below the first arrow. (vi′-1): CO above the first arrow.
  - text: The prose of claims 9 and 10 on this page names no reagent at all; it only says the step may be run stepwise with isolation of the intermediate ester or as a one-pot reaction.
- **[p27.png]** The cyclohexane-1,3-dione partner is drawn as an explicit co-reactant only in (vi′-1); in (vi), (vi′) and (vi-1) it appears without ever being drawn on the reactant side.
  - drawing: (vi′-1) shows '+ cyclohexane-1,3-dione' before the arrow; the other three schemes do not.
  - text: No mention of cyclohexane-1,3-dione anywhere in the text on this page.
- **[p27.png]** The text refers to step (vi′) and step (vi′-1) as the ones that may be run one-pot, but the last paragraph of claim 10 mentions only (vi′-1), leaving (vi-1) without an equivalent statement.
  - drawing: Both (vi-1) and (vi′-1) pass through the isolable ester intermediate.
  - text: 其中步骤(vi′-1)以分离中间体酯化合物的分步方式实施、或以不分离中间体酯化合物的一锅法方式实施。 - only (vi′-1) is named.
- **[p28.png]** The four scheme rows (i) to (iv) claimed in claim 12 carry no reagent labels at all on their arrows; reagents appear only in the preferred variants (i') to (iv') below.
  - drawing: Bare arrows in (i)-(iv); Br2, H2O2, 溴代试剂 and CF3CH2OM only in (i')-(iv').
  - text: Claim 12 describes (i)-(iv) only as 如下所示的(i)～(iv)中任意一个或两个以上步骤 without naming reagents.
- **[p28.png]** The reagent cation M in CF3CH2OM is undefined on this page.
  - drawing: CF3CH2OM above the arrow of (iv').
  - text: No definition of M appears in the prose on this page.
