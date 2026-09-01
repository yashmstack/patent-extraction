# Prompt 7: final gold check on reactions.json

Phase 3. Run this LAST, after every flag from Prompts 2 and 5 has been reviewed and
corrected. This is the pass that decides whether the file can be called gold.

Everything before this looked for problems. This pass assumes nothing and re-derives
every field from the patent.

---

## The pipeline. Follow it in order. Do not skip a step.

1. **Open `output/reactions.json`**, the corrected gold file.

2. **Go record by record, starting at 0**: 0, 1, 2, 3 ... to the last one. Keep the
   index and the running count visible at every step so that no record is skipped and
   neither of us loses track of where we are.

3. **Take one record and understand what it is about.** What reaction is this? What
   reacts, what forms, under what conditions?

4. **Then read the patent `.md`, keeping that specific record in mind**, and understand
   what happened for that record in the patent. Read it properly and in depth, line by
   line, the whole file. Read carefully, as defined below under "What 'read carefully'
   actually means", and do that on every pass. A line can concern your record without naming it: "the salt
   prepared in step (1)", "the same procedure as Example 1", a structure on an arrow,
   or the line that fixes what R or M stands for. Read for anything related, not only
   for direct mentions.

5. **Then go through every field of that record, one at a time, in order**, starting
   from `patent_id`, `reaction_id`, `section_label` and on to the end. For each field:

   **a) Decide where the answer comes from.** Is this a field the PATENT must answer
   (a quantity, a temperature, a compound, a yield), or a field the LLM is expected to
   GENERATE (`reaction_class`, `mechanism_type`, `named_reaction`, `tags`,
   `confidence`)? The two are checked differently: the first against the page, the
   second against the chemistry and against how the rest of the file treats the same
   situation.

   **b) Check whether it is empty or filled.**

   - **Empty:** work out how it ought to be filled, determine the correct value, and
     verify it against the `.md`. If the patent genuinely says nothing, the empty value
     is correct, and say so rather than leaving it unexamined.
   - **Filled:** re-verify it, using both your own chemical knowledge and the `.md`.
     Is the value right? If it is wrong, correct it, reason out why it was wrong, and
     then verify the correction against the patent again.

6. **When every field of that record is done and verified, go back to step 2** and take
   the next record. Repeat until every record has been through the whole loop.

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

## Read the patent for every record

You must read the `.md` for every record, as this pipeline is designed to do. If there
are 55 records, that is 55 readings. Do not carry over an impression from the last
record and assume it still holds.

## What "gold" has to mean by the end

For every record, all of the following are true:

- Every value the patent states about that reaction is in the record.
- Every value in the record is supported by the patent, with nothing invented.
- Every empty field is empty because the patent is silent, and you checked.
- Every generated field is correct, and consistent with how the file treats the same
  situation elsewhere. Two identical reactions must not carry different labels.
- Every derived field agrees with the field it is derived from.

## Rules

- **Correct as you go on this pass**, unlike the flagging passes. But reason out every
  change before you make it, verify it against the patent afterwards, and record what
  you changed and why.
- **If you are unsure, stop and ask.** Do not guess a value into the gold. A flagged
  uncertainty is worth more than a confident invention.
- **Never treat the pipeline's behaviour as correct.** It is the thing being measured.
- Log every record's reasoning in your scratchpad, passes as well as corrections.

## What to give me at the end

- The record-by-record result: how many passed clean, what was corrected, with the
  index and the line numbers.
- A plain statement of whether the file is gold, and if not, exactly what is blocking
  it.
- Anything you could not settle, with both readings.

Ask me if anything is unclear before you start, and stop and ask if you get stuck part
way through rather than guessing.
