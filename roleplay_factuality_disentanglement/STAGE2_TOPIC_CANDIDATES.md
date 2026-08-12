# Stage 2A: Pilot topic candidates

**Status:** Approved and frozen as Stage 2A Version 1 on 2026-08-09. No dataset rows or role-play
prompts have been created yet.

## Relationship to the previous factuality questions

These topics are methodologically compatible with the earlier factuality dataset:

- they use stable, broadly known factual knowledge;
- every evaluation can be expressed as a Yes/No question;
- each question has a clearly identified factual answer and matched nonfactual answer;
- activations can be extracted at the same forced `Yes` or `No` answer position; and
- the same factuality-margin definition can be applied.

Some domains intentionally resemble earlier controls—including astronomy, geometry, chemistry, and
geography—while the exact claims differ. This preserves comparability without training and testing on
duplicate questions. The role-play variable is the new factor added to the established factuality
structure.

## Selection principles

Pilot topics should be:

- stable over time;
- expressible as an unambiguous Yes/No question;
- familiar enough that the pilot model is likely to represent the underlying fact;
- diverse across knowledge domains;
- easy to pair with one plausible but clearly false alternative;
- emotionally and politically neutral; and
- independent enough that one topic does not reveal another topic's answer.

The pilot deliberately avoids current events, disputed claims, approximate quantities, medical
advice, legal claims, and facts whose answer depends strongly on wording or jurisdiction.

## Proposed ten-topic pilot

| ID | Domain | Factual proposition | Matched false proposition | Proposed Yes/No question | Risk review |
|---|---|---|---|---|---|
| T01 | Astronomy | Earth orbits the Sun. | Earth orbits Mars. | Does Earth orbit the Sun? | Low ambiguity |
| T02 | Geography | Canberra is the capital of Australia. | Sydney is the capital of Australia. | Is Canberra the capital of Australia? | Low ambiguity; distinguishes capital from largest/famous city |
| T03 | Chemistry | Water has the chemical formula H₂O. | Water has the chemical formula CO₂. | Is H₂O the chemical formula for water? | Low ambiguity |
| T04 | Zoology | Whales are mammals. | Whales are fish. | Are whales mammals? | Low ambiguity |
| T05 | Mathematics | A triangle has three sides. | A triangle has four sides. | Does a triangle have three sides? | Low ambiguity in ordinary Euclidean definitions |
| T06 | Anatomy | The heart pumps blood through the body. | The heart produces bile. | Does the heart pump blood through the body? | Low ambiguity; descriptive fact, not medical advice |
| T07 | Zoology | Penguins are birds. | Penguins are mammals. | Are penguins birds? | Low ambiguity |
| T08 | Literature | William Shakespeare wrote *Hamlet*. | Charles Dickens wrote *Hamlet*. | Is William Shakespeare the author traditionally credited with *Hamlet*? | Wording acknowledges attribution rather than debating authorship theories |
| T09 | Botany | Photosynthesis uses light energy. | Photosynthesis uses sound energy. | Does photosynthesis use light energy? | Low ambiguity at pilot level |
| T10 | Geography | The Pacific is Earth's largest ocean. | The Atlantic is Earth's largest ocean. | Is the Pacific Earth's largest ocean? | Low ambiguity when "largest" means surface area |

## Why this is only a topic list

At this point, we are choosing the semantic content only. We are **not yet** deciding:

- the exact normal-answer instructions;
- the exact role-play instructions;
- the forced Yes/No answer order;
- dataset splits;
- which wording templates are held out; or
- the final number of examples.

Separating these decisions prevents an early prompt-writing choice from silently changing the topic
balance or label definitions.

## Checks before approval

- [x] All ten factual propositions are sufficiently stable and unambiguous.
- [x] The ten domains are diverse enough for a pilot.
- [x] Each false alternative is clearly false but linguistically comparable to the true alternative.
- [x] No topic should be removed or replaced for avoidable ambiguity.
- [x] Approve this list before matched prompt construction begins.

## Decision record

**Approved by the researcher on 2026-08-09**, with the requirement that the topics remain comparable
to the previous factuality questions. The compatibility is documented above. Stage 2B may now draft
the instruction-template families before they are combined with these facts.
