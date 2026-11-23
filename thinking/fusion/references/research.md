# Researching precedents

How `/fusion` finds the precedents a page stands on. Step 2 of [`../SKILL.md`](../SKILL.md) points
here. The aim is the most insightful, relevant and recent sources for this plan, not the ones you
already know.

Three habits defeat that aim, and this procedure is built against them. A brief that lists the
sources you have in mind makes helpers confirm them instead of discovering others. Research that
skips what the repo itself records about its origins misses the work the plan descends from. And
a rule that prefers papers and official documentation misses the state of a fast-moving field,
which lives in tool documentation, practitioner write-ups, talks, repositories and preprints.

## The layers

Search in layers, from the work outward. Each layer has its own helper and its own first query,
so none crowds out another.

1. **Lineage**: what the work descends from. The repo's own record of it (README credits,
   provenance manifests such as `UPSTREAM.toml`, `CITATION.cff`, `NOTICE`); the upstreams at the
   commits the repo pins and at their latest versions; their authors' own explanations (posts,
   talks, documentation); and the earlier fusion pages and decision records in `fusion_dir` and
   `decision_records`. Follow what the repo points to outward. An influence the repo does not
   record enters only when the user names it. This layer always runs: in a repo with no provenance
   record, the page says what was checked and that it found nothing.
2. **The field now**: recent work in the area the plan lives in. Its helper searches practitioner
   venues (tool documentation, write-ups and critiques, talks, repositories) as well as preprints
   and studies, and the page shows how many of each kind it found. "Recent" means the last 12
   months.
3. **Foundations**: the older ideas the plan rests on, with adjacent fields where they help.

## The steps

1. **Read the lineage yourself**, before writing any brief. A lineage helper then follows what
   you found outward.
2. **Seal your priors.** Write the sources you already have in mind to a separate working list.
   Keep it out of every brief. You compare against it in step 8.
3. **Brief each helper for discovery**, using the template below: the goal, the plan's problem in
   its own words, the field, its layer, the source types, a date window, the rows to return, and
   the file to write. Never a list of expected sources, and never a hypothesis to confirm: what a
   brief names, a helper finds.
4. **Spread the helpers** across the layers and across perspectives (the maintainer, the
   practitioner, the sceptic, the user's own work). Give each a different first query, broad
   before narrow, and the most thorough search mode the harness offers for the field now.
5. **Search, and chase citations** backward (what the strongest sources cite) and forward (what
   cites or answers them). Rewrite queries in the vocabulary each pass finds; a pass is one round
   of queries by every helper still searching. Stop when a pass adds nothing new. Citation chasing
   complements broad search; it does not replace it.
6. **Verify what carries weight.** A source that a fork or a recommendation rests on is re-opened
   by a second reader, who quotes the passage that supports it. A claim that does not survive is
   dropped or stated with its caveat.
7. **Run the gap critic** on a first draft, and on any later round that brings a subject or a fork
   the page's precedents do not cover, or a source the user named. Give a fresh reader, from another model family where the
   harness offers one, the plan's subject and the precedent table, but not your sealed list. It
   names what an expert in this field would expect to find there and does not, and which entries
   are weakest. Its gaps become queries: search them as in step 5 until a pass adds nothing new,
   then go on to step 8. The critic runs once per trigger, not after every gap search. A gap that
   stays unfilled is listed on the page as not found.
8. **Unseal and report.** Compare the precedents with your sealed list, and count the sources it
   did not hold. Report on the page as described below.

A helper's report counts once its file exists and is complete, as step 2 of the skill says.
Helpers write to working files outside the repo, such as the session's scratch area. These are not
committed, and the page summarises them with their sources, as step 3 requires for working notes.

**Every precedent on the page was opened in this research**, by a helper or by you. A source that
could not be opened is listed as not searched, with the reason, never cited as a precedent. A
source on your sealed list enters only after a helper found it, or you opened it during this
research.

**Without helper agents**, run the layers yourself, one after another, each from its own first
query. The second reader and the gap critic become separate passes in which you read only the
precedent table and the sources, and the page names them as self-checks.

## Brief template

```
Goal: <what this page must decide, in one sentence>
The problem, in its own words: <two or three sentences, no candidate answers>
The field: <the area the plan lives in>
Your layer: <lineage | the field now | foundations>; your perspective: <maintainer | practitioner | sceptic | the user's own work>
First query: <one broad query, different from every other helper's>
Source types: <repositories and their commits | documentation | posts | talks | preprints | papers>
Date window: <for the field now, the last 12 months, and say what is newest>
Return, per source: title; author or organisation; exact date; URL (pinned to a commit for a
repository file); kind; credibility (High, Med or Low: who wrote it, how specific it is, whether
it reports real use, its date); two sentences on what it says; one on what it suggests for this
plan; whether you opened it.
Write to: <file path>. Report back only once the file is complete, with what you could not open.
```

## Grading and recency

- **Practitioner sources count.** Grade them for credibility rather than exclude them. Flag a
  preprint as unreviewed, and check whether a published version exists.
- **Recency floor.** At least a third of a page's web precedents, across all layers, come from the
  last 12 months. When fewer exist, the page says why.
- **Dates are exact.** A source without a date is marked undated, never given a guessed one.

## On the page

The precedents section is grouped by layer and shows, so a fresh session can audit the research
from the section alone:

- each layer with its count, and what it searched: for the lineage, the provenance files, pins
  and earlier pages checked; for the field now, the kinds of source and how many of each;
- the newest source's date;
- what was not searched or not found, and why;
- how many precedents the sealed list did not hold;
- which checks ran: the second reader, the gap critic, or the self-checks that stood in for them.

## Asking the user

On a first draft, the page's "where my view ends" section asks, as an optional question the user
may skip, which sources, people or projects the page should know beyond what the repo records. An
answer joins the lineage layer in the next round, even when that round brings no new subject or
fork: open each named source, add it, and send it to the second reader if a fork rests on it.

A later round searches again, and runs the gap critic again, only when it brings a subject or a
fork the page's precedents do not cover, or a source the user named.

## Without web access

Say so on the page. The lineage layer still runs from the repo, and the foundations layer from
what can be verified locally; the precedents section marks the field now as not searched.
