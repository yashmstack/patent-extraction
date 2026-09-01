# Prompt 6: verify every record in compounds.json against the patent

Phase 2. Run this only after Prompts 3 and 4, when `compounds.json` already contains
every compound the patent names. Phase 1 fixed the COUNT. This pass fixes the CONTENT
of each record.

The goal: every field of every compound is verified against the patent, so that once
the issues are fixed the file can be relied on as gold.

---

## The loop

Follow this exact flow. Do not skip any step.

1. **Take the first compound object from `compounds.json`**, and work in file order:
   0, 1, 2, 3 and so on. Keep the index visible in everything you report.

2. **Read the patent `.md` with respect to that compound**, line by line, end to end.
   Read all of it, every line, not only the sections where you first find the compound.
   Read carefully, as defined below under "What 'read carefully' actually means", and do
   that on every pass.

   Read it **properly and in depth, with that compound held in mind the whole way
   through**, asking of every line: does this say anything about my compound? Not
   scanning for the name. A line can be about your compound without naming it, because
   it calls it "the starting material", or "the salt prepared in step (1)", or draws it
   as a structure, or refers to it as R or M. Read for anything RELATED to the compound,
   not only for direct mentions.

   Identify every piece of information the patent gives about it: where it appears, what
   role it plays, what quantity, what strength, what measurement, what physical
   description, what it is called in Chinese and in English, and how it is referred to
   indirectly.

3. **Check whether all of that information has been correctly captured** in the object.

4. **Verify every field against the patent:**
   - Is the value correct?
   - If the value was generated incorrectly, flag it.
   - If the patent states a different value, flag the mismatch.
   - If information is missing, work out whether it is genuinely absent from the patent
     or was present and simply not captured.

5. **Pay special attention to fields that are `null` or `[]`.** Go to the patent and
   determine whether the information is genuinely missing.
   - Genuinely absent from the patent: the empty value is correct, leave it.
   - **Present in the patent but the field is empty: flag it as not captured.**

6. **Go back to step 2 and check the same compound again.** Re-read the patent with
   that compound in mind a second time, to be sure nothing was missed on the first
   pass.

7. **After the second check, move to the next compound** and repeat from step 2.

8. **Continue for every compound in the file.**

9. **Throughout, read the `.md` end to end each time**, all 600 or more lines. Do not
   rely only on the sections where the compound first appears.

10. **When all compounds are done, go back to step 1** and do a final verification pass
    over every object, checking that each was covered and each issue captured.

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

## What to flag, for each compound

- Information present in the patent but not captured.
- Incorrect values.
- Values that differ from what the patent states.
- `null` or `[]` fields that should carry information from the patent.
- Values the patent never states, invented or hallucinated.

## When there is nowhere to put a value

If the patent states something and no field exists for it, **do not drop it and do not
call it a schema problem and move on.** Flag it, say what the value is and where it is,
and I will decide whether to add the field.

Before you conclude that no field exists, check whether a general-purpose field already
fits. `analytics` on a compound takes any measurement: method, value, unit, conditions,
raw_text. It has been wrongly called a schema gap before when the field was simply
unused.

Note also that a value sitting only in `notes` is NOT captured. Nothing downstream
reads prose. If it is only in prose, it is still a finding.

## Rules for this pass

- **Flag. Do not fix.** Reason it out, record it, move on. I will review and tell you
  what to correct.
- **Log as you read**, in your scratchpad, passes as well as failures.
- **Record every flag in the Excel**, on the Compounds tab for this patent, written so
  a beginner with no context can understand it: what the patent says, what the record
  has, what it should be, and the line number.
- **Never treat the pipeline's behaviour as correct.** It is the thing being measured.
- **Quotation fields must quote.** If a field holds a quotation from the patent, check
  it appears in the patent verbatim. A paraphrase in a field named for raw text is a
  finding.

## What to give me at the end

- The complete list of issues found, for each compound, with index, identifier and line
  numbers.
- Which compounds passed clean.
- Anything unresolved, with both readings rather than a guess.
