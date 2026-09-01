# Prompt 4: reconcile your compound list against compounds.json

Only after Prompt 3 is finished and the list is written down.

---

You now have your own list of every compound the patent names. Open
`output/compounds.json` and reconcile the two, going through it **one record at a
time**.

## Step 1: what did they get that you got

Of the compounds you listed, how many are in `compounds.json`?

**Check identity by identity, not by exact name.** The same substance appears under
different names: `DMF` and `N,N-dimethylformamide`, `苄醇` and `benzyl alcohol`, a
Chinese name and its English translation. Look at the `aliases` on each record, not
only the `identifier`. Two lists can hold the same chemistry and share almost no
strings.

Go through `compounds.json` manually, record by record. Do not match by string
comparison alone and call it done.

## Step 2: what is in the file that is not on your list

For each one, reason it out and say plainly which it is:

- **your miss** - the patent does name it and you did not catch it. Say how you missed
  it.
- **their error** - the file holds something the patent never names, or a name that is
  not a compound at all, such as a section title, a method name or a heading.

## Step 3: what is on your list that is not in the file

For each one, say whether it is a genuine extraction miss and how much it matters. A
generic class noun from the claims matters more than a herbicide named once in the
background.

## Before you flag anything

- **Check the twin.** Where the same thing is recorded twice from two sections, the two
  records cover each other. A value on one is not missing from the other.

## What a field MEANS, versus what the pipeline did

Look up what a field is defined to hold before you fill it or judge it. Several field
names do not mean what they sound like, and filling them by guess puts a wrong value
in the gold.

That is the only reason to open the pipeline's prompts. **Never treat the pipeline's
behaviour as correct.** It is the thing being measured. If the patent names a compound
and the extraction does not have it, that is a finding, whatever the pipeline was told
to do. The gold has to be more complete than the pipeline, not equally lossy.

## What to give me at the end

**Three tables. List every compound individually. Do not group them, do not collapse a
range of rows into "10-17 all same", and do not summarise a bucket as one line. If
there are 43 matches, show 43 rows.**

**Table 1: the matches, one row per compound**

| # | your compound | compounds.json identifier | match |
|---|---|---|---|
| 1 | tert-butanol | tert-butanol | exact |
| 2 | DMF | N,N-dimethylformamide | identity |
| 3 | 苄醇 the benzylic alcohol | benzyl alcohol | identity |

Mark each row `exact` where the strings are the same, or `identity` where they are the
same substance under a different name, such as an abbreviation against its full name, a
Chinese name against its English one, or a short form against a systematic name.

**Table 2: missing from compounds.json, one row per compound, with a one-line reason**

| # | compound | line | why it was probably missed |
|---|---|---|---|
| 1 | alkali metal alkoxide | 47 | a generic class noun, though it is a reagent route in claim 1 |
| 2 | HPPD | 125 | an enzyme, not a chemical, named only in the background |

**Table 3: in compounds.json but not on your list, one row each**, with a one-line
verdict saying whether it is your miss or their error, and why.

Then the three counts: matched, missing, extra.

Flag only. Do not change `compounds.json` until I have reviewed the flags and told you
to.
