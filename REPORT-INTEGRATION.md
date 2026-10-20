# Benedict's Phase 2 integration checklist

The Overleaf ZIP has a blank RQ2 question. The previously supplied PDF and pasted
LaTeX already contained a token-requirements question. Therefore, do not replace
the live Overleaf main.tex with the ZIP's main.tex: it could undo newer work.

## 1. Confirm Rifat's final RQ2

Working wording from the newer draft:

> How do the length and structure of SKILL.md instructions relate to their estimated input-token requirements?

The following replacement text assumes that remains the question. Integrate
only once it agrees with Rifat's actual method. Do not claim token results until
his analysis is available.

## 2. Related Work: replace only the closing sentence

Replace the sentence beginning "Together, these works motivate..." with:

```latex
Together, these works motivate investigating cross-repository skill reuse
and characterizing the estimated input-token requirements of task-specific
instruction files. Our study examines these artifacts rather than directly
evaluating agent runtime or task success.
```

The existing cited study summaries are retained; this review did not re-audit
the source papers.

## 3. Replace the Problem Statement paragraph

```latex
Aggregate duplication statistics do not explain how exact skill reuse is
distributed across repositories or whether a small number of widely copied
contents account for much of the observed reuse. Distinguishing file
occurrences from distinct contents is therefore important when interpreting
the GitSkills sample. A second concern is the amount of instruction text
that a skill contributes when included in a model's input. We examine how
instruction length and structure relate to estimated input-token requirements.
These measurements characterize the files themselves; they do not establish
whether instructions are used during a task or whether longer instructions
improve or reduce agent efficiency.
```

## 4. Replace the Proposed Solution paragraph

```latex
We study the public GitSkills sample using content hashes, repository
metadata, and skill-file contents. For RQ1, we group identical contents,
measure their distribution across repositories, and examine concentration,
location associations, and robustness to selected filters. We complement
these measurements with manual coding of 50 sampled contents. For RQ2,
we examine instruction length and structure in relation to estimated
input-token requirements. The Study Design and Experiments sections
describe the measurements and preliminary findings for each question.
```

Use this last paragraph only when the two sections actually contain RQ2's
method and findings; it is not a substitute for them.

## 5. Tighten RQ1 wording

- Replace "78% of distinct skills are never reused" with
  "78% of distinct skill contents occur in only one repository in this sample."
- Replace "most cross-repository copies come from skill collections and mirrors
  (24 of 40 contents...)" with "Among the 40 manually coded cross-repository
  contents, 24 were classified as collection/mirror and nine as independent
  adoption." These are sampled contents, not a count of all copies. The sample
  is stratified and includes the 20 most reused contents, so it is not a random
  estimate of population channel prevalence.
- Add to the location method: "For the content-level analysis, we use the
  location of the dataset's designated representative (dedup_primary = 1).
  A content can appear in multiple locations; this classification represents
  its designated occurrence rather than every location where it appears."
- Describe associations as associations. Collection paths and manual coding
  suggest possible distribution channels; they do not prove causal copying
  histories or actual adoption by agents.

## 6. Finish with Rifat

Insert his measurement description into Step 4b and his motivation, approach,
results, and limitations into the RQ2 Experiments subsection. Specify text
scope, tokenizer/estimation method, handling of duplicates, and structure
features. Keep token requirements distinct from measured agent performance.

Update the overview's RQ2 box and caption to match the implemented method.
The existing caption instead says complexity is related to reuse.

## 7. Final quality check

- Replace abstract `xxx` using final findings from both questions.
- Complete or appropriately remove empty end sections; the supplied Phase 2
  slides specifically require Study Design and Experiments, not every heading
  inherited from the template.
- Remove obsolete MSR 2022 publication metadata if it is merely template text.
- Check Overleaf's log, references, figure labels, and page layout.
- Include the final report and RQ2 scripts/results in the submission package.
- Verify the full teacher announcement for requirements missing from the
  cropped screenshots.

Suggested limitations to discuss in your own words: the sample and snapshot
scope; exact hashes miss near-duplicates; coding is interpretive; standard
location is assigned using a representative; occurrence-level independence is
weak; token estimates do not measure execution cost or effectiveness.

Nothing in this checklist or the reviewed package was uploaded to Overleaf,
Slack, GitHub, or Canvas.
