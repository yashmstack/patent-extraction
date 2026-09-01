# Prompt 5: verify every record in reactions.json against the patent

Phase 2. Run this only after Prompts 1 and 2, when `reactions.json` already contains
every reaction the patent describes. Phase 1 fixed the COUNT. This pass fixes the
CONTENT of each record.

The goal: every record is rich, correct, and carries everything the patent says about
that reaction, so the file can be called gold.

---

## The loop

1. **Open `output/reactions.json`** and read the schema that is actually present, so
   you know what fields exist and what each one is defined to hold.

2. **Take one reaction object**, starting at index 0 and working in the order the file
   records them: 0, 1, 2, 3 and so on. Keep the index visible in everything you report,
   so neither of us loses count.

3. **Read that object and understand it.** What reaction does it say this is? What
   reactants, products, conditions, workup? Understand it properly before you go
   looking.

4. **Then, holding that record in mind, read the patent `.md` again, line by line, end
   to end.** If the patent is 600 lines, read 600 lines. Read carefully, as defined
   below under "What 'read carefully' actually means", and do that on every pass.

   Read it **properly and in depth, with that record held in mind the whole way
   through**, asking of every line: does this say anything about my reaction? Not
   skimming for the compound name. A line can be about your record without naming it,
   because it says "the salt prepared in step (1)", or "the same procedure as Example
   1", or draws it on an arrow, or fixes what R stands for. Read for anything RELATED
   to the record, not only for direct mentions.

   **Do not read only the lines the record cites.** A record's evidence is scattered:
   the charge is in the example, the range is in the claims, the reason is in the
   summary, the structure is in a drawing, and the definition of a symbol is somewhere
   else again. Reading only the citation is how information gets missed.

5. **Compare the record against everything the patent says about that reaction:**
   - Is every value correct? If the patent says 100 and the record says 10, flag it.
   - Is anything in the patent about this reaction missing from the record?
   - Is anything in the record that the patent does not support, invented or
     hallucinated?
   - Is the record RICH: does it carry everything the patent gives, not just the
     minimum?

6. **Go back to step 3 and check the same record a second time.** Re-read the patent
   with that record in mind again. The second pass catches what the first missed. Only
   when the record survives both passes do you move on.

7. **Then take the next object and repeat from step 2.** Do not stop after one record.
   Work through all of them, one after another.

8. **When every record is done, go back to record 0** and do a final pass over the
   whole file, checking that every record was covered and every issue was captured.

## What "read carefully" actually means

**First, read normally, with the record in mind.** Go through the patent as a person
would, understanding what it says, and asking of each passage: does this concern the
record I am holding? Build a picture of what the patent tells you about this one thing,
end to end, before you check anything. That ordinary reading is what finds meaning:
what the reaction is for, why a step is done in that order, what a phrase refers back
to, what a drawing shows. No script finds any of that.

**Then, alongside it, do the checkable things.** Careful reading is not slow reading;
it is reading that also produces something that can be verified:

- **Count as you go.** How many times does the patent state this thing? Then check the
  file holds that many. Two identical sentences look like one when you read them and
  like two when you count them, and counting is the only way to tell.
- **Treat every quotation as a claim to verify.** If a field holds text that is supposed
  to come from the patent, go and find that exact string in the patent. Text that reads
  correctly and text that is actually there are different things.
- **Compare like against like.** When several records describe the same situation, line
  them up side by side. A value that looks reasonable alone often looks wrong next to
  its siblings. Most inconsistency is invisible one record at a time.
- **Read for what is absent.** An empty field is a question, not an answer. Ask what
  ought to be there before accepting that nothing is.
- **Verify rather than accept.** When a record asserts something, go and confirm it
  against the page. Do not read a record's own claim as evidence for itself.
- **Ask why, when two things that should match do not.** A difference between two
  records that describe the same thing is either a real distinction the patent draws,
  or a defect. Find out which. Never assume it is the first.

Where a check can be made mechanically, make it mechanically. Counting, string
matching and cross-record comparison are exactly the things a careful reader does worst
and a short script does perfectly. Use both: read for meaning, compute for coverage.

## Pay special attention to empty fields

A `null` or `[]` is not proof that the patent says nothing. For every empty field, go
and check the patent:

- If the patent genuinely says nothing, the empty value is correct. Leave it.
- **If the patent says something and the field is empty, that is a finding.** Flag it.

This is where information is lost most often, and it is invisible unless you look.

## When there is nowhere to put a value

If the patent states something and no field exists for it, **do not drop it and do not
call it out of scope.** Flag it, say what the value is and where it is, and I will tell
you whether to add the field. The gold is the ground truth, so it must be more complete
than the pipeline, not equally lossy.

Note that a value sitting in `notes`, `procedure_text` or `molar_ratio_text` is NOT
captured. Nothing downstream reads prose. If it is only in prose, it is still a
finding.

## Rules for this pass

- **Flag. Do not fix.** Reason out why the value is wrong or missing, record it, and
  move on. I will review the flags and tell you what to correct.
- **Log as you read.** Keep the reasoning for every record in your scratchpad, passes
  as well as failures, so the work can be checked later.
- **Record every flag in the Excel**, in the sheet for this patent, on the Reactions
  tab. Write it so a beginner with no context can understand what is wrong: what the
  patent says, what the record has, what it should be, and the line number.
- **Never treat the pipeline's behaviour as correct.** It is the thing being measured.
  If the patent states something and the record does not have it, that is a finding
  whatever the pipeline was told to do.
- **Where a step is recorded twice**, once from the claims and once from the summary,
  the two records cover each other. A value present on one is not missing from the
  other. Read the pair together.

## What to give me at the end

- The complete list of issues, record by record, with index, reaction_id and line
  numbers.
- Which records passed clean.
- Anything you could not resolve, with both readings, rather than a guess.
