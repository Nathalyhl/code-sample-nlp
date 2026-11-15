# Research notes and evaluation

## Task definition

Given a natural-language analytical question, produce a validated semantic object or an explicit clarification/rejection outcome. A complete object identifies a year or inclusive year range, a metric, a total/ranking operation, an optional destination and a ranking limit.

The offline analyzer performs Unicode accent normalization, lexical pattern matching, field extraction, semantic normalization and schema validation. It includes a small English/Spanish vocabulary. Three Spanish diagnostic examples demonstrate that vocabulary; they do not establish broad multilingual capability.

The LLM boundary accepts a function mapping an instruction-and-input string to JSON text. It supports the same workflow as the reference analyzer. Supplying an adapter requires an authorized provider and separate model evaluation. No foundation model was trained or evaluated for the results below.

## Evaluation protocol

The dataset contains 36 sample-authored synthetic questions. Categories cover direct phrasing, paraphrases, three Spanish examples, missing/ambiguous parameters, unsupported requests, invalid input and two adversarial requests. Cases are stateless; conversational behavior is checked separately by the regression tests.

The reference labels specify the desired decision and, when applicable, every field of the semantic object. Missing default fields in the dataset are materialized through the same explicit data schema before comparison. The evaluator does not call the database or an LLM.

- **Exact semantic match:** decision, reason and complete normalized query all match the reference.
- **Field accuracy:** each semantic field is scored over the 20 cases whose reference decision is ready. A clarification with no returned query counts as incorrect for every field.
- **Decision confusion:** count reference/predicted decision pairs.
- **Category performance:** retain group counts rather than reporting only an aggregate.

Run `python -m nlp_sample.evaluate --check` to reproduce the saved report. To generate a new report after an intentional code or dataset change, run `python -m nlp_sample.evaluate --output reports/evaluation.json` and review all differences.

## Observed results

The offline reference analyzer matches **32/36 cases (88.89%)** exactly. It completes 16 of the 20 reference-ready cases. All four failures are clarification outcomes for difficult paraphrases. Each ready-case field scores **80%**, because the same four cases return no query.

| Difficult input | Desired interpretation | Observed limitation |
| --- | --- | --- |
| “What were the export earnings in 2023?” | FOB value | The vocabulary does not recognize “earnings” |
| “How many export transactions took place in 2023?” | Operation count | The vocabulary does not recognize this count construction |
| “Show the net mass of exports in 2023” | Net weight | The vocabulary does not map “net mass” |
| “FOB exports to USA in 2023” | United States destination | The alias list does not include “USA” |

The full JSON report preserves references and predictions for every case. Failures are left visible to illustrate coverage limits and motivate a comparison against model-assisted interpretation. The original thesis's LLM is not assigned this baseline score.

## Limits of the evidence

This is a small diagnostic set authored alongside the implementation. It has no independent annotation, train/test separation, inter-annotator agreement or domain-shift assessment. Its percentage should not be presented as general NLP accuracy. The dataset has been used while developing the sample, so it is a development set rather than a blind test.

The rules recognize a limited vocabulary and cannot guarantee correct interpretation of arbitrary text. Negation, implicit references, unknown aliases, complex filters, relative dates and unsupported syntax require broader evaluation. Keyword rejection is illustrative and does not constitute comprehensive prompt-injection defense. Schema validation checks output shape and value bounds; it cannot prove that a model understood the question correctly.

All trade rows are invented. SQLite behavior does not verify cloud identity, Redshift permissions, Glue transformations, Airflow scheduler operation, concurrent access or deployment performance. The local answer formatter avoids prose-generation uncertainty but also omits the richer original analyst agent.

## Further research directions

1. Collect independently annotated questions from authorized users and reserve a blind test set.
2. Compare the rules, a pretrained LLM and an LLM with explicit schema/context instructions using identical cases.
3. Evaluate paraphrases, ambiguity, negation, unsupported requests and multi-turn corrections separately.
4. Measure field correctness and clarification quality as well as SQL execution equivalence on a controlled database.
5. Record model/version, inference settings, prompts, latency, cost and repeated-run variation.
6. Evaluate generated answers against returned data, including empty results and misleading trends.

These are proposed experiments, not completed research results.

## Background reading

- [Deng, Chen and Zhang (2022), Recent Advances in Text-to-SQL](https://aclanthology.org/2022.coling-1.190/): semantic parsing, datasets, methods and evaluation.
- [Wang et al. (2023), Know What I don't Know](https://aclanthology.org/2023.findings-acl.352/): ambiguous and unknown questions in Text-to-SQL.
