# Prompt 1: identify every reaction in the patent

Use this FIRST, before the extraction output is opened. The whole value of this pass
is that it is independent.

---

Read `input/<PATENT_ID>-enriched-numbered.md` line by line, in depth. Do not skip
lines and do not skim the repetitive parts. Read carefully, as defined below under
"What 'read carefully' actually means". Keep a running audit in your scratchpad as
you read, so you have a reference you can point back to later.

Your job in this pass is one thing only: **decide how many genuine reactions,
transformations or steps this patent describes, and where each one is.**

## Rules

1. **Do not open `reactions.json` or any other extraction output.** The `.md` is the
   only source. Once you have seen what the extraction found you will find the same
   things, and your count is worthless. If you have already seen it, say so now.
2. **One entry per genuine transformation.** A transformation mentioned in several
   places is still one transformation. Repeat mentions contribute detail, they do not
   multiply the count.
3. **But the same reaction run twice is two entries.** Twenty worked examples running
   one reaction under different conditions are twenty runs, because the conditions and
   the yields are the patent's actual content. Merging them destroys the point of the
   document.
4. **Ground every count in line numbers.** A count with no line number cannot be
   checked and does not belong in the answer.
5. **Preserve document order.**
6. **Every passage is in English or has an `EN:` translation.** The Chinese is
   authoritative where they differ.
7. **Read the drawings.** `[IMAGE_EXTRACT: ...]` spans carry reactants, products and
   the reagents written on the arrow. A transformation that is only drawn is still a
   transformation.
8. **Scope.** In: anything the patent states was actually performed, including in the
   background, if an example or a procedure carries it. Out: a reaction the patent
   describes only to say it does not work, or would happen under conditions nobody
   used. Flag those explicitly as excluded and say why, rather than silently dropping
   them.

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

## What to give me at the end

1. **A flowchart or mind map first.** I cannot read dense prose. Show the route
   visually, bucketed by product: which reactions make X, which make Y, what feeds
   what.
2. **Then the counts**, bucketed, each with line numbers.
3. **Then the detail**, one line per transformation: line number, what reacts, what
   forms, and which section it sits in.
4. **Anything you deliberately excluded**, with the reason.

Ask me before you start if anything is unclear. Do not assume.
