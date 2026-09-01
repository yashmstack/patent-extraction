# Prompt 3: identify every compound the patent mentions

Use this FIRST, before `compounds.json` is opened. The independence is the point.

---

**Do not open `compounds.json` or any other extraction output.** The `.md` is the only
source. Once you have seen what the extraction found you will find the same things, and
your list is worthless. If you have already seen it, say so now.

Follow these steps in order. Do not skip any.

1. Open `input/<PATENT_ID>-enriched-numbered.md`.
2. Read it line by line and understand what each line says. Read carefully, as defined
   below under "What 'read carefully' actually means".
3. Whenever you come across a compound, write it down in your scratchpad with its
   line number.
4. Move to the next line and repeat.
5. Read the whole file this way, end to end, all 600 or more lines.

At the end, tell me how many compounds the patent mentions.

## What counts as a compound

Include compounds appearing in:

- prose and body text
- experimental procedures
- reaction descriptions
- reaction schemes and drawn structures
- images and figures
- tables
- worked examples
- starting materials, reagents, intermediates, products
- by-products, where explicitly named
- solvents and any other substance explicitly named as a chemical
- anywhere else in the patent

**Do not limit yourself to the main or product compounds.** The goal at this stage is
every chemical the patent names, whatever its role and however briefly it appears.

**Include the generic class terms too**, written exactly as the patent writes them:
"a basic substance", "an alcohol", "a tertiary alcohol", "an alkali metal alkoxide".
The extraction pipeline records these, so a gold set that drops them is not comparable.
Bucket them separately so I can see them, but do not omit them.

## Bucket the answer

Group what you find, for example: route materials, bases, alcohols, alkoxides,
solvents, other reagents, impurities, compounds named only in the background, generic
class terms, placeholders such as ROH and ROM, and anything genuinely borderline such
as an enzyme or a functional group the patent calls a group rather than a substance.

Put the borderline ones in their own bucket with your reasoning, and let me decide.
Do not silently include or exclude them.

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

## How to be sure you have not missed any

Do not rely on reading alone. Cross-check at least these ways and say that you did:

- sweep the Chinese for chemical name endings such as 醇 酸 酯 盐 烷 烯 酮 醚 胺 钠 钾
- sweep the English for name endings such as -ol, -ate, -ide, -one, -ane, acid, ether
- list every distinct SMILES and molecular formula in the `[IMAGE_EXTRACT: ...]` spans
- check every material that carries a mass or a volume in the experimental section

Account for every candidate these sweeps return, including the ones you reject, and
say why you rejected them.

## What to give me

- The count, and the buckets, each entry with line numbers.
- Which are drawn as structures and which are text only.
- The borderline ones separately, with your reasoning and no decision taken.

Ask me before you start if anything is unclear.
