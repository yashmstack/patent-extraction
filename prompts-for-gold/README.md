# Prompts for building the gold set

Eight prompts, run in order, per patent. Odd numbers build gold `reactions.json`, even
numbers build gold `compounds.json`.

    PHASE 1 - the COUNT: does the file hold everything the patent describes?
      1-reactions-identification.md      read the patent, count the reactions
      2-reactions-reconciliation.md      reconcile against reactions.json, flag
      3-compounds-identification.md      read the patent, list the compounds
      4-compounds-reconciliation.md      reconcile against compounds.json, flag

    PHASE 2 - the CONTENT: is every field of every record right?
      5-reactions-record-verification.md   every field of every reaction record
      6-compounds-record-verification.md   every field of every compound record

    PHASE 3 - the FINAL CHECK: is it actually gold?
      7-reactions-final-gold-check.md      re-derive every field, correct as you go
      8-compounds-final-gold-check.md      re-derive every field, correct as you go

## How the phases differ

**Phase 1 fixes the count.** The identification pass reads the patent and never opens
the extraction output. That independence is the whole value: two automated runs that
agree tell you nothing, and once you have seen the answer you cannot unsee it. The
reconciliation pass then matches **by identity, never by number**, and flags.

**Phase 2 fixes the content.** One record at a time, in file order, and for EACH record
the whole `.md` is read again end to end, not only the lines the record cites. Each
record is checked twice before moving on, and the whole file is swept once more at the
end. Flag only.

**Phase 3 decides.** The earlier passes looked for problems. This one assumes nothing:
it walks every field of every record, asks where the answer comes from, whether an
empty field is empty for a reason, and whether a filled value is actually right. It is
the only pass that corrects as it goes, and the only one that ends with a plain yes or
no.

Phases 1 and 2 flag and stop. Fixing happens only after review. That order is what
stops a bad correction going into the ground truth.

## The rules, learned the hard way

**Never open the extraction output during an identification pass.** In one session the
same model produced counts of 48, 54 and 56 depending on what it had seen. Only the
uncontaminated numbers meant anything.

**Reconcile by identity, never by number.** Two files can hold the same count and
disagree about half of it. `DMF` and `N,N-dimethylformamide` are one compound.

**Never treat the pipeline's behaviour as correct.** It is the thing being measured,
and it is not smart enough to be a standard. Look up what a field is DEFINED to hold,
so the gold fills it correctly rather than by guess, but never conclude a value is
absent for a good reason just because the pipeline left it out.

**A step told twice covers itself.** Where the claims and the summary both record one
step, a value present on one is not missing from the other. Read them together. This
holds across the whole gold, reactions and compounds alike.

**Prose is not capture.** A value sitting in `notes` or `molar_ratio_text` is invisible
to anything downstream. "Recoverable in the prose" is not the same as "not lost".

**Never withdraw a finding because the schema has no field.** Flag it. If it matters,
add the field to the gold data, since the gold has to be more complete than the
pipeline rather than equally lossy. Check first whether a general field such as
`analytics` already fits: it takes any measurement, and was wrongly called a schema gap
when it was simply unused.

**A `null` is not evidence the patent is silent.** Checking is the only way to tell an
absent value from an uncaptured one. This is where information is lost most often.

**Two kinds of field, checked two different ways.** A field the PATENT must answer is
checked against the page. A field the LLM GENERATES is checked against the chemistry,
and against how the rest of the file treats the same situation. A generated label can
be chemically defensible and still wrong, if two identical records carry different
values.

**List every item individually.** In a reconciliation table, if there are 43 matches,
show 43 rows. Grouping rows into ranges hides exactly what the reader came to check.
