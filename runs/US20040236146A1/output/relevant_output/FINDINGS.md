# What is wrong with US20040236146A1

Produced by annotating the patent by hand, against the scanned pages rather than
against anyone's OCR. Every item below is a defect in the **patent**, not in the
annotation. The annotation records them and changes nothing.

- 13 reactions extracted, of which 5 carry at least one flag
- 44 unique compounds, 13 pathways
- 15 discrepancies raised by the page-vision pass

## Flags raised, by kind

| flag | count | what it means |
|---|---:|---|
| `no_conditions` | 5 | no reaction conditions stated at all |

## The headline findings

No hand-written analysis exists for US20040236146A1. The generated sections above and below are complete; this section is not, and is omitted rather than filled with another patent's findings.

## Everything the page-vision pass raised

- **[p01.png]** The drawing and the abstract prose use different typography for the same two variable groups, superscript in the drawing and subscript in the text.
  - drawing: R with a raised superscript 1 on the ring, and SO2R with a raised superscript 2
  - text: R with a lowered subscript 1 and R with a lowered subscript 2, in 'where R1 is fluorine chlorine or bromine, and R2 is (C1-C4)alkyl'
- **[p01.png]** The abstract names formula II as a class of '3-bromomethylbenzoic acids', but the drawn ring bears two further substituents beyond the acid and the bromomethyl group, so the name is a partial description of the drawn structure rather than a full one.
  - drawing: benzene bearing COOH at C1, R1 at C2, CH2Br at C3 and SO2R2 at C4, with C5 and C6 unsubstituted
  - text: '3-bromomethylbenzoic acids of the formula II', and the title (54) 'METHOD FOR PRODUCING 3-BROMOMETHYLBENZOIC ACIDS'
- **[p01.png]** The starting material is named in the prose but is not drawn anywhere on this page, so there is no drawn scheme to check the bromination against.
  - drawing: only the product formula II is drawn; no arrow, no reagent and no starting structure appear on the page
  - text: 'by brominating the corresponding 3-methylbenzoic acids'
- **[p02.png]** Paragraph [0019] is cut off by the page break, so the workup reagent the caller asked about is simply not on this page.
  - drawing: No drawing bears on this. There are only two drawings on the page and both sit in the left column, well above [0019].
  - text: [0019] ends mid-sentence at 'When the bromination is effected by process variant' and the column goes blank below it. The strings 'bisulfate' and 'bisulfite' do not occur anywhere on p02. Whichever of the two i
- **[p02.png]** The same reagent is spelled two different ways on this one page.
  - drawing: No drawing bears on this; neither formula I nor formula II depicts a reagent.
  - text: [0007] prints 'N-bromosuccimide'; [0016] prints 'N-bromosuccinimide (NBS)'. Recorded rather than silently unified: zh keeps each as printed.
- **[p02.png]** A hyphen is missing from two compound names, in a pattern (the hyphen before a locant that follows 'methyl'/'chloro') that recurs.
  - drawing: Formula II puts the sulfonyl at the ring carbon two positions clockwise from R1, i.e. at C4 counting from the carboxyl carbon, which is what the hyphenated form of the name asserts.
  - text: [0002] prints '3-bromomethyl-2-chloro4-methylsulfonylbenzoic acid' and [0003] prints '2-halo-3-methyl4-alkylsulfonylbenzoic acids'. Both are as-printed misprints on the page itself, verified on the pixels, not 
- **[p02.png]** Cross-check of the two drawn structures against the prose that introduces them: no disagreement found.
  - drawing: Formula I carries CH3 at C3 and formula II carries CH2Br at the same C3, with HOOC at C1, R1 at C2 and SO2R2 at C4 unchanged between them, so the drawn pair differ only by H to Br at the benzylic carbon.
  - text: [0004] and [0005] describe exactly that, preparing '3-bromomethylbenzoic acids of the formula II' 'by brominating 3-methylbenzoic acids of the formula I', and [0003] names the pair as 2-halo-3-methyl-4-alkylsul
- **[p03.png]** Both examples name the starting material with the sulfone substituent written backwards relative to the drawn formula, the example titles and the rest of the patent.
  - drawing: Formulae (I) and (II) both draw SO2R2 attached to C4 through sulfur, with R2 an alkyl group carried on that sulfur. With R2 = CH3 that group is methylsulfonyl (CH3-SO2-); with R2 = C2H5 it is ethylsulfonyl (C2H
  - text: [0027] prints '2-chloro-3-methyl4-sulfonylmethylbenzoic acid', [0031] prints '2-chloro-3-methyl-4-sulfonylmethylbenzoic acid' and [0033] prints '2-chloro-3-methyl-4-sulfonylethylbenzoic acid'. 'sulfonylmethyl' 
- **[p03.png]** The workup reagent is named as a sulfate in one place and a sulfite everywhere else.
  - drawing: Nothing is drawn for the workup; no drawing on this page depicts any reagent, so the drawings cannot settle it.
  - text: The unmarked paragraph at the top of the left column (tail of the general workup description) prints 'sodium bisulfate solution'. [0027] and [0033] both print '100 ml of a 2% sodium bisulfite solution'. Sodium 
- **[p03.png]** N-bromosuccinimide is misspelled in claim 6 but spelled correctly in the description.
  - drawing: Not drawn. NBS appears nowhere as a structure on this page.
  - text: Claim 6 prints 'with N-bromosuccimide in the presence of a radical initiator' (no n before the -imide), while [0027] and [0033] both print 'N-bromosuccinimide'. Confirmed at 7x. The claim as printed names a dif
- **[p03.png]** The radical initiator is misspelled in the description but spelled correctly in the claims.
  - drawing: Not drawn.
  - text: [0027] prints '6.6 g of azoisobutyroniltrile'; claim 7 on the same page prints 'azoisobutyronitrile'. Confirmed at 7x in both places. Recorded as printed in zh, corrected in en.
- **[p03.png]** The bromine charge in Example 1 variant B is printed as letters, not digits, so it carries no numeric value.
  - drawing: Not drawn. No quantity appears in any drawing on this page.
  - text: [0031] prints 'Under irradiation with a 300 W lamp, II g of bromine were gradually metered in over 3 h'. Two capital-I letterforms with full serifs, unambiguously not digit ones at 8x magnification. No other pa
- **[p04.png]** Claim 20 narrows R2 to a single carbon count using a notation the rest of the page does not use.
  - drawing: The formula (II) drawing carries only the variable label SO2R2 and says nothing about the size of R2.
  - text: Claim 19 defines R2 as (C1-C4)alkyl, while dependent claim 20 writes it as (C2)alkyl, a one-member range written as a bare (C2) rather than as (C2-C2)alkyl or as 'ethyl'. The value is inside the parent range, s
- **[p04.png]** The compound excluded by claim 19 is the R1 = chlorine, R2 = methyl member, and claim 20 then claims R1 = chlorine with R2 = (C2)alkyl.
  - drawing: Not addressable from the drawing; both R1 and R2 are open variables.
  - text: Claim 19 excludes 3-bromomethyl-2-chloro-4-methylsulfonyl-benzoic acid, i.e. the R2 = methyl member. Claim 20 keeps R1 = chlorine but sets R2 = (C2)alkyl, which sits outside the disclaimer. Recording this as an
- **[p04.png]** Parallel claim series 8-12 and 14-18 are not exact mirrors.
  - drawing: n/a
  - text: Claim 10 names acetonitrile as the second solvent, claim 16 names methylene chloride. Both were magnified and both readings are certain, so the asymmetry is in the printed document, not in the reading.
